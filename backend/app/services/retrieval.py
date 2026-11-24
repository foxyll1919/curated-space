from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, text as sql_text
from sqlalchemy.orm import Session

from app.db.models import Item, ItemEmbedding
from app.services.embeddings import cosine_similarity


@dataclass(frozen=True)
class SearchResult:
    item: Item
    keyword_rank: int | None = None
    semantic_rank: int | None = None
    semantic_score: float | None = None


def keyword_search(
    session: Session,
    *,
    owner_id: str,
    query: str,
    limit: int,
) -> list[SearchResult]:
    tokens = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
    if not tokens:
        return []
    fts_query = " AND ".join(f'"{token}"' for token in tokens)
    matching_ids: list[str] = list(
        session.execute(
            sql_text(
                "SELECT item_fts.item_id FROM item_fts "
                "JOIN items ON items.id = item_fts.item_id "
                "WHERE item_fts MATCH :fts_query "
                "AND items.owner_id = :owner_id AND items.status = 'ready' "
                "ORDER BY bm25(item_fts) LIMIT :limit"
            ),
            {"fts_query": fts_query, "owner_id": owner_id, "limit": limit},
        ).scalars()
    )
    if not matching_ids:
        return []
    items = session.scalars(
        select(Item).where(
            Item.id.in_(matching_ids),
            Item.owner_id == owner_id,
            Item.status == "ready",
        )
    ).all()
    items_by_id = {item.id: item for item in items}
    return [
        SearchResult(item=items_by_id[item_id], keyword_rank=index + 1)
        for index, item_id in enumerate(matching_ids)
        if item_id in items_by_id
    ]


def semantic_search(
    session: Session,
    *,
    owner_id: str,
    query_vector: list[float],
    limit: int,
) -> list[SearchResult]:
    rows = session.execute(
        select(Item, ItemEmbedding)
        .join(ItemEmbedding, ItemEmbedding.item_id == Item.id)
        .where(Item.owner_id == owner_id, Item.status == "ready")
    ).all()
    ranked = []
    for item, embedding in rows:
        vector = embedding.vector
        if isinstance(vector, list):
            score = cosine_similarity(query_vector, vector)
            ranked.append((score, item))
    ranked.sort(key=lambda row: (row[0], row[1].created_at), reverse=True)
    return [
        SearchResult(
            item=item,
            semantic_rank=index + 1,
            semantic_score=score,
        )
        for index, (score, item) in enumerate(ranked[:limit])
    ]


def hybrid_search(
    keyword_results: list[SearchResult],
    semantic_results: list[SearchResult],
    limit: int,
) -> list[SearchResult]:
    """Reciprocal-rank fusion keeps the implementation bounded and explainable."""
    fused: dict[str, dict[str, Any]] = {}
    for results, kind in ((keyword_results, "keyword"), (semantic_results, "semantic")):
        for rank_index, result in enumerate(results, start=1):
            entry = fused.setdefault(
                result.item.id,
                {
                    "item": result.item,
                    "keyword_rank": None,
                    "semantic_rank": None,
                    "semantic_score": None,
                    "rrf": 0.0,
                },
            )
            entry[f"{kind}_rank"] = rank_index
            if kind == "semantic":
                entry["semantic_score"] = result.semantic_score
            entry["rrf"] = float(entry["rrf"]) + 1.0 / (60.0 + rank_index)

    ranked = sorted(fused.values(), key=lambda entry: float(entry["rrf"]), reverse=True)
    return [
        SearchResult(
            item=entry["item"],
            keyword_rank=entry["keyword_rank"],
            semantic_rank=entry["semantic_rank"],
            semantic_score=entry["semantic_score"],
        )
        for entry in ranked[:limit]
    ]
