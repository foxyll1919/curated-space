"""In-process job recovery and dispatch behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.models import Item
from app.services.jobs import recover_interrupted_items


def test_recovery_resets_only_stale_processing_and_returns_pending_ids(migrated_settings):
    from app.db.session import create_database_engine, create_session_factory

    # The regular fixture already migrates to head; open its database through
    # the same configured path so the recovery helper uses the app session type.
    engine = create_database_engine(migrated_settings)
    sessions = create_session_factory(engine)
    stale_id = "11111111-1111-1111-1111-111111111111"
    fresh_id = "22222222-2222-2222-2222-222222222222"
    pending_id = "33333333-3333-3333-3333-333333333333"
    old_time = datetime.now(UTC) - timedelta(hours=1)
    with sessions() as session:
        session.add_all(
            [
                Item(id=stale_id, status="processing", image_key="stale.png", updated_at=old_time),
                Item(id=fresh_id, status="processing", image_key="fresh.png"),
                Item(id=pending_id, status="pending", image_key="pending.png"),
            ]
        )
        session.commit()

    ids = recover_interrupted_items(sessions, stuck_after_minutes=15)

    with sessions() as session:
        rows = {row.id: row for row in session.scalars(select(Item))}
    assert set(ids) == {stale_id, pending_id}
    assert rows[stale_id].status == "pending"
    assert rows[stale_id].error_code is None
    assert rows[fresh_id].status == "processing"
    assert rows[pending_id].status == "pending"
    engine.dispose()


def test_app_startup_requeues_stale_processing_item(migrated_settings, extractor, classifier):
    from fastapi.testclient import TestClient

    from app.db.session import create_database_engine, create_session_factory
    from app.main import create_app
    from app.services.storage import LocalDiskStorage
    from tests.conftest import make_image

    engine = create_database_engine(migrated_settings)
    sessions = create_session_factory(engine)
    storage = LocalDiskStorage(migrated_settings.storage_path)
    item_id = "44444444-4444-4444-4444-444444444444"
    image_key = storage.put(item_id, make_image())
    with sessions() as session:
        session.add(
            Item(
                id=item_id,
                status="processing",
                image_key=image_key,
                content_sha256="stale-hash",
                mime="image/png",
                width=64,
                height=48,
                byte_size=100,
                updated_at=datetime.now(UTC) - timedelta(hours=1),
            )
        )
        session.commit()
    engine.dispose()

    app = create_app(migrated_settings, extractor=extractor, storage=storage, classifier=classifier)
    with TestClient(app):
        pass

    with app.state.session_factory() as session:
        item = session.get(Item, item_id)
    assert item.status == "ready"
    assert len(extractor.calls) == 1
