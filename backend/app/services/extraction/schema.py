from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, create_model, field_validator


SCHEMA_VERSION = "metadata-v1"

#: The label-emitting variant has a different response shape, so it must have a
#: different version. Otherwise a cached labeled answer could be served to an
#: unlabeled request and vice versa, under a key that cannot tell them apart.
LABELED_SCHEMA_VERSION = "metadata-v1+labels"

MAX_TAGS = 8
MIN_TAG_LENGTH = 2
MAX_TAG_LENGTH = 30

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_HTML_TAG = re.compile(r"<[^>]*>")
_WHITESPACE = re.compile(r"\s+")


class ExtractedMetadata(BaseModel):
    """The schema-constrained shape of everything Gemini is allowed to return.

    Passed to the provider as `response_schema` and then validated again here.
    Provider output is untrusted input; this model is the first boundary.
    """

    title: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=280)
    tags: list[str] = Field(default_factory=list, max_length=MAX_TAGS)

    @field_validator("tags")
    @classmethod
    def _check_tags(cls, value: list[str]) -> list[str]:
        if any(
            not isinstance(tag, str) or not MIN_TAG_LENGTH <= len(tag) <= MAX_TAG_LENGTH
            for tag in value
        ):
            raise ValueError("tag length out of range")
        return value


def _clean_text(value: str) -> str:
    text = unicodedata.normalize("NFC", value)
    text = _CONTROL_CHARS.sub(" ", text)
    text = _HTML_TAG.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()


def sanitize_metadata(metadata: ExtractedMetadata) -> ExtractedMetadata:
    """Post-rules applied after schema validation.

    Lowercase and dedupe tags, collapse whitespace, strip markup and control
    characters, and drop anything that becomes empty or out of range. Model
    output is never persisted verbatim.
    """
    tags: list[str] = []
    for raw in metadata.tags:
        tag = _clean_text(raw).lower()
        if not MIN_TAG_LENGTH <= len(tag) <= MAX_TAG_LENGTH:
            continue
        if tag not in tags:
            tags.append(tag)
        if len(tags) == MAX_TAGS:
            break

    title = _clean_text(metadata.title)
    description = _clean_text(metadata.description)
    if not title or not description:
        raise ValueError("metadata is empty after sanitizing")
    return ExtractedMetadata(
        title=title[:80],
        description=description[:280],
        tags=tags,
    )


def build_labeled_schema(labels: Sequence[str]) -> type[ExtractedMetadata]:
    """Build the label-emitting response schema from a taxonomy, at runtime.

    The enum values come from the taxonomy file and never from a hard-coded
    list, so a taxonomy change is a data change. `Literal` over the label tuple
    is what makes the provider *structurally* unable to return an off-taxonomy
    value; the post-validator then re-checks membership anyway, because a
    constrained schema is a request, not a guarantee.

    Used only by the Milestone 6 eval harness. Because it changes the response
    schema, it also changes the schema version, and therefore the cache key.
    """
    if not labels:
        raise ValueError("a labeled schema needs at least one taxonomy label")
    # Building a `Literal` from a runtime tuple is the whole point here, and mypy
    # cannot express it. The validation it wants is done below instead.
    taxonomy_literal = Literal[tuple(labels)]  # type: ignore[valid-type]
    return create_model(
        "ExtractedMetadataWithLabels",
        __base__=ExtractedMetadata,
        labels=(
            cast("Any", taxonomy_literal),
            Field(description=f"Taxonomy label. One of: {', '.join(labels)}"),
        ),
    )


def validate_labels(value: object, labels: Sequence[str]) -> str:
    """Return the label, or raise if it is not in the taxonomy.

    Case is normalized rather than rejected, because an enum-constrained
    response still arrives as text and a lowercase label is the same label.
    Anything else is refused rather than coerced, so an invented category can
    never be stored.
    """
    if not isinstance(value, str):
        raise ValueError("label must be a string")
    for candidate in labels:
        if candidate.lower() == value.strip().lower():
            return candidate
    raise ValueError(f"label {value!r} is not in the taxonomy")
