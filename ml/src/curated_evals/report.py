"""Report rendering: one JSON file for the record, one table for the decision.

The table is the deliverable. It is ordered so the decision the milestone exists
to make is readable at a glance: quality first, then latency, then cost, then
what went wrong. A column that cannot be computed prints `n/a` rather than `0`,
because `0` for accuracy or cost reads as a result.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from curated_evals.dataset import summarize
from curated_evals.metrics import LabelMetrics
from curated_evals.runner import RunResult


REPORT_VERSION = "eval-report-v1"


def build_report(
    runs: Sequence[RunResult],
    set_,
    *,
    pricing: dict[str, Any] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Assemble the JSON document written to disk."""
    return {
        "report_version": REPORT_VERSION,
        "notes": notes,
        "set": summarize(set_),
        "pricing": pricing or {},
        "runs": [run.as_dict() for run in runs],
    }


def write_report(report: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return target


def _fmt(value: Any, spec: str = ".3f") -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return format(value, spec)
    return str(value)


def render_table(report: dict[str, Any]) -> str:
    """The printed summary. Every cell traces back to a number in the JSON."""
    set_summary = report["set"]
    lines: list[str] = []

    split = set_summary["split"]
    lines.append(f"set: {set_summary['size']} items, {set_summary['labeled']} labeled")
    lines.append(
        f"split: {split}   taxonomy: {set_summary['taxonomy_version']}   facet: {set_summary['facet']}"
    )
    if split == "synthetic":
        lines.append("!! synthetic set: measures the harness, not model quality !!")
    if set_summary["unlabeled"]:
        lines.append(
            f"   {set_summary['unlabeled']} items have no gold label: "
            "accuracy is not reported, latency and cost are"
        )
    if set_summary["labels_with_no_rows"]:
        lines.append(f"   labels with no rows: {', '.join(set_summary['labels_with_no_rows'])}")

    pricing = report.get("pricing") or {}
    if pricing:
        lines.append(f"prices verified {pricing.get('verified_on')} ({pricing.get('source')})")

    header = (
        f"\n{'config':<52} {'acc':>6} {'F1':>6} {'abst':>6} "
        f"{'p50 ms':>7} {'p95 ms':>7} {'$/item':>8} {'tok/item':>9} {'fail':>5}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for run in report["runs"]:
        config = run["config"]
        name = config["name"]
        classifier = run.get("classifier") or {}
        cost = run.get("cost") or {}
        latency = run.get("latency") or {}
        tokens = cost.get("prompt_tokens_per_item")
        tokens_per_item = (
            (tokens or 0) + (cost.get("output_tokens_per_item") or 0)
            if tokens is not None
            else None
        )
        lines.append(
            f"{name:<52} "
            f"{_fmt(classifier.get('accuracy')):>6} "
            f"{_fmt(classifier.get('macro_f1')):>6} "
            f"{_fmt(classifier.get('abstain_rate')):>6} "
            f"{_fmt(latency.get('p50_ms'), ',d'):>7} "
            f"{_fmt(latency.get('p95_ms'), ',d'):>7} "
            f"{_fmt(cost.get('usd_per_item'), '.6f'):>8} "
            f"{_fmt(tokens_per_item, '.1f'):>9} "
            f"{len(run.get('failures') or []):>5}"
        )

    lines.extend(_provider_label_section(report))
    lines.extend(_agreement_section(report))
    lines.extend(_cache_section(report))

    if report.get("notes"):
        lines.append("")
        lines.append(f"notes: {report['notes']}")

    return "\n".join(lines)


def _provider_label_section(report: dict[str, Any]) -> list[str]:
    runs_with_provider = [run for run in report["runs"] if run.get("provider_labels")]
    if not runs_with_provider:
        return []
    lines = ["", "Gemini enum labels (the 'does Gemini label too' arm):"]
    for run in runs_with_provider:
        metrics = run["provider_labels"]
        lines.append(
            f"  {run['config']['name']:<50} acc {_fmt(metrics.get('accuracy'))}  "
            f"F1 {_fmt(metrics.get('macro_f1'))}  n_labeled {metrics.get('n_labeled', 0)}"
        )
    return lines


def _agreement_section(report: dict[str, Any]) -> list[str]:
    runs_with_agreement = [run for run in report["runs"] if (run.get("agreement") or {}).get("n")]
    if not runs_with_agreement:
        return []
    lines = [
        "",
        "Gemini label vs local classifier label (agreement, not accuracy):",
    ]
    for run in runs_with_agreement:
        agreement = run["agreement"]
        lines.append(
            f"  {run['config']['name']:<50} {_fmt(agreement['rate'])} over n={agreement['n']}"
        )
    return lines


def _cache_section(report: dict[str, Any]) -> list[str]:
    cached = [run for run in report["runs"] if run.get("cache_hits")]
    if not cached:
        return []
    lines = ["", "cache:"]
    for run in cached:
        lines.append(
            f"  {run['config']['name']:<50} hit rate {_fmt(run['cache_hit_rate'])} "
            f"({run['cache_hits']} hits, {run['provider_calls']} provider calls)"
        )
    return lines


def per_class_table(metrics: LabelMetrics | None, title: str) -> str:
    """Per-class precision/recall, for reviewing errors rather than a headline."""
    if metrics is None or not metrics.per_class:
        return ""
    lines = ["", title, f"  {'label':<24} {'P':>6} {'R':>6} {'F1':>6} {'n':>5}"]
    for score in metrics.per_class:
        lines.append(
            f"  {score.label:<24} {_fmt(score.precision):>6} {_fmt(score.recall):>6} "
            f"{_fmt(score.f1):>6} {score.support:>5}"
        )
    return "\n".join(lines)
