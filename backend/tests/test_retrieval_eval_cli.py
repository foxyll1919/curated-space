import csv
import json

import pytest

from app.cli.evaluate_retrieval import evaluate


def test_evaluate_export_files_and_report_metrics(tmp_path):
    items_path = tmp_path / "items.jsonl"
    labels_path = tmp_path / "labels.csv"
    items = [
        {
            "id": "img001",
            "title": "Binary search patterns",
            "description": "Koko eating bananas problem",
            "tags": ["algorithms"],
        },
        {
            "id": "img002",
            "title": "A recipe collection",
            "description": "Cooking notes",
            "tags": ["food"],
        },
    ]
    items_path.write_text(
        "".join(json.dumps(item) + "\n" for item in items),
        encoding="utf-8",
    )
    with labels_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=["query", "relevant_item_ids", "query_type", "notes"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "query": "Binary search Koko bananas",
                "relevant_item_ids": "img001",
                "query_type": "keyword",
                "notes": "",
            }
        )
        writer.writerow(
            {
                "query": "Flights to Mars",
                "relevant_item_ids": "",
                "query_type": "no_result",
                "notes": "",
            }
        )

    report = evaluate(items_path, labels_path)
    assert "Candidate screenshots: 2" in report
    assert "| keyword | 1.000 | 1.000 | 1.000 |" in report
    assert "No-result false-positive rate: 0.000" in report
    assert "does not call an external embedding API" in report


def test_evaluation_rejects_unknown_relevant_ids(tmp_path):
    items_path = tmp_path / "items.jsonl"
    labels_path = tmp_path / "labels.csv"
    items_path.write_text('{"id":"img001","title":"One"}\n', encoding="utf-8")
    labels_path.write_text(
        'query,relevant_item_ids,query_type\n"Find it","img999",keyword\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown relevant IDs"):
        evaluate(items_path, labels_path)
