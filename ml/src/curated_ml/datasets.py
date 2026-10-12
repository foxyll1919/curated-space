"""Loaders for training data and the human-labeled holdout.

The holdout is the only data that may justify a quality claim or a tuned
abstention threshold. It is kept separate from the training set and is never
split, never tuned on, and never written by the training script.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ("text", "category")


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_labeled_csv(path: str | Path) -> pd.DataFrame:
    """Load and minimally validate a labeled CSV."""
    frame = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing required column(s): {', '.join(missing)}")
    if frame.empty:
        raise ValueError(f"{path} has no rows")
    if frame[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError(f"{path} has rows with an empty text or category")
    return frame


def load_holdout(path: str | Path) -> pd.DataFrame | None:
    """Load the human-labeled holdout, or None when the owner has not supplied one.

    Returns None rather than inventing an empty evaluation. An absent holdout
    means no quality claim may be made, and it must not silently become a
    substitute for one.
    """
    holdout_path = Path(path)
    if not holdout_path.exists():
        return None
    if not holdout_path.is_file() or holdout_path.stat().st_size == 0:
        return None
    return load_labeled_csv(holdout_path)
