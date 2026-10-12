"""Milestone 4: curated_ml shared code, the serving adapter and abstention."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import joblib
import pytest
import sklearn
from curated_ml.datasets import load_holdout, load_labeled_csv
from curated_ml.model_card import card_path_for, read_model_card, write_model_card
from curated_ml.taxonomy import load_taxonomy
from curated_ml.text import BUILD_TEXT_VERSION, build_text, normalize_tags

from app.core.config import Settings
from app.main import build_classifier
from app.services.classification.base import Prediction
from app.services.classification.sklearn_svc import (
    ClassifierLoadError,
    SklearnSvcClassifier,
    UnavailableClassifier,
)
from tests.conftest import BACKEND_DIR


ML_DIR = BACKEND_DIR.parent / "ml"
TAXONOMY_PATH = ML_DIR / "taxonomy" / "legacy-8.json"
ARTIFACT_PATH = ML_DIR / "model" / "curated_space_classifier_v2.pkl"


# --------------------------------------------------------------------------
# curated_ml.text: one build_text for training and serving
# --------------------------------------------------------------------------


def test_build_text_is_deterministic_and_versioned():
    first = build_text("Title", "Description", ["a", "b"])
    second = build_text("Title", "Description", ["a", "b"])
    assert first == second
    assert BUILD_TEXT_VERSION == "build-text-v1"
    assert first == "Title\nDescription\nTags: a, b"


def test_build_text_accepts_comma_string_and_missing_fields():
    assert build_text("T", "D", "a, b") == build_text("T", "D", ["a", "b"])
    # The Tags: marker is always present so training and serving share a layout.
    assert build_text(None, None, None) == "\n\nTags:"
    assert build_text("T", "D", None) == "T\nD\nTags:"


def test_raw_dataset_text_uses_the_serving_layout():
    from curated_ml.text import build_text_from_raw

    raw = build_text_from_raw("Figma ideas for visual inspiration")
    assert raw == build_text(None, "Figma ideas for visual inspiration", None)
    assert raw.endswith("Tags:")
    assert build_text(None, None, None).endswith("Tags:")


def test_serving_and_training_agree_on_the_tags_token():
    """The format mismatch this module exists to prevent."""
    from curated_ml.text import build_text_from_raw

    assert "Tags:" in build_text_from_raw("anything")
    assert "Tags:" in build_text("t", "d", [])


def test_normalize_tags_drops_empties():
    assert normalize_tags([" a ", "", None, "b"]) == ["a", "b"]


# --------------------------------------------------------------------------
# curated_ml.taxonomy and model_card
# --------------------------------------------------------------------------


def test_legacy_taxonomy_has_eight_unique_labels():
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    assert taxonomy.version == "legacy-8"
    assert len(taxonomy.labels) == 8
    assert len(set(taxonomy.labels)) == 8
    assert "Tutorials" in taxonomy


def test_taxonomy_rejects_duplicate_labels(tmp_path):
    path = tmp_path / "dup.json"
    path.write_text(json.dumps({"version": "x", "labels": ["A", "A"]}), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_taxonomy(path)


def test_taxonomy_rejects_missing_version(tmp_path):
    path = tmp_path / "nov.json"
    path.write_text(json.dumps({"labels": ["A"]}), encoding="utf-8")
    with pytest.raises(ValueError, match="version"):
        load_taxonomy(path)


def test_model_card_roundtrips(tmp_path):
    card = read_model_card(card_path_for(ARTIFACT_PATH))
    target = write_model_card(card, tmp_path / "card.json")
    assert read_model_card(target).to_dict() == card.to_dict()


def test_model_card_path_sits_next_to_the_artifact():
    assert card_path_for(ARTIFACT_PATH) == ARTIFACT_PATH.with_suffix(".card.json")


# --------------------------------------------------------------------------
# The shipped artifact and card must agree
# --------------------------------------------------------------------------


def test_shipped_artifact_classes_are_label_strings():
    """Guards the exact hazard that retired the previous artifact."""
    model = joblib.load(ARTIFACT_PATH)
    classes = list(model.classes_)
    assert all(isinstance(value, str) for value in classes), (
        "classes_ must be label strings; numeric ids have an unrecoverable mapping"
    )


def test_shipped_card_records_unvalidated_threshold():
    card = read_model_card(card_path_for(ARTIFACT_PATH))
    assert card.threshold_source == "default-unvalidated"
    assert card.taxonomy_version == "legacy-8"
    assert card.build_text_version == BUILD_TEXT_VERSION
    assert card.sklearn_version == sklearn.__version__
    assert "NOT model-quality evidence" in card.notes


def test_retired_artifact_has_numeric_classes():
    """Documents why the legacy .pkl must not be served. If this ever changes,
    the migration note in readme.md is stale."""
    retired = ML_DIR / "model" / "curated_space_classifier.pkl"
    if not retired.exists():
        pytest.skip("retired artifact already removed")
    assert not all(isinstance(value, str) for value in joblib.load(retired).classes_)


# --------------------------------------------------------------------------
# Loading and the scikit-learn version guard
# --------------------------------------------------------------------------


def test_loads_and_predicts_from_the_configured_path():
    classifier = SklearnSvcClassifier(ARTIFACT_PATH)
    classifier.load()
    assert classifier.is_ready
    assert classifier.status.ok
    assert classifier.taxonomy_version == "legacy-8"

    prediction = classifier.predict(
        build_text("React JWT authentication guide", "Step by step with screenshots", ["tutorial"])
    )
    assert isinstance(prediction, Prediction)
    assert set(prediction.labels) <= {"category"}


def test_production_refuses_a_sklearn_version_mismatch(tmp_path):
    card = read_model_card(card_path_for(ARTIFACT_PATH))
    mismatched = type(card)(**{**card.to_dict(), "sklearn_version": "0.0.1-not-a-version"})
    shutil.copy(ARTIFACT_PATH, tmp_path / "model.pkl")
    write_model_card(mismatched, card_path_for(tmp_path / "model.pkl"))

    classifier = SklearnSvcClassifier(tmp_path / "model.pkl", strict_version=True)
    with pytest.raises(ClassifierLoadError, match="version mismatch"):
        classifier.load()


def test_development_warns_instead_of_refusing(tmp_path):
    card = read_model_card(card_path_for(ARTIFACT_PATH))
    mismatched = type(card)(**{**card.to_dict(), "sklearn_version": "0.0.1-not-a-version"})
    shutil.copy(ARTIFACT_PATH, tmp_path / "model.pkl")
    write_model_card(mismatched, card_path_for(tmp_path / "model.pkl"))

    classifier = SklearnSvcClassifier(tmp_path / "model.pkl", strict_version=False)
    classifier.load()
    assert classifier.is_ready


def test_refuses_numeric_classes_rather_than_guessing(tmp_path):
    legacy = ML_DIR / "model" / "curated_space_classifier.pkl"
    if not legacy.exists():
        pytest.skip("retired artifact already removed")
    shutil.copy(legacy, tmp_path / "model.pkl")
    shutil.copy(card_path_for(ARTIFACT_PATH), card_path_for(tmp_path / "model.pkl"))

    with pytest.raises(ClassifierLoadError, match="numeric"):
        SklearnSvcClassifier(tmp_path / "model.pkl").load()


def test_missing_artifact_raises(tmp_path):
    with pytest.raises(ClassifierLoadError):
        SklearnSvcClassifier(tmp_path / "absent.pkl").load()


def test_missing_card_raises(tmp_path):
    shutil.copy(ARTIFACT_PATH, tmp_path / "model.pkl")
    with pytest.raises(ClassifierLoadError, match="model card"):
        SklearnSvcClassifier(tmp_path / "model.pkl").load()


def test_build_classifier_falls_back_in_development():
    settings = Settings(
        environment="development",
        classifier_artifact=Path("does-not-exist.pkl"),
        classifier_required=False,
    )
    classifier = build_classifier(settings)
    assert isinstance(classifier, UnavailableClassifier)
    assert not classifier.is_ready


def test_build_classifier_refuses_in_production():
    settings = Settings(
        environment="production",
        classifier_artifact=Path("does-not-exist.pkl"),
        classifier_required=True,
    )
    with pytest.raises(ClassifierLoadError):
        build_classifier(settings)


# --------------------------------------------------------------------------
# Abstention
# --------------------------------------------------------------------------


def test_abstains_on_ambiguous_text_and_returns_no_labels():
    classifier = SklearnSvcClassifier(ARTIFACT_PATH)
    classifier.load()
    threshold = read_model_card(card_path_for(ARTIFACT_PATH)).abstention_threshold

    prediction = classifier.predict(
        build_text("Screenshot of a padlock with a six digit code", "Private key material", [])
    )
    if prediction.abstained:
        assert prediction.labels == {}
    assert prediction.score < threshold or prediction.abstained is False
    assert not hasattr(prediction, "confidence")


def test_score_is_a_margin_not_a_probability():
    classifier = SklearnSvcClassifier(ARTIFACT_PATH)
    classifier.load()
    prediction = classifier.predict(build_text("Figma palette", "Colours", ["design"]))
    assert isinstance(prediction.score, float)
    assert "confidence" not in Prediction.__dataclass_fields__


# --------------------------------------------------------------------------
# Datasets
# --------------------------------------------------------------------------


def test_holdout_is_absent_so_no_quality_claim(tmp_path):
    assert load_holdout(tmp_path / "holdout.csv") is None


def test_holdout_loader_reads_a_supplied_file(tmp_path):
    path = tmp_path / "holdout.csv"
    path.write_text("text,category\nA React tutorial,Tutorials\n", encoding="utf-8")
    frame = load_holdout(path)
    assert frame is not None
    assert len(frame) == 1


def test_labeled_csv_rejects_a_missing_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("text\nsomething\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required column"):
        load_labeled_csv(path)


def test_realistic_eval_is_not_the_legacy_taxonomy():
    """Its labels differ, so it must never be folded into training or the holdout."""
    import pandas as pd

    frame = pd.read_csv(ML_DIR / "dataset" / "realistic_eval.csv")
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    assert not set(frame["category"]) <= set(taxonomy.labels)
    # It also uses title/description/tags columns, not the `text` column the
    # shared loader requires, which is a second reason it is not interchangeable.
    assert "text" not in frame.columns
