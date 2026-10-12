"""Train the legacy-8 placeholder classifier and write its model card.

Run from the repository root:

    python ml/train.py

Hardened relative to the previous version:

- Fails on missing, empty or unknown labels instead of training anyway.
- Asserts the observed label set against a taxonomy FILE, never a hard-coded list.
- Writes a model card sidecar recording provenance and the abstention threshold.
- Reports macro-F1 and a per-class table.
- Refuses to overwrite an artifact unless an explicit `--output` says so.

The metrics printed here describe a synthetic, templated dataset. They are a
code-path check, NOT model-quality evidence. Do not quote them as accuracy.
"""

from __future__ import annotations

import argparse
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from curated_ml.datasets import file_sha256, load_holdout, load_labeled_csv
from curated_ml.model_card import ModelCard, card_path_for, write_model_card
from curated_ml.taxonomy import Taxonomy, load_taxonomy
from curated_ml.text import BUILD_TEXT_VERSION, build_text_from_raw


ML_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = ML_DIR / "dataset" / "curated_space_dataset.csv"
DEFAULT_TAXONOMY = ML_DIR / "taxonomy" / "legacy-8.json"
DEFAULT_HOLDOUT = ML_DIR / "holdout" / "holdout.csv"
DEFAULT_OUTPUT = ML_DIR / "model" / "curated_space_classifier_v2.pkl"

# Conservative fixed default. A margin threshold tuned on the synthetic split
# would be meaningless, so this is a placeholder until a human-labeled holdout
# exists. See build.md section 6.
DEFAULT_ABSTAIN_THRESHOLD = 0.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--holdout", type=Path, default=DEFAULT_HOLDOUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--abstain-threshold", type=float, default=DEFAULT_ABSTAIN_THRESHOLD)
    return parser.parse_args()


def assert_labels_match_taxonomy(observed: set[str], taxonomy: Taxonomy) -> None:
    unknown = observed - set(taxonomy.labels)
    missing = set(taxonomy.labels) - observed
    problems = []
    if unknown:
        problems.append(f"unexpected label(s): {', '.join(sorted(unknown))}")
    if missing:
        problems.append(f"taxonomy label(s) absent from the data: {', '.join(sorted(missing))}")
    if problems:
        raise SystemExit(
            f"Refusing to train: taxonomy '{taxonomy.version}' does not match the data. "
            + "; ".join(problems)
        )


def build_model() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2))),
            ("svm", LinearSVC(random_state=0)),
        ]
    )


def evaluate(model: Pipeline, x_test, y_test, labels: tuple[str, ...]) -> dict:
    predictions = model.predict(x_test)
    report = classification_report(y_test, predictions, labels=list(labels), zero_division=0)
    print("\nPer-class report:")
    print(report)
    macro_f1 = float(f1_score(y_test, predictions, average="macro", zero_division=0))
    print(f"macro-F1: {macro_f1:.4f}")
    return {"macro_f1": macro_f1, "report": report}


def evaluate_holdout(model: Pipeline, holdout_path: Path) -> dict | None:
    holdout = load_holdout(holdout_path)
    if holdout is None:
        print(
            f"\nNo human-labeled holdout at {holdout_path}. "
            "No quality claim can be made. See ml/holdout/README.md."
        )
        return None
    print(f"\nHuman-labeled holdout ({len(holdout)} rows):")
    predictions = model.predict(holdout["text"].map(build_text_from_raw))
    print(classification_report(holdout["category"], predictions, zero_division=0))
    return {
        "row_count": int(len(holdout)),
        "macro_f1": float(
            f1_score(holdout["category"], predictions, average="macro", zero_division=0)
        ),
        "sha256": file_sha256(holdout_path),
    }


def main() -> None:
    args = parse_args()
    taxonomy = load_taxonomy(args.taxonomy)
    frame = load_labeled_csv(args.data)

    print(f"Data: {args.data} ({len(frame)} rows)")
    print(f"Taxonomy: {taxonomy.version} ({len(taxonomy.labels)} labels)")
    assert_labels_match_taxonomy(set(frame["category"]), taxonomy)

    # Train through the SAME build_text serving uses. The dataset has one
    # free-text column, so it becomes the description. Passing the raw column
    # straight through would train on a different token layout from the one
    # serving produces, which is the format mismatch this module exists to stop.
    features = frame["text"].map(build_text_from_raw)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        frame["category"],
        test_size=args.test_size,
        random_state=args.seed,
        stratify=frame["category"],
    )
    print(f"Train {len(x_train)} / test {len(x_test)}")

    model = build_model()
    model.fit(x_train, y_train)

    # classes_ must be the label strings, never numeric ids. The retired
    # artifact's classes_ were 0..7 with an unrecoverable mapping.
    classes = [str(value) for value in model.named_steps["svm"].classes_]
    assert_labels_match_taxonomy(set(classes), taxonomy)

    metrics = evaluate(model, x_test, y_test, taxonomy.labels)
    holdout_metrics = evaluate_holdout(model, args.holdout)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output)

    card = ModelCard(
        model_version=f"{taxonomy.version}-tfidf-linear-svc",
        taxonomy_version=taxonomy.version,
        labels=list(taxonomy.labels),
        facet=taxonomy.facet,
        sklearn_version=sklearn.__version__,
        python_version=platform.python_version(),
        build_text_version=BUILD_TEXT_VERSION,
        training_data_sha256=file_sha256(args.data),
        training_row_count=int(len(frame)),
        metrics={**metrics, "split": "synthetic", "warning": "not quality evidence"},
        abstention_threshold=args.abstain_threshold,
        threshold_source="default-unvalidated",
        created_at=datetime.now(UTC).isoformat(),
        notes=(
            "Trained on a synthetic, templated dataset. The card's macro_f1 "
            "exercises the code path and is NOT model-quality evidence. The "
            "abstention threshold is an unvalidated placeholder."
        ),
    )
    if holdout_metrics:
        card.metrics["holdout"] = holdout_metrics
        card.threshold_source = "human-holdout"

    card_file = write_model_card(card, card_path_for(args.output))
    print(f"\nSaved artifact: {args.output}")
    print(f"Saved card:     {card_file}")


if __name__ == "__main__":
    sys.exit(main())
