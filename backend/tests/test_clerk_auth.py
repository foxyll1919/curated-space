from __future__ import annotations

import io
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import deps
from app.db.models import Item, User
from app.db.session import create_database_engine, create_session_factory
from app.main import create_app
from tests.conftest import FakeClassifier, FakeExtractor, make_image


def _settings(settings):
    return settings.model_copy(
        update={
            "api_key": None,
            "auth_allow_registration": True,
            "clerk_jwt_key": "test-public-key",
            "allowed_origins": ["https://app.example"],
        }
    )


def _verified_request(_request, options):
    assert options.jwt_key == "test-public-key"
    assert options.authorized_parties == ["https://app.example"]
    assert options.accepts_token == ["session_token"]
    return SimpleNamespace(is_signed_in=True, payload={"sub": "user_clerk_test"})


def test_linking_clerk_identity_preserves_existing_item_owner(
    migrated_settings, monkeypatch
):
    settings = _settings(migrated_settings)
    app = create_app(settings, extractor=FakeExtractor(), classifier=FakeClassifier())
    monkeypatch.setattr(deps, "authenticate_request", _verified_request)

    with TestClient(app) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json={"email": "owner@example.com", "password": "a sufficiently long password"},
        )
        assert registration.status_code == 201
        user_id = registration.json()["user"]["id"]

        upload = client.post(
            "/api/v1/items",
            data={"skip_analysis": "true"},
            files={"file": ("shot.png", io.BytesIO(make_image()), "image/png")},
        )
        assert upload.status_code == 202
        item_id = upload.json()["id"]

        linked = client.post(
            "/api/v1/auth/link-clerk",
            headers={"Authorization": "Bearer test-clerk-token"},
        )
        assert linked.status_code == 200
        assert linked.json()["id"] == user_id

        client.cookies.clear()
        items = client.get(
            "/api/v1/items",
            headers={"Authorization": "Bearer test-clerk-token"},
        )
        assert items.status_code == 200
        assert [item["id"] for item in items.json()["items"]] == [item_id]

    engine = create_database_engine(settings)
    try:
        with create_session_factory(engine)() as session:
            user = session.get(User, user_id)
            item = session.get(Item, item_id)
            assert user is not None
            assert user.clerk_user_id == "user_clerk_test"
            assert item is not None
            assert item.owner_id == user_id
    finally:
        engine.dispose()


def test_clerk_identity_cannot_be_linked_to_a_second_local_account(
    migrated_settings, monkeypatch
):
    settings = _settings(migrated_settings)
    app = create_app(settings, extractor=FakeExtractor(), classifier=FakeClassifier())
    monkeypatch.setattr(deps, "authenticate_request", _verified_request)

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/auth/register",
            json={"email": "first@example.com", "password": "a sufficiently long password"},
        )
        assert first.status_code == 201
        linked = client.post(
            "/api/v1/auth/link-clerk",
            headers={"Authorization": "Bearer test-clerk-token"},
        )
        assert linked.status_code == 200

        client.post("/api/v1/auth/logout")
        second = client.post(
            "/api/v1/auth/register",
            json={"email": "second@example.com", "password": "another sufficiently long password"},
        )
        assert second.status_code == 201

        conflict = client.post(
            "/api/v1/auth/link-clerk",
            headers={"Authorization": "Bearer test-clerk-token"},
        )
        assert conflict.status_code == 409
        assert client.get("/api/v1/auth/me").json()["id"] == second.json()["user"]["id"]


def test_invalid_clerk_bearer_does_not_fall_back_to_cookie_or_api_key(
    migrated_settings, monkeypatch
):
    settings = migrated_settings.model_copy(
        update={
            "clerk_jwt_key": "test-public-key",
            "allowed_origins": ["https://app.example"],
        }
    )
    app = create_app(settings, extractor=FakeExtractor(), classifier=FakeClassifier())
    monkeypatch.setattr(
        deps,
        "authenticate_request",
        lambda _request, _options: SimpleNamespace(is_signed_in=False, payload=None),
    )

    with TestClient(app, headers={"X-API-Key": "test-api-key"}) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json={"email": "owner@example.com", "password": "a sufficiently long password"},
        )
        assert registration.status_code == 201
        response = client.get(
            "/api/v1/items",
            headers={"Authorization": "Bearer invalid-token"},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
