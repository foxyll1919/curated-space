from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator

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
