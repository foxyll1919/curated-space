"""The model card sidecar.

`curated_space_classifier.card.json` is written by `train.py` and read by the
backend at startup. It answers the questions a bare `.pkl` cannot: which labels
exist, which scikit-learn trained it, which data, and how it was evaluated.

`sklearn_version` exists because pickle artifacts are version-sensitive: a
`.pkl` trained on one scikit-learn can fail to unpickle or silently change
behaviour on another.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


CARD_SUFFIX = ".card.json"


@dataclass(frozen=True)
class ClassMetrics:
    precision: float
    recall: float
    f1: float
    support: int


@dataclass(frozen=True)
class ModelCard:
    model_version: str
    taxonomy_version: str
    labels: list[str]
    facet: str
    sklearn_version: str
    python_version: str
    build_text_version: str
    training_data_sha256: str
    training_row_count: int
    metrics: dict[str, Any]
    abstention_threshold: float
    threshold_source: str
    created_at: str
    notes: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        extras = data.pop("extras")
        data.update(extras)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelCard":
        known = {field_name for field_name in cls.__dataclass_fields__}
        kwargs = {key: value for key, value in data.items() if key in known}
        extras = {key: value for key, value in data.items() if key not in known}
        return cls(extras=extras, **kwargs)

    @property
    def macro_f1(self) -> float | None:
        value = self.metrics.get("macro_f1")
        return float(value) if isinstance(value, (int, float)) else None


def card_path_for(artifact_path: str | Path) -> Path:
    artifact = Path(artifact_path)
    return artifact.with_suffix(CARD_SUFFIX)


def write_model_card(card: ModelCard, path: str | Path) -> Path:
    target = Path(path)
    target.write_text(json.dumps(card.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target


def read_model_card(path: str | Path) -> ModelCard:
    return ModelCard.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
