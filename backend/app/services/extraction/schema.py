from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel, Field, field_validator


SCHEMA_VERSION = "metadata-v1"

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
