"""The single text-building function used by BOTH training and serving.

There are historically three different text formats in this repo. They produced
three different feature spaces, which is why a model trained in one place could
not be compared honestly with a prediction made in another. Training and serving
now import this module and there is no second implementation.

`BUILD_TEXT_VERSION` is recorded in the model card. Changing the format without
bumping it silently invalidates every trained artifact, so bump it deliberately.
"""

from __future__ import annotations

from collections.abc import Iterable

BUILD_TEXT_VERSION = "build-text-v1"

TAGS_PREFIX = "Tags:"


def normalize_tags(tags: Iterable[str] | str | None) -> list[str]:
    """Accept a list or a comma-separated string and return a clean list."""
    if tags is None:
        return []
    raw = tags.split(",") if isinstance(tags, str) else list(tags)
    return [tag.strip() for tag in raw if isinstance(tag, str) and tag.strip()]


def build_text(
    title: str | None,
    description: str | None,
    tags: Iterable[str] | str | None,
) -> str:
    """Build the classifier input from extracted metadata.

    This is the contract between the Gemini extraction output and the local
    classifier. Changing it changes the feature space.

    The `Tags:` marker is always emitted, even with no tags, so that training
    and serving produce the same token layout.
    """
    return "\n".join(
        [
            (title or "").strip(),
            (description or "").strip(),
            f"{TAGS_PREFIX} {', '.join(normalize_tags(tags))}".rstrip(),
        ]
    )


def build_text_from_raw(raw: str | None) -> str:
    """Build training input from a dataset's single free-text column.

    The synthetic dataset has one `text` blob with no title/description split.
    Treating it as the description keeps the layout identical to serving so the
    `Tags:` token is present in both, which a raw pass-through would lose.
    """
    return build_text(None, raw, None)
