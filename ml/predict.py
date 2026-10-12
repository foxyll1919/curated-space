"""Predict a category with the trained classifier.

Run from the repository root:

    python ml/predict.py

Uses `curated_ml.build_text`, the same function training uses. The result is a
decision margin, not a probability, and the artifact is the legacy-8 placeholder
trained on synthetic data: treat its output as a code-path demonstration, not as
a real category assignment.
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
from curated_ml.model_card import card_path_for, read_model_card
from curated_ml.text import build_text


ML_DIR = Path(__file__).resolve().parent
ARTIFACT_PATH = ML_DIR / "model" / "curated_space_classifier_v2.pkl"

EXAMPLE = {
    "title": "React JWT authentication tutorial",
    "description": "Step-by-step guide to JWT auth in a React application",
    "tags": ["react", "jwt", "authentication", "javascript"],
}


def main() -> int:
    if not ARTIFACT_PATH.is_file():
        print(f"Artifact not found: {ARTIFACT_PATH}")
        print("Train it first:  python ml/train.py")
        return 1

    card = read_model_card(card_path_for(ARTIFACT_PATH))
    model = joblib.load(ARTIFACT_PATH)

    text = build_text(EXAMPLE["title"], EXAMPLE["description"], EXAMPLE["tags"])
    scores = model.decision_function([text])[0]
    ranking = sorted(zip(model.classes_, scores), key=lambda pair: pair[1], reverse=True)
    top_label, top_score = ranking[0]
    margin = top_score - ranking[1][1]

    print("Input text:")
    print(text)
    print(f"\nPredicted category: {top_label}")
    print(f"Top-1 vs top-2 margin: {margin:.4f}")
    print(f"Abstain threshold:     {card.abstention_threshold} ({card.threshold_source})")
    if margin < card.abstention_threshold:
        print("Abstained: the margin is below the threshold, so this item is uncategorized.")
    print("\nThis is a decision score, not a probability or a confidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
