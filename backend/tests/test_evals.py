"""The eval harness, the price table, and the label-emitting schema.

These are the Milestone 6 tests. The bias throughout is toward the failure modes
that produce a *believable wrong number* rather than a crash:

- accuracy reported over zero labeled rows,
- an abstention counted as a correct prediction,
- an unknown model priced at zero so a cost target passes,
- a labeled answer cached under the unlabeled schema version,
- a report built from generated images that does not say so.
"""

from __future__ import annotations

import json
from pathlib import Path

import hashlib
import pytest

from app.core.pricing import (
    PRICING_TABLE_PATH,
    estimate_cost_usd,
    load_pricing_table,
)
from app.services.classification.base import Prediction
from app.services.extraction.base import CacheIdentity
from app.services.extraction.schema import (
    LABELED_SCHEMA_VERSION,
    SCHEMA_VERSION,
    build_labeled_schema,
    validate_labels,
)
from curated_evals.config import CANDIDATE_MODELS, EvalConfig, by_name, matrix
from curated_evals.dataset import EvalSetError, load_set, write_label_template
from curated_evals.metrics import LabelObservation, score_items, score_latency
from curated_evals.report import build_report, render_table
from curated_evals.runner import ItemRecord, run_config
from curated_evals.synthetic import build_synthetic_set

BACKEND_DIR = Path(__file__).resolve().parents[1]
ML_DIR = BACKEND_DIR.parent / "ml"
TAXONOMY = ML_DIR / "taxonomy" / "legacy-8.json"


# --------------------------------------------------------------------------
# Price table
# --------------------------------------------------------------------------


def test_price_table_records_provenance():
    table = load_pricing_table()
    assert table.verified_on, "a price table with no verified_on cannot be trusted"
    assert table.source.startswith("https://")
    assert table.output_includes_thinking_tokens is True


def test_every_benchmarked_model_is_priced():
    """The harness must not produce a free-looking $0.00 for a real model."""
    priced = load_pricing_table().models
    missing = [model for model in CANDIDATE_MODELS if model not in priced]
    assert not missing, f"models benchmarked but absent from {PRICING_TABLE_PATH.name}: {missing}"


def test_default_model_is_priced(migrated_settings):
    assert migrated_settings.gemini_model in load_pricing_table().models


def test_known_price_arithmetic():
    # Verified 2026-10-11: 3.5-flash-lite is $0.30 in / $2.50 out per Mtok.
    cost = estimate_cost_usd(
        "gemini-3.5-flash-lite", prompt_tokens=1_000_000, output_tokens=1_000_000
    )
    assert cost == pytest.approx(2.80)


def test_unknown_model_is_none_not_zero():
    """None and 0.0 mean different things; conflating them fakes a free model."""
    assert estimate_cost_usd("gemini-imaginary", prompt_tokens=10**6, output_tokens=10**6) is None


def test_usage_prices_thinking_tokens_once_at_the_output_rate():
    """Google's output figure already says 'including thinking tokens'."""
    combined = estimate_cost_usd("gemini-3.5-flash-lite", prompt_tokens=0, output_tokens=1_000_000)
    assert combined == pytest.approx(2.50)


# --------------------------------------------------------------------------
# Label-emitting schema
# --------------------------------------------------------------------------


def test_labeled_schema_enum_is_built_from_the_taxonomy():
    schema = build_labeled_schema(("Alpha", "Beta"))
    assert set(schema.model_fields["labels"].annotation.__args__) == {"Alpha", "Beta"}


def test_validate_labels_accepts_a_case_variant_and_refuses_an_invented_one():
    assert validate_labels("tutorials", ("Tutorials", "Design")) == "Tutorials"
    with pytest.raises(ValueError):
        validate_labels("Recipes", ("Tutorials", "Design"))


def test_labeled_and_unlabeled_schemas_have_different_cache_versions():
    """Otherwise a cached labeled answer is served to an unlabeled request."""
    assert LABELED_SCHEMA_VERSION != SCHEMA_VERSION


def test_extractor_cache_identity_tracks_the_label_flag(migrated_settings):
    from app.services.extraction.gemini import GeminiExtractor

    plain = GeminiExtractor(migrated_settings)
    assert plain.cache_identity.schema_version == SCHEMA_VERSION

    labeled = GeminiExtractor(
        migrated_settings.model_copy(
            update={
                "gemini_return_labels": True,
                "taxonomy_path": TAXONOMY,
            }
        )
    )
    assert labeled.cache_identity.schema_version == LABELED_SCHEMA_VERSION


def test_labeled_extractor_reads_and_validates_the_provider_label(migrated_settings):
    from app.services.extraction.gemini import GeminiExtractor

    labeled = GeminiExtractor(
        migrated_settings.model_copy(
            update={"gemini_return_labels": True, "taxonomy_path": TAXONOMY}
        )
    )
    assert labeled._read_label(_Parsed("Tutorials")) == "Tutorials"
    assert labeled._read_label(_Parsed("  tutorials ")) == "Tutorials"

    with pytest.raises(ValueError):
        labeled._read_label(_Parsed("Cooking"))
    with pytest.raises(ValueError):
        labeled._read_label(_Parsed(None))


def test_label_reading_is_off_unless_asked_for(migrated_settings):
    from app.services.extraction.gemini import GeminiExtractor

    assert GeminiExtractor(migrated_settings)._read_label(_Parsed("Tutorials")) is None


class _Parsed:
    """The minimum `response.parsed` shape `_read_label` touches."""

    def __init__(self, labels: object) -> None:
        self.labels = labels


# --------------------------------------------------------------------------
# Dataset loader
# --------------------------------------------------------------------------


@pytest.fixture
def synthetic_set(tmp_path: Path):
    return build_synthetic_set(tmp_path / "synthetic", TAXONOMY)


def test_loader_reads_images_labels_and_marks_them_synthetic(synthetic_set):
    assert synthetic_set.size == 8  # one per legacy-8 label
    assert synthetic_set.split == "synthetic"
    assert synthetic_set.labeled_count == synthetic_set.size
    assert synthetic_set.missing_gold_labels() == ()
    assert all(item.path.is_file() for item in synthetic_set.items)


def test_label_template_refuses_to_overwrite_existing_labels(tmp_path: Path):
    from curated_evals.synthetic import _render

    directory = tmp_path / "shots"
    directory.mkdir()
    _render(directory / "a.png", "Design", "A")
    written = write_label_template(directory, taxonomy_path=TAXONOMY)
    assert written.exists()

    with pytest.raises(EvalSetError):
        write_label_template(directory, taxonomy_path=TAXONOMY)


def test_label_template_leaves_the_label_column_blank(tmp_path: Path):
    """A template that pre-fills a label is a fabricated label."""
    import csv

    from curated_evals.synthetic import _render

    directory = tmp_path / "shots"
    directory.mkdir()
    _render(directory / "a.png", "Design", "A")
    _render(directory / "b.png", "Design", "B")

    write_label_template(directory, taxonomy_path=TAXONOMY)
    with (directory / "labels.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert all(row["category"] == "" for row in rows)
    assert all(row["title"] == "" and row["description"] == "" for row in rows)


def test_loader_rejects_a_gold_label_outside_the_taxonomy(tmp_path: Path, synthetic_set):
    labels_path = synthetic_set.root / "labels.csv"
    labels_path.write_text(
        labels_path.read_text(encoding="utf-8").replace(",Design\n", ",Cooking\n"),
        encoding="utf-8",
    )
    with pytest.raises(EvalSetError, match="not in taxonomy"):
        load_set(synthetic_set.root, TAXONOMY)


def test_loader_rejects_a_row_pointing_at_a_missing_file(synthetic_set):
    labels_path = synthetic_set.root / "labels.csv"
    labels_path.write_text(
        labels_path.read_text(encoding="utf-8").replace(".png", ".nope"),
        encoding="utf-8",
    )
    with pytest.raises(EvalSetError, match="missing file"):
        load_set(synthetic_set.root, TAXONOMY)


def test_folder_without_a_label_file_is_refused(tmp_path: Path):
    empty = tmp_path / "no-labels"
    empty.mkdir()
    with pytest.raises(EvalSetError, match="will not guess labels"):
        load_set(empty, TAXONOMY)


def test_unlabeled_rows_still_load(synthetic_set):
    """Latency and cost are measurable before anyone labels anything."""
    import csv

    labels_path = synthetic_set.root / "labels.csv"
    with labels_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    rows[0]["category"] = ""

    with labels_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    reloaded = load_set(synthetic_set.root, TAXONOMY)
    assert reloaded.size == synthetic_set.size
    assert reloaded.labeled_count == synthetic_set.size - 1
    assert len(reloaded.unlabeled()) == 1


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------


def test_accuracy_is_none_when_nothing_is_labeled():
    """The failure this guards: a perfect 1.000 over an empty denominator."""
    metrics = score_items([LabelObservation("a", None, "Tutorials", False)])
    assert metrics.accuracy is None
    assert metrics.macro_f1 is None
    assert metrics.n_labeled == 0


def test_an_abstention_is_scored_as_a_miss_not_a_hit():
    metrics = score_items([LabelObservation("a", "Tutorials", None, abstained=True)])
    assert metrics.accuracy == 0.0
    assert metrics.abstain_rate == 1.0


def test_per_class_precision_and_recall():
    metrics = score_items(
        [
            LabelObservation("a", "A", "A", False),
            LabelObservation("b", "A", "B", False),
            LabelObservation("c", "B", "B", False),
        ]
    )
    by_label = {c.label: c for c in metrics.per_class}
    # A was predicted once, and was right once; it was missed once.
    assert by_label["A"].precision == pytest.approx(1.0)
    assert by_label["A"].recall == pytest.approx(0.5)
    assert by_label["A"].support == 2
    # B was predicted twice, right once.
    assert by_label["B"].precision == pytest.approx(0.5)
    assert by_label["B"].recall == pytest.approx(1.0)


def test_accuracy_denominator_excludes_unlabeled_rows():
    metrics = score_items(
        [
            LabelObservation("a", "A", "A", False),
            LabelObservation("b", None, "B", False),
        ]
    )
    assert metrics.n == 2
    assert metrics.n_labeled == 1
    assert metrics.accuracy == 1.0


def test_percentiles_are_deterministic():
    latency = score_latency([100, 200, 300, 400, 500])
    assert latency.p50_ms == 300
    assert latency.p95_ms == 500
    assert score_latency([]).p50_ms is None


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------


class StubClassifier:
    """Returns a fixed label, optionally abstaining."""

    def __init__(self, label: str | None, *, abstained: bool = False) -> None:
        self._label = label
        self._abstained = abstained
        self.is_ready = True
        self.texts: list[str] = []

    def predict(self, text: str) -> Prediction:
        self.texts.append(text)
        labels = {"category": self._label} if self._label else {}
        return Prediction(
            labels=labels,
            score=0.9,
            abstained=self._abstained or self._label is None,
            model_version="stub",
            taxonomy_version="legacy-8",
        )


class DictCache:
    def __init__(self) -> None:
        self.store: dict[str, object] = {}

    def get(self, key: str):
        return self.store.get(key)

    def put(self, key: str, value) -> None:
        self.store[key] = value


def _prepare(data: bytes):
    """A stand-in for the firewall's output, shaped like a `ModelInput`."""
    from app.services.extraction.base import ModelInput

    class Prepared:
        def __init__(self) -> None:
            self.model_input = ModelInput(data=data, mime="image/png")
            self.content_sha256 = hashlib.sha256(data).hexdigest()

    return Prepared()


def _run(config: EvalConfig, set_, **kwargs):
    from curated_evals.fake import build_fake_extractor

    labels = set_.taxonomy.labels
    extractor = kwargs.pop("extractor", None) or build_fake_extractor(config, labels)
    return run_config(
        config,
        set_,
        extractor=extractor,
        classifier=kwargs.pop("classifier", None),
        prepare=kwargs.pop("prepare", _prepare),
        estimate_cost=kwargs.pop(
            "estimate_cost",
            lambda model, prompt, output: (prompt * 0.3 + output * 2.5) / 1_000_000,
        ),
        cache=kwargs.pop("cache", None),
        cache_key=kwargs.pop("cache_key", None),
        facet=set_.facet,
        **kwargs,
    )


def test_runner_scores_against_gold_and_reports_latency_and_cost(synthetic_set):
    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    result = _run(config, synthetic_set, classifier=StubClassifier("Design"))
    assert result.items == synthetic_set.size
    assert result.provider_calls == synthetic_set.size
    assert result.failures == ()
    assert result.latency["p50_ms"] is not None
    assert result.cost["usd_per_item"] is not None


def test_runner_marks_an_unpriced_model_unknown_rather_than_free(synthetic_set):
    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    result = _run(config, synthetic_set, estimate_cost=lambda *_: None)
    assert result.cost["usd_per_item"] is None
    assert result.cost["priced"] is False


def test_a_second_pass_over_the_same_pixels_makes_no_provider_call(synthetic_set):
    """The '< $0.002 per item, re-saves are free' claim, measured."""
    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    cache = DictCache()
    result = _run(
        config,
        synthetic_set,
        cache=cache,
        cache_key=lambda sha, cfg: f"{sha}|{cfg.model}",
        repeats=2,
    )
    assert result.cache_hits == synthetic_set.size
    assert result.provider_calls == synthetic_set.size
    assert result.cache_hit_rate == pytest.approx(0.5)


def test_a_failing_item_is_a_data_point_not_a_crash(synthetic_set):
    class Boom:
        def extract(self, image):
            raise RuntimeError("provider exploded")

    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    result = _run(config, synthetic_set, extractor=Boom())
    assert result.items == synthetic_set.size
    assert len(result.failures) == synthetic_set.size
    assert result.provider_calls == 0


def test_the_classifier_is_challenged_with_serving_text(synthetic_set):
    """Train/serving feature mismatch is what Milestone 4 fixed; keep it fixed."""
    classifier = StubClassifier("Design")
    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    _run(config, synthetic_set, classifier=classifier)
    assert classifier.texts
    assert all("Tags:" in text for text in classifier.texts)


def test_provider_label_and_classifier_label_agreement_is_reported(synthetic_set):
    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    config = EvalConfig(**{**config.as_dict(), "provider_labels": True})
    result = _run(config, synthetic_set, classifier=StubClassifier("Design"))
    assert result.agreement_n == synthetic_set.size
    assert 0.0 <= result.agreement_rate <= 1.0
    assert result.provider_metrics is not None


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def test_report_flags_a_synthetic_set_loudly(synthetic_set):
    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    report = build_report([_run(config, synthetic_set)], synthetic_set)
    table = render_table(report)
    assert "synthetic set" in table
    assert "not model quality" in table


def test_report_prints_n_a_rather_than_zero_for_an_uncomputable_metric(synthetic_set):
    """A 0 in the accuracy column reads as a result; n/a reads as 'no data'."""
    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    report = build_report(
        [_run(config, synthetic_set, estimate_cost=lambda *_: None)], synthetic_set
    )
    row = next(line for line in render_table(report).splitlines() if config.name in line)
    assert "n/a" in row


def test_report_is_json_serializable_and_holds_no_metadata(synthetic_set):
    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    result = _run(config, synthetic_set, classifier=StubClassifier("Design"))
    report = build_report([result], synthetic_set)
    payload = json.loads(json.dumps(report))

    blob = json.dumps(payload["runs"][0]["records"])
    assert "screenshot saved for later" not in blob, "extracted text leaked into telemetry"
    assert all(isinstance(r, ItemRecord) for r in result.records)


def test_report_carries_the_provenance_a_reader_needs(synthetic_set):
    config = by_name(matrix(), "gemini-3.5-flash-lite|medium|minimal")
    report = build_report(
        [_run(config, synthetic_set)],
        synthetic_set,
        pricing={"verified_on": "2026-10-11", "source": "https://example.test"},
    )
    assert report["set"]["split"] == "synthetic"
    assert report["set"]["taxonomy_version"] == "legacy-8"
    assert report["pricing"]["verified_on"] == "2026-10-11"
    assert report["runs"][0]["config"]["model"] == "gemini-3.5-flash-lite"


def test_cache_identity_includes_everything_that_changes_the_answer():
    """The key is the reason a stale answer is impossible, so it is tested."""
    plain = CacheIdentity("m", "p", SCHEMA_VERSION)
    labeled = CacheIdentity("m", "p", LABELED_SCHEMA_VERSION)
    assert plain != labeled
    assert CacheIdentity("m", "p", SCHEMA_VERSION) != CacheIdentity("m2", "p", SCHEMA_VERSION)
