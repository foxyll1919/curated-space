"""Schema validation, tag post-rules and prompt-injection resistance."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.extraction.schema import ExtractedMetadata, sanitize_metadata


def test_rejects_oversized_title():
    with pytest.raises(ValidationError):
        ExtractedMetadata(title="x" * 81, description="ok", tags=[])


def test_rejects_too_many_tags():
    with pytest.raises(ValidationError):
        ExtractedMetadata(title="ok", description="ok", tags=[f"tag{i:02d}" for i in range(9)])


def test_rejects_short_tag():
    with pytest.raises(ValidationError):
        ExtractedMetadata(title="ok", description="ok", tags=["a"])


def test_sanitize_lowercases_and_dedupes_tags():
    result = sanitize_metadata(
        ExtractedMetadata(
            title="  Dashboard   Overview ",
            description="Line one\nline two",
            tags=["  UI ", "ui", "Design", "Design"],
        )
    )
    assert result.title == "Dashboard Overview"
    assert result.description == "Line one line two"
    assert result.tags == ["ui", "design"]


def test_sanitize_strips_markup_and_control_characters():
    result = sanitize_metadata(
        ExtractedMetadata(
            title="<b>Settings</b> page",
            description="Uses a zero-width char",
            tags=["<i>italic</i>", "clean"],
        )
    )
    assert "<" not in result.title
    assert "Settings" in result.title
    assert result.description == "Uses a zero-width char"
    assert result.tags == ["italic", "clean"]


def test_sanitize_drops_tags_that_normalize_to_nothing():
    # "<i></i>" passes the schema's length check, then cleans to empty.
    result = sanitize_metadata(
        ExtractedMetadata(title="ok", description="ok", tags=["<i></i>", "keep"])
    )
    assert result.tags == ["keep"]


def test_sanitize_rejects_empty_after_cleaning():
    with pytest.raises(ValueError):
        sanitize_metadata(ExtractedMetadata(title="   ", description="ok", tags=[]))
