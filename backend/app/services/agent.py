from __future__ import annotations

import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.services.embeddings import EmbeddingProvider
from app.services.retrieval import SearchResult, hybrid_search, keyword_search, semantic_search


class AgentState(TypedDict, total=False):
    question: str
    search_query: str
    owner_id: str
    session: Session
    provider: EmbeddingProvider
    route: str
    tool_trace: list[str]
    results: list[SearchResult]
    answer: str


def run_agent(
    *,
    session: Session,
    owner_id: str,
    provider: EmbeddingProvider,
    question: str,
    history: str = "",
) -> tuple[str, list[SearchResult], list[str]]:
    if not provider.is_configured:
        return "Semantic retrieval and answer generation are not configured.", [], []

    def supervisor(state: AgentState) -> AgentState:
        q = state["question"]
        try:
            search_query = provider.rewrite_query(q, history)
        except Exception:
            search_query = q

        try:
            route = provider.route(search_query)
        except Exception:
            route = "hybrid"
        return {
            **state,
            "search_query": search_query,
            "route": route,
            "tool_trace": [f"{route}_search"],
        }

    def retrieval(state: AgentState) -> AgentState:
        route = state["route"]
        query = state.get("search_query", state["question"])
        if route == "keyword":
            found = keyword_search(session, owner_id=owner_id, query=query, limit=8)
        else:
            vector = provider.embed_text(query)
            semantic = semantic_search(
                session,
                owner_id=owner_id,
                query_vector=vector,
                limit=8,
            )
            if route == "semantic":
                found = semantic
            else:
                keyword = keyword_search(
                    session,
                    owner_id=owner_id,
                    query=query,
                    limit=8,
                )
                found = hybrid_search(keyword, semantic, 8)

        return {**state, "results": found}

    def answer(state: AgentState) -> AgentState:
        results = state.get("results", [])
        if not results:
            return {
                **state,
                "answer": "I could not find enough information in your screenshot library.",
                "results": [],
            }
        context_lines = []
        for result in results:
            item = result.item
            context_lines.append(
                f"[screenshot {item.id}] Title: {item.title or ''}\n"
                f"Description: {item.description or ''}\n"
                f"Tags: {', '.join(item.tags)}"
            )
        ans = provider.answer(
            state["question"],
            "\n\n".join(context_lines),
            history,
        )
        cited_ids = set(re.findall(r"\[(?:screenshot\s+)?([a-zA-Z0-9_-]+)\]", ans))
        cited_results = [r for r in results if r.item.id in cited_ids]
        return {**state, "answer": ans, "results": cited_results if cited_results else results}

    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor)
    builder.add_node("retrieval", retrieval)
    builder.add_node("answer", answer)
    builder.add_edge(START, "supervisor")
    builder.add_edge("supervisor", "retrieval")
    builder.add_edge("retrieval", "answer")
    builder.add_edge("answer", END)
    graph = builder.compile()
    state = graph.invoke(
        {
            "question": question,
            "owner_id": owner_id,
            "session": session,
            "provider": provider,
        }
    )
    return state["answer"], state.get("results", []), state.get("tool_trace", [])
