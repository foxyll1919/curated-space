from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.models import Item


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; the API contract is UTC-aware."""
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class ImageInfo(BaseModel):
    mime: str
    width: int
    height: int
    byte_size: int


class ItemResponse(BaseModel):
    """The public contract. Never exposes storage keys or filesystem paths."""

    id: str
    status: str
    image: ImageInfo
    title: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    abstained: bool = False
    # A LinearSVC decision margin, NOT a probability. Do not rename to
    # "confidence": LinearSVC has no predict_proba and is uncalibrated.
    classifier_score: float | None = None
    taxonomy_version: str | None = None
    classifier_version: str | None = None
    extractor_model: str | None = None
    prompt_version: str | None = None
    error_code: str | None = None
    user_corrected: bool = False
    created_at: datetime
    updated_at: datetime
    analyzed_at: datetime | None = None

    _utc_created_at = field_validator("created_at")(_as_utc)
    _utc_updated_at = field_validator("updated_at")(_as_utc)
    _utc_analyzed_at = field_validator("analyzed_at")(_as_utc)

    @classmethod
    def from_model(cls, item: Item) -> "ItemResponse":
        return cls(
            id=item.id,
            status=item.status,
            image=ImageInfo(
                mime=item.mime or "application/octet-stream",
                width=item.width or 0,
                height=item.height or 0,
                byte_size=item.byte_size or 0,
            ),
            title=item.title,
            description=item.description,
            tags=list(item.tags or []),
            labels=dict(item.labels or {}),
            abstained=item.abstained,
            classifier_score=item.classifier_score,
            taxonomy_version=item.taxonomy_version,
            classifier_version=item.classifier_version,
            extractor_model=item.extractor_model,
            prompt_version=item.prompt_version,
            error_code=item.error_code,
            user_corrected=item.user_corrected,
            created_at=item.created_at,
            updated_at=item.updated_at,
            analyzed_at=item.analyzed_at,
        )


class ItemListResponse(BaseModel):
    items: list[ItemResponse]
    next_cursor: str | None = None


class AcceptedItem(BaseModel):
    id: str
    status: str = "pending"


class ItemPatch(BaseModel):
    """Validated user corrections accepted by PATCH /items/{id}."""

    model_config = {"extra": "forbid"}

    title: str | None = Field(default=None, max_length=80)
    tags: list[str] | None = Field(default=None, max_length=8)
    labels: dict[str, str] | None = Field(default=None, max_length=8)

    @model_validator(mode="after")
    def require_changes(self) -> "ItemPatch":
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        return self

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = unicodedata.normalize("NFC", value)
        value = re.sub(r"[\x00-\x1f\x7f]", " ", value)
        value = re.sub(r"<[^>]*>", " ", value)
        value = " ".join(value.split())
        if not value:
            raise ValueError("title cannot be empty")
        return value[:80]

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned: list[str] = []
        for value in values:
            tag = unicodedata.normalize("NFC", value)
            tag = re.sub(r"[\x00-\x1f\x7f]", " ", tag)
            tag = re.sub(r"<[^>]*>", " ", tag)
            tag = " ".join(tag.split()).lower()
            if not 2 <= len(tag) <= 30:
                raise ValueError("tag length must be between 2 and 30 characters")
            if tag not in cleaned:
                cleaned.append(tag)
        return cleaned

    @field_validator("labels")
    @classmethod
    def clean_labels(cls, labels: dict[str, str] | None) -> dict[str, str] | None:
        if labels is None:
            return None
        cleaned: dict[str, str] = {}
        for key, value in labels.items():
            clean_key = " ".join(key.split())
            clean_value = " ".join(value.split())
            if not clean_key or len(clean_key) > 64 or len(clean_value) > 80:
                raise ValueError("label key or value length is out of range")
            cleaned[clean_key] = clean_value
        return cleaned
