"""The taxonomy, loaded from a versioned JSON file.

Label strings are never hard-coded in application code. The backend reads them
from the model card, and the card records which taxonomy file produced it, so a
taxonomy change is a data change with a version bump rather than a code change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Taxonomy:
    version: str
    labels: tuple[str, ...]
    facet: str = "category"
    description: str = ""

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("taxonomy version is required")
        if not self.labels:
            raise ValueError("taxonomy must declare at least one label")
        if len(set(self.labels)) != len(self.labels):
            raise ValueError(f"taxonomy {self.version} contains duplicate labels")

    def __contains__(self, label: object) -> bool:
        return label in self.labels


def load_taxonomy(path: str | Path) -> Taxonomy:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        return Taxonomy(
            version=data["version"],
            labels=tuple(data["labels"]),
            facet=data.get("facet", "category"),
            description=data.get("description", ""),
        )
    except KeyError as exc:
        raise ValueError(f"taxonomy file {path} is missing key {exc}") from exc
