"""Pixel-hash analysis cache.

A cache hit means zero provider calls, so re-saving an identical screenshot
never re-bills. The key carries every version that can change the answer:

    sha256(normalized pixels) + model + prompt_version + schema_version

The hash is of the decoded, normalized pixel buffer (see `image_firewall`), not
of the re-encoded file, so a Pillow upgrade does not invalidate every entry.
Changing the prompt, the schema or the model produces a different key, which
is the whole point of putting the versions in the key rather than expiring rows.

Stored values are already-sanitized metadata. They are re-validated on read: a
corrupt or hand-edited row must degrade to a miss, never to a served item.
"""

from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.models import AnalysisCache
from app.services.extraction.base import CacheIdentity
from app.services.extraction.schema import ExtractedMetadata


CACHE_HIT_STATUS = "cache_hit"


def cache_key(content_sha256: str, identity: CacheIdentity) -> str:
    return "|".join(
        (content_sha256, identity.model, identity.prompt_version, identity.schema_version)
    )


def lookup(session: Session, key: str) -> ExtractedMetadata | None:
    """Return cached metadata, or None for a miss or an unusable row."""
    row = session.get(AnalysisCache, key)
    if row is None:
        return None
    try:
        return ExtractedMetadata.model_validate(row.value)
    except (ValidationError, TypeError):
        # A row we cannot trust is a miss, not an error: the provider call is
        # still the correct fallback.
        return None


def store(session: Session, key: str, metadata: ExtractedMetadata) -> None:
    """Upsert the validated metadata under `key`. Carries no image bytes."""
    value = metadata.model_dump(mode="json")
    row = session.get(AnalysisCache, key)
    if row is None:
        session.add(AnalysisCache(key=key, value=value))
        return
    row.value = value
