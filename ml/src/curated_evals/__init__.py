"""The evaluation harness: measure before building more on top of a choice.

Milestone 6 exists because every provider decision so far has been a default
copied from the brief rather than a measurement. This package runs the real
extractor and the real classifier over a labeled set and reports the numbers that
decide them: quality, latency, tokens, dollars and cache hit rate.

Two rules govern everything here:

**Nothing is fabricated.** A screenshot set is a folder of real images plus a
label file the owner writes. There is a small generated fixture for CI that is
marked `split: "synthetic"` in every report, so a synthetic number can never be
mistaken for a real one.

**A metric without its denominator is not a result.** Every accuracy figure is
reported next to its `n`, and a run with no gold labels reports `None` rather
than a number computed over an empty set.
"""

from curated_evals.config import CANDIDATE_MODELS, EvalConfig, by_name, matrix
from curated_evals.dataset import (
    EvalItem,
    EvalSetError,
    LabeledSet,
    load_set,
    write_label_template,
)
from curated_evals.metrics import LabelMetrics, LabelObservation, score_items, score_latency
from curated_evals.report import build_report, render_table, write_report
from curated_evals.runner import ItemRecord, RunResult, run_config

__all__ = [
    "CANDIDATE_MODELS",
    "EvalConfig",
    "EvalItem",
    "EvalSetError",
    "ItemRecord",
    "LabelMetrics",
    "LabelObservation",
    "LabeledSet",
    "RunResult",
    "by_name",
    "build_report",
    "load_set",
    "matrix",
    "render_table",
    "run_config",
    "score_items",
    "score_latency",
    "write_label_template",
    "write_report",
]
