from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import OwnerDep, SessionDep, get_embedding_provider
from app.db.models import Item, ItemEmbedding
from app.services.embeddings import EmbeddingProvider, embedding_text, text_hash
from app.services.retrieval import hybrid_search, keyword_search, semantic_search
from app.services.agent import run_agent

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class Source(BaseModel):
    id: str
    title: str | None
    description: str | None
    tags: list[str]
    keyword_rank: int | None = None
    semantic_rank: int | None = None
    semantic_score: float | None = None


class SearchResponse(BaseModel):
    query: str
    items: list[Source]
    mode: str


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=12)


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    insufficient_evidence: bool


class ReindexResponse(BaseModel):
    indexed: int
    failed: int
    model: str


class AgentResponse(BaseModel):
    answer: str
    sources: list[Source]
    tool_trace: list[str]
    insufficient_evidence: bool


def _source(result) -> Source:
    item = result.item
    return Source(
        id=item.id,
        title=item.title,
        description=item.description,
        tags=item.tags,
        keyword_rank=result.keyword_rank,
        semantic_rank=result.semantic_rank,
        semantic_score=result.semantic_score,
    )


def _history_text(history: list[HistoryMessage]) -> str:
    lines = []
    for message in history:
        if message.content:
            lines.append(f"{message.role}: {message.content}")
    return "\n".join(lines)


@router.get("/search", response_model=SearchResponse)
def search(
    session: SessionDep,
    owner_id: OwnerDep,
    provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    q: Annotated[str, Query(min_length=1, max_length=256)],
    mode: Annotated[str, Query(pattern="^(keyword|semantic|hybrid)$")] = "hybrid",
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
) -> SearchResponse:
    keyword = keyword_search(session, owner_id=owner_id, query=q, limit=limit)
    if mode == "keyword":
        return SearchResponse(
            query=q,
            items=[_source(result) for result in keyword],
            mode=mode,
        )
    if not provider.is_configured:
        if mode == "semantic":
            return SearchResponse(query=q, items=[], mode=mode)
        return SearchResponse(
            query=q,
            items=[_source(result) for result in keyword],
            mode="keyword-fallback",
        )

    query_vector = provider.embed_text(q)
    semantic = semantic_search(
        session,
        owner_id=owner_id,
        query_vector=query_vector,
        limit=limit,
    )
    if mode == "semantic":
        return SearchResponse(
            query=q,
            items=[_source(result) for result in semantic],
            mode=mode,
        )
    combined = hybrid_search(keyword, semantic, limit)
    return SearchResponse(
        query=q,
        items=[_source(result) for result in combined],
        mode="hybrid",
    )


@router.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    session: SessionDep,
    owner_id: OwnerDep,
    provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
) -> AskResponse:
    history = _history_text(body.history)
    if not provider.is_configured:
        return AskResponse(
            answer="Semantic retrieval and answer generation are not configured.",
            sources=[],
            insufficient_evidence=True,
        )

    try:
        try:
            search_query = provider.rewrite_query(body.question, history)
        except Exception:
            search_query = body.question

        keyword = keyword_search(session, owner_id=owner_id, query=search_query, limit=8)
        query_vector = provider.embed_text(search_query)
        semantic = semantic_search(
            session,
            owner_id=owner_id,
            query_vector=query_vector,
            limit=8,
        )
        results = hybrid_search(keyword, semantic, 8)
        if not results:
            return AskResponse(
                answer="I could not find enough information in your screenshot library.",
                sources=[],
                insufficient_evidence=True,
            )

        context_lines = []
        for index, result in enumerate(results, start=1):
            item = result.item
            context_lines.append(
                f"[screenshot {item.id}] Title: {item.title or ''}\n"
                f"Description: {item.description or ''}\n"
                f"Tags: {', '.join(item.tags)}"
            )
        answer = provider.answer(body.question, "\n\n".join(context_lines), history)
        cited_ids = set(re.findall(r"\[(?:screenshot\s+)?([a-zA-Z0-9_-]+)\]", answer))
        cited_results = [r for r in results if r.item.id in cited_ids]
        final_sources = cited_results if cited_results else results
        return AskResponse(
            answer=answer,
            sources=[_source(result) for result in final_sources],
            insufficient_evidence=False,
        )
    except Exception:
        logger.exception("Ask question processing failed")
        return AskResponse(
            answer="I could not reach the answer service just now. Please try again.",
            sources=[],
            insufficient_evidence=True,
        )


@router.post("/reindex", response_model=ReindexResponse)
def reindex(
    session: SessionDep,
    owner_id: OwnerDep,
    provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
) -> ReindexResponse:
    if not provider.is_configured:
        return ReindexResponse(indexed=0, failed=0, model=provider.model)

    items = list(
        session.scalars(
            select(Item).where(
                Item.owner_id == owner_id,
                Item.status == "ready",
            )
        )
    )
    indexed = 0
    failed = 0
    for item in items:
        text = embedding_text(item.title, item.description, item.tags)
        if not text:
            continue
        try:
            vector = provider.embed_text(text)
        except Exception:
            failed += 1
            continue
        existing = session.get(ItemEmbedding, item.id)
        if existing is None:
            existing = ItemEmbedding(item_id=item.id)
            session.add(existing)
        existing.model = provider.model
        existing.text_hash = text_hash(text)
        existing.dimensions = len(vector)
        existing.vector = vector
        existing.updated_at = datetime.now(UTC)
        indexed += 1
    session.commit()
    return ReindexResponse(indexed=indexed, failed=failed, model=provider.model)


@router.post("/agent", response_model=AgentResponse)
def agent(
    body: AskRequest,
    session: SessionDep,
    owner_id: OwnerDep,
    provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
) -> AgentResponse:
    history = _history_text(body.history)
    try:
        answer, results, tool_trace = run_agent(
            session=session,
            owner_id=owner_id,
            provider=provider,
            question=body.question,
            history=history,
        )
        return AgentResponse(
            answer=answer,
            sources=[_source(result) for result in results],
            tool_trace=tool_trace,
            insufficient_evidence=not results,
        )
    except Exception:
        logger.exception("Agent question processing failed")
        return AgentResponse(
            answer="I could not reach the answer service just now. Please try again.",
            sources=[],
            tool_trace=[],
            insufficient_evidence=True,
        )
