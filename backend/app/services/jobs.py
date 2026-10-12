"""Narrow in-process job runner, replaceable by a durable queue later."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from threading import BoundedSemaphore
from typing import Protocol

from fastapi import BackgroundTasks
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.db.models import Item
from app.services.pipeline import PipelineContext, process_item, remove_item
from app.services.storage import Storage


logger = logging.getLogger(__name__)


class JobRunner(Protocol):
    def enqueue(
        self, background_tasks: BackgroundTasks, item_id: str, context: PipelineContext
    ) -> None: ...

    async def run_recovered(self, item_id: str, context: PipelineContext) -> None: ...


class BackgroundJobRunner:
    """FastAPI BackgroundTasks adapter with a bound on active analyses."""

    def __init__(self, max_concurrent: int) -> None:
        self._semaphore = BoundedSemaphore(max_concurrent)

    def enqueue(
        self, background_tasks: BackgroundTasks, item_id: str, context: PipelineContext
    ) -> None:
        background_tasks.add_task(self._run, item_id, context)

    async def run_recovered(self, item_id: str, context: PipelineContext) -> None:
        # Startup recovery has no request-owned BackgroundTasks instance.
        await run_in_threadpool(self._run, item_id, context)

    def _run(self, item_id: str, context: PipelineContext) -> None:
        with self._semaphore:
            try:
                process_item(item_id, context)
            except Exception as exc:  # noqa: BLE001 - background failures must not escape
                logger.error(
                    "background_job_crashed",
                    extra={"item_id": item_id, "stage": "job"},
                )
                logger.debug("background_job_crash_detail", exc_info=exc)


def recover_interrupted_items(
    session_factory: sessionmaker[Session], *, stuck_after_minutes: int
) -> list[str]:
    """Reset stale processing rows and return all pending IDs for requeueing."""
    cutoff = datetime.now(UTC) - timedelta(minutes=stuck_after_minutes)
    with session_factory() as session:
        if not inspect(session.get_bind()).has_table("items"):
            # Keep liveness/readiness available before the first migration.
            return []
        stale = list(
            session.scalars(
                select(Item).where(
                    Item.status == "processing",
                    Item.updated_at < cutoff,
                )
            )
        )
        for item in stale:
            item.status = "pending"
            item.error_code = None

        session.flush()
        pending_ids = list(session.scalars(select(Item.id).where(Item.status == "pending")))
        session.commit()
    return pending_ids


def purge_expired_items(
    session_factory: sessionmaker[Session], storage: Storage, *, retention_days: int
) -> int:
    """Delete expired item blobs and rows; zero disables automatic retention."""
    if retention_days <= 0:
        return 0
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    removed = 0
    with session_factory() as session:
        if not inspect(session.get_bind()).has_table("items"):
            return 0
        expired_ids = list(
            session.scalars(select(Item.id).where(Item.created_at < cutoff).order_by(Item.id))
        )
    for item_id in expired_ids:
        with session_factory() as session:
            item = session.get(Item, item_id)
            created_at = item.created_at if item is not None else None
            if created_at is not None and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
            if item is None or created_at is None or created_at >= cutoff:
                continue
            storage.delete(item.image_key)
            remove_item(session, item)
            removed += 1
    return removed


def retain_task(task: asyncio.Task[None], tasks: set[asyncio.Task[None]]) -> None:
    """Keep startup jobs alive until completion and remove their references."""
    tasks.add(task)
    task.add_done_callback(tasks.discard)
