"""Serving adapter for the TF-IDF + LinearSVC classifier.

Security note: `joblib.load` executes code. This module only ever loads the path
configured by `settings.classifier_artifact`, which is operator-controlled. It
is never given a user-supplied path and never fetched over the network.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import joblib
import sklearn
from curated_ml.model_card import ModelCard, card_path_for, read_model_card

from app.services.classification.base import Prediction


logger = logging.getLogger(__name__)


class ClassifierLoadError(RuntimeError):
    """The artifact could not be loaded. Never surfaced to API callers verbatim."""


@dataclass(frozen=True)
class ClassifierStatus:
    name: str
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.name == "ok"


class _DecisionModel(Protocol):
    """The subset of a fitted sklearn Pipeline this adapter uses."""

    classes_: Sequence[str]

    def decision_function(self, X: Sequence[str]) -> Any: ...

    def predict(self, X: Sequence[str]) -> Any: ...


class SklearnSvcClassifier:
    """Loads the artifact once and answers `predict(text) -> Prediction`.

    Labels are keyed by the taxonomy's facet name, which is `category` today and
    becomes `{"intent": ..., "domain": ...}` under the v1 guide without any
    schema change.
    """

    def __init__(self, artifact_path: Path, *, strict_version: bool = True) -> None:
        self._artifact_path = artifact_path
        self._strict_version = strict_version
        self._model: _DecisionModel | None = None
        self._status = ClassifierStatus("not_loaded")

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    @property
    def status(self) -> ClassifierStatus:
        return self._status

    @property
    def taxonomy_version(self) -> str | None:
        return self._card.taxonomy_version if self.is_ready else None

    @property
    def model_version(self) -> str | None:
        return self._card.model_version if self.is_ready else None

    def load(self) -> None:
        """Load the artifact and its card, or raise ClassifierLoadError."""
        try:
            card = read_model_card(card_path_for(self._artifact_path))
        except (OSError, ValueError) as exc:
            raise ClassifierLoadError(f"missing or unreadable model card: {exc}") from exc

        if not self._artifact_path.is_file():
            raise ClassifierLoadError(f"classifier artifact not found: {self._artifact_path}")

        if card.sklearn_version != sklearn.__version__:
            message = (
                f"scikit-learn version mismatch: artifact trained on "
                f"{card.sklearn_version}, running {sklearn.__version__}"
            )
            if self._strict_version:
                raise ClassifierLoadError(message)
            logger.warning(message)

        try:
            model = cast(_DecisionModel, joblib.load(self._artifact_path))
        except Exception as exc:
            raise ClassifierLoadError(f"could not load classifier artifact: {exc}") from exc

        self._validate(model, card)
        self._model = model
        self._card = card
        self._status = ClassifierStatus("ok")

    def _validate(self, model: Any, card: ModelCard) -> None:
        """Refuse an artifact whose classes are numeric ids, not label strings.

        The retired artifact had `classes_` of 0..7 with an unrecoverable
        mapping to the CSV's category strings. Failing loudly here is much
        cheaper than silently writing wrong labels onto user items.
        """
        classes = getattr(model, "classes_", None)
        if classes is None:
            inner = getattr(model, "steps", None) or []
            for _, step in inner:
                if hasattr(step, "classes_"):
                    classes = step.classes_
                    break
        if classes is None:
            raise ClassifierLoadError("classifier artifact exposes no classes_")
        if not all(isinstance(value, str) for value in classes):
            raise ClassifierLoadError(
                "classifier classes are not label strings (numeric ids); "
                "retrain with ml/train.py instead of inferring the mapping"
            )
        unknown = set(classes) - set(card.labels)
        if unknown:
            raise ClassifierLoadError(
                f"classifier classes not present in the card: {', '.join(sorted(unknown))}"
            )

    def predict(self, text: str) -> Prediction:
        if self._model is None:
            raise ClassifierLoadError("classifier is not loaded")
        scores = self._model.decision_function([text])[0]
        classes = list(self._model.classes_)
        ranking = sorted(zip(classes, scores), key=lambda pair: pair[1], reverse=True)
        top_label, top_score = ranking[0]
        runner_up_score = ranking[1][1] if len(ranking) > 1 else float("-inf")
        margin = float(top_score - runner_up_score)

        abstained = margin < self._card.abstention_threshold
        return Prediction(
            labels={} if abstained else {self._card.facet: top_label},
            score=margin,
            abstained=abstained,
            model_version=self._card.model_version,
            taxonomy_version=self._card.taxonomy_version,
        )


class UnavailableClassifier:
    """Stand-in used when the artifact is missing, so startup never hard-fails."""

    def __init__(self, detail: str) -> None:
        self._status = ClassifierStatus("unavailable", detail)

    @property
    def is_ready(self) -> bool:
        return False

    @property
    def status(self) -> ClassifierStatus:
        return self._status

    @property
    def taxonomy_version(self) -> str | None:
        return None

    @property
    def model_version(self) -> str | None:
        return None

    def predict(self, text: str) -> Prediction:
        raise ClassifierLoadError("classifier is unavailable")
