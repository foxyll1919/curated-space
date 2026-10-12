from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import OwnerDep, SessionDep, get_job_runner, get_pipeline_context, get_storage
from app.core.errors import ConflictError, NotFoundError, PayloadTooLargeError
from app.db.models import Item
from app.schemas.items import AcceptedItem, ItemListResponse, ItemPatch, ItemResponse
from app.services.image_firewall import read_bounded, sanitize_image
from app.services.jobs import JobRunner
from app.services.pipeline import PipelineContext, create_item, list_items, remove_item
from app.services.rate_limit import enforce_rate_limit
from app.services.storage import Storage


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/items", tags=["items"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def _owned_item(session: Session, item_id: str, owner_id: str) -> Item | None:
    return session.scalar(select(Item).where(Item.id == item_id, Item.owner_id == owner_id))


@router.post("", response_model=AcceptedItem, status_code=status.HTTP_202_ACCEPTED)
def upload_item(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="Screenshot to save")],
    session: SessionDep,
    owner_id: OwnerDep,
    storage: Annotated[Storage, Depends(get_storage)],
    pipeline_context: Annotated[PipelineContext, Depends(get_pipeline_context)],
    job_runner: Annotated[JobRunner, Depends(get_job_runner)],
    skip_analysis: Annotated[bool, Form()] = False,
) -> AcceptedItem:
    """Validate, store and analyze a screenshot in one call.

    Persist the sanitized image and pending row before scheduling the job.
    """
    # Starlette records the individual multipart part size while parsing it.
    # Use that hint to fail before copying it into our own buffer; the bounded
    # reader remains authoritative when size is absent or inaccurate.
    if file.size is not None and file.size > pipeline_context.settings.max_upload_bytes:
        raise PayloadTooLargeError()
    enforce_rate_limit(request, "upload")
    data = read_bounded(file.file, pipeline_context.settings.max_upload_bytes)
    sanitized = sanitize_image(data, pipeline_context.settings)
    analyze = pipeline_context.settings.analysis_enabled and not skip_analysis

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
        owner_id=owner_id,
        session=session,
    )

    logger.info(
        "item_created",
        extra={"item_id": item_id, "stage": "upload", "duration_ms": 0},
    )
    if analyze:
        job_runner.enqueue(background_tasks, item.id, pipeline_context)
        return AcceptedItem(id=item.id, status="pending")
    item.status = "deferred"
    item.error_code = "analysis_skipped" if skip_analysis else "analysis_disabled"
    session.commit()
    return AcceptedItem(id=item.id, status="deferred")


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: str, session: SessionDep, owner_id: OwnerDep) -> ItemResponse:
    item = _owned_item(session, item_id, owner_id)
    if item is None:
        raise NotFoundError()
    return ItemResponse.from_model(item)


@router.get("/{item_id}/image", response_class=Response, include_in_schema=True)
def get_item_image(
    item_id: str,
    session: SessionDep,
    owner_id: OwnerDep,
    storage: Annotated[Storage, Depends(get_storage)],
) -> Response:
    """Return only the sanitized image for an item visible to this caller.

    Ownership is checked before the storage layer reads any bytes.
    """
    item = _owned_item(session, item_id, owner_id)
    if item is None:
        raise NotFoundError()

    try:
        image_bytes = storage.get(item.image_key)
    except FileNotFoundError:
        # A missing blob is indistinguishable from a missing item to clients.
        raise NotFoundError() from None

    generated_name = f"screenshot-{UUID(item.id)}.png"
    return Response(
        content=image_bytes,
        media_type=item.mime or "image/png",
        headers={
            "Content-Disposition": f'inline; filename="{generated_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.patch("/{item_id}", response_model=ItemResponse)
def patch_item(
    item_id: str, body: ItemPatch, session: SessionDep, owner_id: OwnerDep
) -> ItemResponse:
    item = _owned_item(session, item_id, owner_id)
    if item is None:
        raise NotFoundError()
    if item.status in {"pending", "processing"}:
        raise ConflictError("The item cannot be corrected while analysis is running.")

    if "title" in body.model_fields_set:
        item.title = body.title
    if "tags" in body.model_fields_set:
        item.tags = body.tags or []
    if "labels" in body.model_fields_set:
        item.labels = body.labels or {}
    item.user_corrected = True
    session.commit()
    return ItemResponse.from_model(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: str,
    session: SessionDep,
    owner_id: OwnerDep,
    storage: Annotated[Storage, Depends(get_storage)],
) -> Response:
    item = _owned_item(session, item_id, owner_id)
    if item is None:
        raise NotFoundError()

    # Delete the blob first. LocalDiskStorage treats an already-missing blob as
    # deleted; other storage errors leave the database row intact for retry.
    storage.delete(item.image_key)
    remove_item(session, item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{item_id}/reanalyze",
    response_model=AcceptedItem,
    status_code=status.HTTP_202_ACCEPTED,
)
def reanalyze_item(
    request: Request,
    item_id: str,
    background_tasks: BackgroundTasks,
    session: SessionDep,
    owner_id: OwnerDep,
    pipeline_context: Annotated[PipelineContext, Depends(get_pipeline_context)],
    job_runner: Annotated[JobRunner, Depends(get_job_runner)],
) -> AcceptedItem:
    item = _owned_item(session, item_id, owner_id)
    if item is None:
        raise NotFoundError()
    enforce_rate_limit(request, "reanalyze")
    if item.status in {"pending", "processing"}:
        raise ConflictError("The item is already queued or processing.")

    item.status = "pending" if pipeline_context.settings.analysis_enabled else "deferred"
    item.error_code = None if pipeline_context.settings.analysis_enabled else "analysis_disabled"
    item.analyzed_at = None
    session.commit()
    if pipeline_context.settings.analysis_enabled:
        job_runner.enqueue(background_tasks, item.id, pipeline_context)
        return AcceptedItem(id=item.id, status="pending")
    return AcceptedItem(id=item.id, status="deferred")


@router.get("", response_model=ItemListResponse)
def list_items_route(
    session: SessionDep,
    owner_id: OwnerDep,
    item_status: Annotated[str | None, Query(alias="status")] = None,
    label: Annotated[str | None, Query(max_length=80)] = None,
    q: Annotated[str | None, Query(max_length=256)] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    cursor: Annotated[str | None, Query()] = None,
) -> ItemListResponse:
    items = list_items(
        session,
        owner_id=owner_id,
        status=item_status,
        label=label,
        q=q,
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
