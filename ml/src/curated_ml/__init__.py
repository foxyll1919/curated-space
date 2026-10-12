"""Shared by ml/train.py and the backend. No third-party imports at module scope
beyond what the card needs, so `taxonomy` and `text` stay cheap to import.
"""

from curated_ml.model_card import ClassMetrics, ModelCard, card_path_for, read_model_card
from curated_ml.model_card import write_model_card
from curated_ml.taxonomy import Taxonomy, load_taxonomy
from curated_ml.text import BUILD_TEXT_VERSION, build_text, build_text_from_raw, normalize_tags

__all__ = [
    "BUILD_TEXT_VERSION",
    "ClassMetrics",
    "ModelCard",
    "Taxonomy",
    "build_text",
    "build_text_from_raw",
    "card_path_for",
    "load_taxonomy",
    "normalize_tags",
    "read_model_card",
    "write_model_card",
]
