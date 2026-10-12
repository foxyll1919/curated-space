from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

from sqlalchemy import String, and_, column, delete, or_, select, table, text, update
from sqlalchemy.orm import Session, sessionmaker

from curated_ml.text import build_text

from app.core.config import Settings
from app.core.errors import AppError, BadRequestError, ExtractionError
from app.db.models import AnalysisCache, Item
from app.services.analysis_cache import (
    cache_key,
    lookup as cache_lookup,
    store as cache_store,
)
from app.services.budget import evaluate_budget
from app.services.classification.base import Classifier
from app.services.extraction.base import (
    CacheIdentity,
    MetadataExtractor,
    ModelInput,
    TokenUsage,
)
from app.services.extraction.schema import ExtractedMetadata
from app.services.image_firewall import prepare_model_input
from app.services.storage import Storage
from app.services.usage import record_cache_hit, record_usage


logger = logging.getLogger(__name__)


class PipelineContext:
    """Everything the pipeline needs, passed in so tests can swap each piece."""

    def __init__(
        self,
        *,
        settings: Settings,
        extractor: MetadataExtractor,
        storage: Storage,
        session_factory: sessionmaker[Session],
        classifier: Classifier | None = None,
    ) -> None:
        self.settings = settings
        self.extractor = extractor
        self.storage = storage
        self.session_factory = session_factory
        self.classifier = classifier


def process_item(item_id: str, context: PipelineContext) -> None:
    """Analyze one stored item after atomically claiming a retryable state."""
    with context.session_factory() as session:
        claimed_id = session.scalar(
            update(Item)
            .where(
                Item.id == item_id,
                Item.status.in_(("pending", "failed", "deferred")),
            )
            .values(status="processing", error_code=None, updated_at=datetime.now(UTC))
            .returning(Item.id)
        )
        if claimed_id is None:
            return
        session.commit()
        item = session.get(Item, item_id)
        if item is None:
            return
        image_key = item.image_key
        content_sha256 = item.content_sha256

    if not context.settings.analysis_enabled:
        _finish(item_id, status="deferred", error_code="analysis_disabled", context=context)
        return

    identity = context.extractor.cache_identity
    started = datetime.now(UTC)

    cached = _read_cache(item_id, content_sha256, identity, context)
    if cached is not None:
        logger.info("analysis_cache_hit", extra={"item_id": item_id, "stage": "cache"})
        _complete(item_id, cached, identity.model, identity.prompt_version, started, context)
        return

    deferral = _budget_deferral(item_id, context)
    if deferral is not None:
        _finish(item_id, status="deferred", error_code=deferral, context=context)
        return

    try:
        image_bytes = context.storage.get(image_key)
        result = context.extractor.extract(
            ModelInput(
                data=prepare_model_input(image_bytes, context.settings),
                mime="image/png",
            )
        )
    except ExtractionError as exc:
        _finish(item_id, status="failed", error_code=exc.code, context=context)
        return
    except AppError as exc:
        _finish(item_id, status="failed", error_code=exc.code, context=context)
        return
    except (OSError, ValueError) as exc:
        # Storage or a corrupt stored image. Full detail goes to the log only.
        logger.warning("item_analysis_failed", extra={"item_id": item_id, "stage": "analysis"})
        logger.debug("item_analysis_detail", exc_info=exc)
        _finish(item_id, status="failed", error_code="analysis_failed", context=context)
        return

    with context.session_factory() as session:
        _write_cache(session, content_sha256, identity, result.metadata, context)
        session.commit()

    _complete(
        item_id,
        result.metadata,
        result.model,
        result.prompt_version,
        started,
        context,
        usage=result.usage,
        latency_ms=result.latency_ms,
    )


def _read_cache(
    item_id: str, content_sha256: str | None, identity: CacheIdentity, context: PipelineContext
) -> ExtractedMetadata | None:
    """Return cached metadata, recording the hit. None means call the provider.

    A miss and an unusable cache are deliberately indistinguishable: both cost
    the same, one provider call, so there is nothing to branch on.
    """
    if not context.settings.analysis_cache_enabled or content_sha256 is None:
        return None
    key = cache_key(content_sha256, identity)
    with context.session_factory() as session:
        metadata = cache_lookup(session, key)
        if metadata is not None:
            record_cache_hit(
                session, item_id=item_id, settings=context.settings, model=identity.model
            )
            session.commit()
    return metadata


def _write_cache(
    session: Session,
    content_sha256: str | None,
    identity: CacheIdentity,
    metadata: ExtractedMetadata,
    context: PipelineContext,
) -> None:
    """Store the validated metadata under the key that requested it.

    Keyed on the *request's* identity rather than on whatever versions the
    response claimed, so a provider that under-reports its own version cannot
    poison the cache under a key that would never be looked up again.
    """
    if not context.settings.analysis_cache_enabled or content_sha256 is None:
        return
    cache_store(session, cache_key(content_sha256, identity), metadata)


def _budget_deferral(item_id: str, context: PipelineContext) -> str | None:
    """The `error_code` for a budget block, or None to proceed."""
    with context.session_factory() as session:
        decision = evaluate_budget(session, context.settings)
    if decision.allowed:
        return None
    logger.warning(
        "analysis_deferred_by_budget",
        extra={
            "item_id": item_id,
            "stage": "budget",
            "error_code": decision.error_code,
            "spent_today_usd": decision.spent_today_usd,
        },
    )
    return decision.error_code


def _complete(
    item_id: str,
    metadata: ExtractedMetadata,
    model: str,
    prompt_version: str,
    started: datetime,
    context: PipelineContext,
    *,
    usage: TokenUsage | None = None,
    latency_ms: int = 0,
) -> None:
    """Persist the metadata, its provenance and its cost row.

    `usage` is None for a cache hit: the caller already recorded the zero-cost
    row, and there are no tokens to attribute.
    """
    with context.session_factory() as session:
        item = session.get(Item, item_id)
        if item is None:
            return
        if usage is not None:
            record_usage(
                session,
                item_id=item_id,
                settings=context.settings,
                model=model,
                usage=usage,
                latency_ms=latency_ms,
                status="ok",
            )
        item.status = "ready"
        item.title = metadata.title
        item.description = metadata.description
        item.tags = metadata.tags
        item.extractor_model = model
        item.prompt_version = prompt_version
        item.error_code = None
        item.analyzed_at = started
        _apply_classification(item, metadata, context)
        session.commit()


def _apply_classification(
    item: Item, metadata: ExtractedMetadata, context: PipelineContext
) -> None:
    """Attach local-classifier labels. Never fails the item.

    The classifier is a challenger, not a dependency: if it is unavailable or
    raises, the item still reaches `ready` with no labels rather than being lost.
    """
    classifier = context.classifier
    if classifier is None or not classifier.is_ready:
        return
    try:
        prediction = classifier.predict(
            build_text(metadata.title, metadata.description, metadata.tags)
        )
    except Exception as exc:  # noqa: BLE001 - a challenger must not break the item
        logger.warning("classification_failed", extra={"item_id": item.id, "stage": "classify"})
        logger.debug("classification_detail", exc_info=exc)
        return
    item.labels = prediction.labels
    item.classifier_score = prediction.score
    item.abstained = prediction.abstained
    item.taxonomy_version = prediction.taxonomy_version
    item.classifier_version = prediction.model_version


def _finish(item_id: str, *, status: str, error_code: str, context: PipelineContext) -> None:
    with context.session_factory() as session:
        item = session.get(Item, item_id)
        if item is None:
            return
        item.status = status
        item.error_code = error_code
        item.analyzed_at = datetime.now(UTC)
        session.commit()


def create_item(
    *,
    id: str,
    image_key: str,
    content_sha256: str,
    mime: str,
    width: int,
    height: int,
    byte_size: int,
    owner_id: str | None,
    session: Session,
) -> Item:
    item = Item(
        id=id,
        owner_id=owner_id,
        status="pending",
        image_key=image_key,
        content_sha256=content_sha256,
        mime=mime,
        width=width,
        height=height,
        byte_size=byte_size,
    )
    session.add(item)
    session.commit()
    return item


def remove_item(session: Session, item: Item) -> None:
    """Remove item metadata and unreferenced analysis cache entries."""
    content_sha256 = item.content_sha256
    if content_sha256:
        another_item_uses_hash = session.scalar(
            select(Item.id)
            .where(Item.content_sha256 == content_sha256, Item.id != item.id)
            .limit(1)
        )
        if another_item_uses_hash is None:
            session.execute(
                delete(AnalysisCache).where(AnalysisCache.key.startswith(f"{content_sha256}|"))
            )
    # The llm_usage FK uses ON DELETE SET NULL, preserving aggregate cost data
    # without retaining a link to deleted item content.
    session.delete(item)
    session.commit()


def list_items(
    session: Session,
    *,
    owner_id: str | None,
    status: str | None,
    label: str | None = None,
    q: str | None = None,
    limit: int,
    cursor: str | None,
) -> list[Item]:
    """Newest-first keyset page over `(created_at, id)`.

    `created_at` alone is not a safe key: SQLite's `current_timestamp` has
    second resolution, so items saved in the same second would be skipped or
    repeated. Pairing it with the id gives a strict total order.
    """
    query = select(Item).where(
        Item.owner_id.is_(None) if owner_id is None else Item.owner_id == owner_id
    )
    if status:
        query = query.where(Item.status == status)
    if label:
        query = query.where(
            text("EXISTS (SELECT 1 FROM json_each(items.labels) WHERE json_each.value = :label)")
        ).params(label=label)
    if q:
        tokens = re.findall(r"[^\W_]+", q, flags=re.UNICODE)
        if not tokens:
            raise BadRequestError("Search query must contain at least one letter or number.")
        fts_query = " AND ".join(f'"{token}"' for token in tokens)
        fts = table("item_fts", column("item_id", String))
        matching_ids = select(fts.c.item_id).where(text("item_fts MATCH :fts_query"))
        query = query.where(Item.id.in_(matching_ids)).params(fts_query=fts_query)
    if cursor:
        anchor = session.get(Item, cursor)
        if anchor is not None and anchor.created_at is not None:
            query = query.where(
                or_(
                    Item.created_at < anchor.created_at,
                    and_(Item.created_at == anchor.created_at, Item.id < anchor.id),
                )
            )
    query = query.order_by(Item.created_at.desc(), Item.id.desc()).limit(limit)
    return list(session.scalars(query))
