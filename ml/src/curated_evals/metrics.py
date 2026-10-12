"""Metrics for the eval harness.

The two numbers that decide the open questions are deliberately kept apart:

**Label agreement** (provider label vs local classifier label, no gold needed) is
always reportable, even on an unlabeled set. It says the two systems *disagree*,
not that either is *right*.

**Accuracy / macro-F1 against gold** is only reportable once the owner has
labeled. `score_items` returns `None` for those metrics when there are no gold
labels, so a report can never carry an accuracy computed over zero rows.

Abstention is tracked separately from accuracy on purpose: a classifier that
abstains on 40% of items can show a high accuracy on the 60% it answered, which
is exactly the kind of number that should not be read as "good".
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LabelObservation:
    """One item's labels from each arm."""

    item_id: str
    gold: str | None
    predicted: str | None
    abstained: bool = False


@dataclass(frozen=True)
class ClassScore:
    label: str
    precision: float | None
    recall: float | None
    f1: float | None
    support: int


@dataclass(frozen=True)
class LabelMetrics:
    """Accuracy and macro-F1 over a set of label observations."""

    n: int
    accuracy: float | None
    macro_f1: float | None
    abstain_rate: float | None
    per_class: tuple[ClassScore, ...] = ()
    #: Items with no gold label. When non-zero, accuracy is over `n_labeled`
    #: rows only and `n_labeled` says so.
    n_labeled: int = 0
    confusion: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass(frozen=True)
class LatencyMetrics:
    p50_ms: int | None
    p95_ms: int | None
    mean_ms: int | None


@dataclass(frozen=True)
class CostMetrics:
    #: None when the model is absent from the checked-in price table. Not zero:
    #: an unpriced model is unknown, and a fake $0.00 would quietly pass the
    #: "< $0.002 per item" target that the brief is trying to test.
    usd_per_item: float | None
    total_usd: float | None
    prompt_tokens_per_item: float | None
    output_tokens_per_item: float | None


def percentile(values: Sequence[float], q: float) -> float | None:
    """Nearest-rank percentile. `q` in [0, 1]."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = max(1, min(len(ordered), int(round(q * len(ordered) + 0.5))))
    return ordered[rank - 1]


def score_items(observations: Iterable[LabelObservation]) -> LabelMetrics:
    """Accuracy, macro-F1, per-class scores and abstain rate.

    An abstained prediction is scored as a miss (no label), which is the
    behaviour the API actually exhibits: `labels` is empty and the item shows as
    uncategorized. Scoring abstentions as correct would inflate every metric.
    """
    observations = list(observations)
    n = len(observations)
    labeled = [o for o in observations if o.gold is not None]

    abstain_rate = sum(1 for o in observations if o.abstained) / n if observations else None

    if not labeled:
        return LabelMetrics(
            n=n,
            accuracy=None,
            macro_f1=None,
            abstain_rate=abstain_rate,
            n_labeled=0,
        )

    correct = sum(1 for o in labeled if o.predicted is not None and o.predicted == o.gold)
    accuracy = correct / len(labeled)

    labels = sorted({o.gold for o in labeled} | {o.predicted for o in labeled if o.predicted})
    per_class: list[ClassScore] = []
    confusion: dict[str, dict[str, int]] = {}
    for label in labels:
        confusion[label] = {}
    for o in labeled:
        if o.predicted is not None:
            confusion[o.gold][o.predicted] = confusion[o.gold].get(o.predicted, 0) + 1

    f1s: list[float] = []
    for label in labels:
        tp = sum(1 for o in labeled if o.predicted == label and o.gold == label)
        fp = sum(1 for o in labeled if o.predicted == label and o.gold != label)
        fn = sum(1 for o in labeled if o.predicted != label and o.gold == label)
        support = tp + fn
        if tp == 0 and fp == 0 and fn == 0:
            continue
        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        if precision and recall and (precision + recall) > 0:
            f1 = 2 * precision * recall / (precision + recall)
        elif precision is None and recall is None:
            f1 = None
        else:
            f1 = 0.0
        if f1 is not None:
            f1s.append(f1)
        per_class.append(
            ClassScore(label=label, precision=precision, recall=recall, f1=f1, support=support)
        )

    macro_f1 = sum(f1s) / len(f1s) if f1s else None

    return LabelMetrics(
        n=n,
        accuracy=accuracy,
        macro_f1=macro_f1,
        abstain_rate=abstain_rate,
        per_class=tuple(per_class),
        n_labeled=len(labeled),
        confusion=confusion,
    )


def score_latency(latencies_ms: Sequence[int]) -> LatencyMetrics:
    if not latencies_ms:
        return LatencyMetrics(p50_ms=None, p95_ms=None, mean_ms=None)
    return LatencyMetrics(
        p50_ms=int(percentile(latencies_ms, 0.50) or 0),
        p95_ms=int(percentile(latencies_ms, 0.95) or 0),
        mean_ms=int(sum(latencies_ms) / len(latencies_ms)),
    )


def agreement(gold: str | None, predicted: str | None) -> float | None:
    """1.0 if two labelers agree, 0.0 if not, None if either abstained.

    An abstention is not disagreement. Counting it as a miss would make a
    cautious classifier look worse than one that guesses, which is the opposite
    of what abstention is for.
    """
    if gold is None or predicted is None:
        return None
    return 1.0 if gold == predicted else 0.0


def summarize_to_dict(metrics: LabelMetrics) -> dict[str, Any]:
    return {
        "n": metrics.n,
        "n_labeled": metrics.n_labeled,
        "accuracy": metrics.accuracy,
        "macro_f1": metrics.macro_f1,
        "abstain_rate": metrics.abstain_rate,
        "per_class": [
            {
                "label": c.label,
                "precision": c.precision,
                "recall": c.recall,
                "f1": c.f1,
                "support": c.support,
            }
            for c in metrics.per_class
        ],
    }
