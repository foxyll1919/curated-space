from __future__ import annotations

import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.api.deps import SessionDep, get_pipeline_context, get_storage
from app.core.errors import AppError, NotFoundError
from app.db.models import Item
from app.schemas.items import ItemListResponse, ItemResponse
from app.services.image_firewall import read_bounded, sanitize_image
from app.services.pipeline import PipelineContext, create_item, list_items, process_item
from app.services.storage import Storage


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/items", tags=["items"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def upload_item(
    file: Annotated[UploadFile, File(description="Screenshot to save")],
    session: SessionDep,
    storage: Annotated[Storage, Depends(get_storage)],
    pipeline_context: Annotated[PipelineContext, Depends(get_pipeline_context)],
) -> ItemResponse:
    """Validate, store and analyze a screenshot in one call.

    Analysis runs inline today. Milestone 8 returns 202 with `status=pending`
    and schedules this same `process_item` in the background.
    """
    data = read_bounded(file.file, pipeline_context.settings.max_upload_bytes)
    sanitized = sanitize_image(data, pipeline_context.settings)

    item_id = str(uuid4())
    image_key = storage.put(item_id, sanitized.stored_bytes)
    item = create_item(
        id=item_id,
        image_key=image_key,
        content_sha256=sanitized.content_sha256,
        mime=sanitized.mime,
        width=sanitized.width,
        height=sanitized.height,
        byte_size=sanitized.byte_size,
        owner_id=None,
        session=session,
    )

    logger.info(
        "item_created",
        extra={"item_id": item_id, "stage": "upload", "duration_ms": 0},
    )
    try:
        process_item(item.id, pipeline_context)
    except AppError as exc:
        # A provider failure belongs on the item, never on the response body.
        logger.warning("item_analysis_error", extra={"item_id": item.id, "stage": "analysis"})
        logger.debug("item_analysis_error_detail", exc_info=exc)
    session.expire_all()
    refreshed = session.get(Item, item.id)
    assert refreshed is not None
    return ItemResponse.from_model(refreshed)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: str, session: SessionDep) -> ItemResponse:
    item = session.get(Item, item_id)
    if item is None or item.owner_id is not None:
        raise NotFoundError()
    return ItemResponse.from_model(item)


@router.get("", response_model=ItemListResponse)
def list_items_route(
    session: SessionDep,
    item_status: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    cursor: Annotated[str | None, Query()] = None,
) -> ItemListResponse:
    items = list_items(
        session,
        owner_id=None,
        status=item_status,
        limit=limit + 1,
        cursor=cursor,
    )
    next_cursor = None
    if len(items) > limit:
        items = items[:limit]
        next_cursor = items[-1].id
    return ItemListResponse(
        items=[ItemResponse.from_model(item) for item in items],
        next_cursor=next_cursor,
    )
