from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RetrievalMetrics:
    recall_at_5: float
    recall_at_10: float
    mrr: float


def recall_at(ranking: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    retrieved = set(ranking[:k])
    return len(retrieved & relevant) / len(relevant)


def reciprocal_rank(ranking: list[str], relevant: set[str]) -> float:
    for index, item_id in enumerate(ranking, start=1):
        if item_id in relevant:
            return 1.0 / index
    return 0.0


def evaluate_retrieval(
    rankings: Iterable[tuple[list[str], set[str]]],
    *,
    k5: int = 5,
    k10: int = 10,
) -> RetrievalMetrics:
    rows = [(ranking, relevant) for ranking, relevant in rankings if relevant]
    if not rows:
        return RetrievalMetrics(recall_at_5=0.0, recall_at_10=0.0, mrr=0.0)
    return RetrievalMetrics(
        recall_at_5=sum(recall_at(ranking, relevant, k5) for ranking, relevant in rows) / len(rows),
        recall_at_10=sum(recall_at(ranking, relevant, k10) for ranking, relevant in rows)
        / len(rows),
        mrr=sum(reciprocal_rank(ranking, relevant) for ranking, relevant in rows) / len(rows),
    )
