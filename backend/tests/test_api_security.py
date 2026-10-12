"""Milestone 9 API authentication, privacy controls and limits."""

from __future__ import annotations

import io
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Item
from app.main import create_app
from app.services.jobs import purge_expired_items
from app.services.storage import LocalDiskStorage
from tests.conftest import FakeExtractor, make_image


def test_item_and_usage_routes_reject_missing_api_key(client):
    for path in ("/api/v1/items", "/api/v1/usage"):
        response = client.get(path, headers={"X-API-Key": ""})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"
        assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
        assert "nosniff" == response.headers["x-content-type-options"]
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"


def test_other_owner_cannot_read_image_edit_delete_or_reanalyze(client):
    uploaded = client.post(
        "/api/v1/items", files={"file": ("shot.png", io.BytesIO(make_image()), "image/png")}
    )
    item_id = uploaded.json()["id"]
    with client.app.state.session_factory() as session:
        session.execute(
            Item.__table__.update().where(Item.id == item_id).values(owner_id="other-owner")
        )
        session.commit()

    responses = [
        client.get(f"/api/v1/items/{item_id}"),
        client.get(f"/api/v1/items/{item_id}/image"),
        client.patch(f"/api/v1/items/{item_id}", json={"title": "private"}),
        client.delete(f"/api/v1/items/{item_id}"),
        client.post(f"/api/v1/items/{item_id}/reanalyze"),
    ]
    assert [response.status_code for response in responses] == [404] * len(responses)


def test_skip_analysis_stores_owner_bound_deferred_item_without_provider_call(
    migrated_settings, classifier
):
    extractor = FakeExtractor()
    app = create_app(migrated_settings, extractor=extractor, classifier=classifier)
    with TestClient(app, headers={"X-API-Key": "test-api-key"}) as client:
        response = client.post(
            "/api/v1/items",
            data={"skip_analysis": "true"},
            files={"file": ("shot.png", io.BytesIO(make_image()), "image/png")},
        )
        assert response.status_code == 202
        assert response.json()["status"] == "deferred"
        item_id = response.json()["id"]
        item = client.get(f"/api/v1/items/{item_id}").json()
    assert item["error_code"] == "analysis_skipped"
    assert extractor.calls == []
    with app.state.session_factory() as session:
        stored = session.get(Item, item_id)
    assert stored.owner_id == "legacy-owner"


def test_upload_rate_limit_is_enforced_per_key_and_ip(migrated_settings, classifier):
    settings = migrated_settings.model_copy(update={"upload_rate_limit": 1})
    app = create_app(settings, extractor=FakeExtractor(), classifier=classifier)
    with TestClient(app, headers={"X-API-Key": "test-api-key"}) as client:
        first = client.post(
            "/api/v1/items", files={"file": ("shot.png", io.BytesIO(make_image()), "image/png")}
        )
        second = client.post(
            "/api/v1/items", files={"file": ("shot.png", io.BytesIO(make_image(65)), "image/png")}
        )
    assert first.status_code == 202
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limited"


def test_app_body_limit_and_cors_allowlist(migrated_settings, extractor, classifier):
    settings = migrated_settings.model_copy(
        update={"max_request_body_bytes": 1024, "allowed_origins": ["https://app.example"]}
    )
    app = create_app(settings, extractor=extractor, classifier=classifier)
    with TestClient(app, headers={"X-API-Key": "test-api-key"}) as client:
        too_large = client.post("/api/v1/items", content=b"x" * 2048)
        allowed = client.options(
            "/api/v1/items",
            headers={
                "Origin": "https://app.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        rejected = client.options(
            "/api/v1/items",
            headers={"Origin": "https://attacker.example", "Access-Control-Request-Method": "POST"},
        )
    assert too_large.status_code == 413
    assert too_large.json()["error"]["request_id"] == too_large.headers["x-request-id"]
    assert allowed.headers["access-control-allow-origin"] == "https://app.example"
    assert "access-control-allow-origin" not in rejected.headers


def test_retention_purges_old_rows_and_blobs_but_keeps_recent_items(
    migrated_settings, extractor, classifier
):
    from app.db.session import create_database_engine, create_session_factory

    storage = LocalDiskStorage(migrated_settings.storage_path)
    engine = create_database_engine(migrated_settings)
    sessions = create_session_factory(engine)
    cutoff = datetime.now(UTC) - timedelta(days=10)
    old_id = "11111111-1111-1111-1111-111111111111"
    recent_id = "22222222-2222-2222-2222-222222222222"
    old_key = storage.put(old_id, make_image())
    recent_key = storage.put(recent_id, make_image(65))
    with sessions() as session:
        session.add_all(
            [
                Item(id=old_id, image_key=old_key, created_at=cutoff - timedelta(days=1)),
                Item(id=recent_id, image_key=recent_key, created_at=cutoff + timedelta(days=1)),
            ]
        )
        session.commit()

    count = purge_expired_items(sessions, storage, retention_days=10)

    with sessions() as session:
        remaining = set(session.scalars(select(Item.id)))
    assert count == 1
    assert remaining == {recent_id}
    assert not storage._resolve(old_key).exists()
    assert storage._resolve(recent_key).exists()
    engine.dispose()
