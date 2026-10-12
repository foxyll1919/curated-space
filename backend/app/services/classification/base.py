from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Prediction:
    """A classifier result.

    `score` is a LinearSVC decision value, NOT a probability and NOT a
    confidence. LinearSVC has no `predict_proba`. Never rename this field
    "confidence"; calibration is a separate, later step.
    """

    labels: dict[str, str]
    score: float
    abstained: bool
    model_version: str
    taxonomy_version: str


class Classifier(Protocol):
    def predict(self, text: str) -> Prediction: ...

    @property
    def is_ready(self) -> bool: ...
