from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from app.services.retrieval_evaluation import evaluate_retrieval


def _read_items(path: Path) -> list[dict[str, Any]]:
    items = []
    seen: set[str] = set()
    with path.open(encoding="utf-8-sig") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                raise ValueError(f"{path}:{line_number}: every item needs a non-empty string id")
            if item_id in seen:
                raise ValueError(f"{path}:{line_number}: duplicate item id {item_id!r}")
            seen.add(item_id)
            items.append(item)
    return items


def _read_labels(path: Path, item_ids: set[str]) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"query", "relevant_item_ids", "query_type"}
        if not required.issubset(reader.fieldnames or []):
            missing = ", ".join(sorted(required - set(reader.fieldnames or [])))
            raise ValueError(f"{path}: missing required columns: {missing}")
        rows = []
        for line_number, row in enumerate(reader, start=2):
            query = (row.get("query") or "").strip()
            if not query:
                raise ValueError(f"{path}:{line_number}: query cannot be empty")
            relevant = {
                item_id.strip()
                for item_id in (row.get("relevant_item_ids") or "").split("|")
                if item_id.strip()
            }
            unknown = relevant - item_ids
            if unknown:
                raise ValueError(
                    f"{path}:{line_number}: unknown relevant IDs: {', '.join(sorted(unknown))}"
                )
            query_type = (row.get("query_type") or "").strip()
            if query_type not in {"keyword", "semantic", "multi_screenshot", "no_result"}:
                raise ValueError(f"{path}:{line_number}: unsupported query_type {query_type!r}")
            if query_type == "no_result" and relevant:
                raise ValueError(f"{path}:{line_number}: no_result query has relevant IDs")
            if query_type != "no_result" and not relevant:
                raise ValueError(f"{path}:{line_number}: answerable query has no relevant IDs")
            rows.append({"query": query, "relevant": relevant, "query_type": query_type})
    return rows


def _fts_query(query: str) -> str:
    tokens = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
    return " AND ".join(f'"{token}"' for token in tokens)


def _rank_keyword(items: list[dict[str, Any]], query: str, *, limit: int) -> list[str]:
    fts_query = _fts_query(query)
    if not fts_query:
        return []
    with sqlite3.connect(":memory:") as connection:
        connection.execute(
            "CREATE VIRTUAL TABLE eval_fts USING fts5(item_id UNINDEXED, title, description, tags)"
        )
        connection.executemany(
            "INSERT INTO eval_fts (item_id, title, description, tags) VALUES (?, ?, ?, ?)",
            [
                (
                    item["id"],
                    item.get("title") or "",
                    item.get("description") or "",
                    " ".join(item.get("tags") or []),
                )
                for item in items
            ],
        )
        rows = connection.execute(
            "SELECT item_id FROM eval_fts WHERE eval_fts MATCH ? ORDER BY bm25(eval_fts) LIMIT ?",
            (fts_query, limit),
        ).fetchall()
    return [row[0] for row in rows]


def evaluate(items_path: Path, labels_path: Path) -> str:
    items = _read_items(items_path)
    if not items:
        raise ValueError(f"{items_path}: no items found")
    labels = _read_labels(labels_path, {item["id"] for item in items})

    keyword_rankings: dict[str, list[tuple[list[str], set[str]]]] = {
        "all answerable": [],
        "keyword": [],
        "semantic": [],
        "multi_screenshot": [],
    }
    no_result_hits = []
    for row in labels:
        ranking = _rank_keyword(items, row["query"], limit=10)
        if row["query_type"] == "no_result":
            no_result_hits.append(bool(ranking))
        else:
            keyword_rankings["all answerable"].append((ranking, row["relevant"]))
            keyword_rankings[row["query_type"]].append((ranking, row["relevant"]))

    metrics_by_type = {
        query_type: evaluate_retrieval(rankings)
        for query_type, rankings in keyword_rankings.items()
    }
    no_result_false_positive_rate = (
        sum(no_result_hits) / len(no_result_hits) if no_result_hits else 0.0
    )
    return "\n".join(
        [
            "# Retrieval evaluation",
            "",
            f"- Candidate screenshots: {len(items)}",
            f"- Labeled queries: {len(labels)}",
            f"- Answerable queries: {len(keyword_rankings['all answerable'])}",
            f"- No-result queries: {len(no_result_hits)}",
            "- Keyword retrieval: production SQLite FTS5 AND matching, ranked with BM25",
            "- Semantic and hybrid: not run; this export has no vectors and this evaluation "
            "does not call an external embedding API.",
            "",
            "| Keyword FTS5/BM25 subset | Recall@5 | Recall@10 | MRR |",
            "|---|---:|---:|---:|",
            *[
                f"| {query_type} | {metrics.recall_at_5:.3f} | "
                f"{metrics.recall_at_10:.3f} | {metrics.mrr:.3f} |"
                for query_type, metrics in metrics_by_type.items()
            ],
            "",
            f"No-result false-positive rate: {no_result_false_positive_rate:.3f}",
            "",
            "Metrics average over answerable queries only. No-result queries are reported "
            "separately because recall and MRR are undefined when there are no relevant items.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate local FTS5 retrieval against a JSONL export and labeled CSV."
    )
    parser.add_argument("--items", type=Path, required=True, help="Screenshot metadata JSONL")
    parser.add_argument("--labels", type=Path, required=True, help="Gold query labels CSV")
    parser.add_argument("--output", type=Path, help="Optional Markdown report destination")
    args = parser.parse_args()

    report = evaluate(args.items, args.labels)
    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
