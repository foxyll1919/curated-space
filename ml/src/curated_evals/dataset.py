"""Loading a labeled screenshot set, and refusing to invent one.

An eval set is a folder of images plus a `labels.csv` the owner writes by hand.
This loader is strict about the things that quietly corrupt an eval: a row
pointing at a missing file, a duplicate id, a label outside the taxonomy, and a
set that has no labels at all (which is not an error, but changes what the run
is allowed to claim).

Nothing in this module writes gold labels. `write_label_template` writes an empty
label file so the work of labeling is mechanical; the judging is still the
owner's.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from curated_ml.taxonomy import Taxonomy, load_taxonomy
from curated_ml.text import normalize_tags


#: Column names the loader understands. `file` is relative to the set root.
REQUIRED_COLUMNS = ("id", "file")
#: A row with no value in `category` is unlabeled: it still runs, and still
#: contributes latency/cost, but contributes nothing to accuracy.
GOLD_LABEL_COLUMN = "category"

LABELS_FILENAME = "labels.csv"

IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"})

#: Label a generated set with this and every report has to carry it, so a
#: synthetic number can never be quoted as a real one.
SYNTHETIC_SPLIT = "synthetic"
REAL_SPLIT = "owner-labeled"


class EvalSetError(ValueError):
    """The set on disk cannot be evaluated as given."""


@dataclass(frozen=True)
class EvalItem:
    """One screenshot and whatever gold data exists for it."""

    id: str
    path: Path
    gold_title: str | None = None
    gold_description: str | None = None
    gold_tags: tuple[str, ...] = ()
    gold_label: str | None = None

    @property
    def is_labeled(self) -> bool:
        return self.gold_label is not None


@dataclass(frozen=True)
class LabeledSet:
    items: tuple[EvalItem, ...]
    taxonomy: Taxonomy
    split: str = REAL_SPLIT
    root: Path | None = None
    notes: str = ""

    @property
    def facet(self) -> str:
        return self.taxonomy.facet

    @property
    def size(self) -> int:
        return len(self.items)

    def labeled(self) -> tuple[EvalItem, ...]:
        return tuple(item for item in self.items if item.is_labeled)

    def unlabeled(self) -> tuple[EvalItem, ...]:
        return tuple(item for item in self.items if not item.is_labeled)

    @property
    def labeled_count(self) -> int:
        return sum(1 for item in self.items if item.is_labeled)

    def missing_gold_labels(self) -> tuple[str, ...]:
        """Taxonomy labels in the set with no row, so a coverage gap is visible."""
        present = {item.gold_label for item in self.items if item.gold_label}
        return tuple(label for label in self.taxonomy.labels if label not in present)


def load_set(source: str | Path, taxonomy_path: str | Path) -> LabeledSet:
    """Load a set from a folder or a CSV.

    A folder must contain images and a `labels.csv`. A CSV is read directly and
    its `file` column resolves against the CSV's own directory.
    """
    root = Path(source)
    taxonomy = load_taxonomy(taxonomy_path)

    if root.is_dir():
        csv_path = root / LABELS_FILENAME
        if not csv_path.is_file():
            raise EvalSetError(
                f"{root} has no {LABELS_FILENAME}. Write the label file first; "
                "this loader will not guess labels for images."
            )
        return _load_from_csv(csv_path, root, taxonomy, split=_split_marker(root))

    if root.is_file() and root.suffix.lower() == ".csv":
        return _load_from_csv(root, root.parent, taxonomy, split=_split_marker(root.parent))

    raise EvalSetError(f"{root} is neither a folder with {LABELS_FILENAME} nor a CSV")


def _split_marker(root: Path) -> str:
    """A generated set is marked with a file so the marker cannot be lost in a copy."""
    marker = root / "SYNTHETIC"
    return SYNTHETIC_SPLIT if marker.exists() else REAL_SPLIT


def _load_from_csv(csv_path: Path, root: Path, taxonomy: Taxonomy, *, split: str) -> LabeledSet:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise EvalSetError(f"{csv_path} is missing column(s): {', '.join(missing)}")

        seen: set[str] = set()
        items: list[EvalItem] = []
        for line_number, row in enumerate(reader, start=2):
            item_id = (row.get("id") or "").strip()
            relative = (row.get("file") or "").strip()
            if not item_id or not relative:
                raise EvalSetError(f"{csv_path}:{line_number} needs both id and file")
            if item_id in seen:
                raise EvalSetError(f"{csv_path}:{line_number} repeats id {item_id!r}")
            seen.add(item_id)

            path = (root / relative).resolve()
            if not path.is_file():
                raise EvalSetError(f"{csv_path}:{line_number} points at a missing file: {relative}")

            label = (row.get(GOLD_LABEL_COLUMN) or "").strip() or None
            if label is not None and label not in taxonomy:
                raise EvalSetError(
                    f"{csv_path}:{line_number} gold label {label!r} is not in taxonomy "
                    f"{taxonomy.version}. Valid labels: {', '.join(taxonomy.labels)}"
                )

            items.append(
                EvalItem(
                    id=item_id,
                    path=path,
                    gold_title=(row.get("title") or "").strip() or None,
                    gold_description=(row.get("description") or "").strip() or None,
                    gold_tags=tuple(normalize_tags(row.get("tags"))),
                    gold_label=label,
                )
            )

    if not items:
        raise EvalSetError(f"{csv_path} has a header but no rows")

    return LabeledSet(items=tuple(items), taxonomy=taxonomy, split=split, root=root)


def write_label_template(
    root: str | Path,
    *,
    taxonomy_path: str | Path,
    title: str | None = None,
    description: str | None = None,
) -> Path:
    """Write an empty `labels.csv` for the images already in `root`.

    Only useful when the folder has images and no label file. Every gold column
    is left blank on purpose: a template that pre-fills a label is a fabricated
    label.
    """
    directory = Path(root)
    images = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not images:
        raise EvalSetError(f"{directory} contains no images to list")

    labels_path = directory / LABELS_FILENAME
    if labels_path.exists():
        raise EvalSetError(f"{labels_path} already exists; refusing to overwrite your labels")

    load_taxonomy(taxonomy_path)  # Fail before writing if the taxonomy path is wrong.
    with labels_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "file", "title", "description", "tags", GOLD_LABEL_COLUMN],
        )
        writer.writeheader()
        for index, image in enumerate(images, start=1):
            writer.writerow(
                {
                    "id": f"{index:03d}",
                    "file": image.name,
                    "title": title or "",
                    "description": description or "",
                    "tags": "",
                    GOLD_LABEL_COLUMN: "",
                }
            )
    return labels_path


def summarize(set_: LabeledSet) -> dict[str, Any]:
    """Provenance block that goes at the top of every report."""
    label_counts: dict[str, int] = {}
    for item in set_.items:
        if item.gold_label:
            label_counts[item.gold_label] = label_counts.get(item.gold_label, 0) + 1
    return {
        "root": str(set_.root) if set_.root else None,
        "size": set_.size,
        "labeled": set_.labeled_count,
        "unlabeled": set_.size - set_.labeled_count,
        "split": set_.split,
        "taxonomy_version": set_.taxonomy.version,
        "facet": set_.facet,
        "labels": list(set_.taxonomy.labels),
        "label_counts": dict(sorted(label_counts.items())),
        "labels_with_no_rows": list(set_.missing_gold_labels()),
    }
