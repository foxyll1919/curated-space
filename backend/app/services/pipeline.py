from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.errors import AppError, ExtractionError
from app.db.models import Item
from app.services.extraction.base import MetadataExtractor, ModelInput
from app.services.image_firewall import prepare_model_input
from app.services.storage import Storage
from app.services.usage import record_usage


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
    ) -> None:
        self.settings = settings
        self.extractor = extractor
        self.storage = storage
        self.session_factory = session_factory


def process_item(item_id: str, context: PipelineContext) -> None:
    """Analyze one stored item. Idempotent and safe to call inline or from a job.

    The upload route calls this directly today. Milestone 8 schedules the same
    function in the background after flipping the row to `pending` first, so
    this function must never assume it owns the row's initial state.
    """
    with context.session_factory() as session:
        item = session.get(Item, item_id)
        if item is None:
            return
        if item.status == "ready" and item.analyzed_at is not None:
            return
        item.status = "processing"
        session.commit()
        image_key = item.image_key

    if not context.settings.analysis_enabled:
        _finish(item_id, status="deferred", error_code="analysis_disabled", context=context)
        return

    started = datetime.now(UTC)
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
        item = session.get(Item, item_id)
        if item is None:
            return
        record_usage(
            session,
            item_id=item_id,
            settings=context.settings,
            model=result.model,
            usage=result.usage,
            latency_ms=result.latency_ms,
            status="ok",
        )
        item.status = "ready"
        item.title = result.metadata.title
        item.description = result.metadata.description
        item.tags = result.metadata.tags
        item.extractor_model = result.model
        item.prompt_version = result.prompt_version
        item.error_code = None
        item.analyzed_at = started
        session.commit()


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


def list_items(
    session: Session,
    *,
    owner_id: str | None,
    status: str | None,
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
