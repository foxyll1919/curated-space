"""Tests for Supabase Postgres URL resolution and Supabase Storage adapter."""

from __future__ import annotations

import httpx
import pytest
from pydantic import SecretStr

from app.db.session import is_sqlite_url, resolve_database_url
from app.services.storage import LocalDiskStorage, SupabaseStorage, build_storage
from tests.conftest import make_settings


def test_resolve_database_url_normalizes_postgres_schemes(tmp_path):
    sqlite_settings = make_settings(tmp_path)
    assert is_sqlite_url(resolve_database_url(sqlite_settings))

    pg_settings = make_settings(
        tmp_path,
        database_url=SecretStr("postgres://user:pass@db.example.supabase.co:5432/postgres"),
    )
    resolved = resolve_database_url(pg_settings)
    assert resolved == "postgresql+psycopg://user:pass@db.example.supabase.co:5432/postgres"
    assert not is_sqlite_url(resolved)

    pg_settings_2 = make_settings(
        tmp_path,
        database_url=SecretStr("postgresql://user:pass@db.example.supabase.co:5432/postgres"),
    )
    assert (
        resolve_database_url(pg_settings_2)
        == "postgresql+psycopg://user:pass@db.example.supabase.co:5432/postgres"
    )


def test_build_storage_selects_supabase_when_configured(tmp_path):
    local = build_storage(make_settings(tmp_path))
    assert isinstance(local, LocalDiskStorage)

    remote = build_storage(
        make_settings(
            tmp_path,
            supabase_url="https://example.supabase.co",
            supabase_service_role_key=SecretStr("service-key"),
            supabase_storage_bucket="screenshots",
        )
    )
    assert isinstance(remote, SupabaseStorage)


def test_supabase_storage_round_trip_and_health():
    store: dict[str, bytes] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/storage/v1/bucket/screenshots" and request.method == "GET":
            return httpx.Response(200, json={"name": "screenshots"})
        if request.url.path.startswith("/storage/v1/object/screenshots/"):
            key = request.url.path.removeprefix("/storage/v1/object/screenshots/")
            if request.method == "POST":
                store[key] = request.content
                return httpx.Response(200, json={"Key": f"screenshots/{key}"})
            if request.method == "GET":
                if key not in store:
                    return httpx.Response(404)
                return httpx.Response(200, content=store[key])
            if request.method == "DELETE":
                if key not in store:
                    return httpx.Response(404)
                del store[key]
                return httpx.Response(200)
        return httpx.Response(400)

    storage = SupabaseStorage(
        "https://example.supabase.co",
        "service-key",
        "screenshots",
        transport=httpx.MockTransport(handler),
    )
    item_id = "11111111-1111-1111-1111-111111111111"
    key = storage.put(item_id, b"png-bytes")
    assert key == f"{item_id}.png"
    assert storage.get(key) == b"png-bytes"
    assert storage.is_healthy() is True

    storage.delete(key)
    storage.delete(key)  # idempotent on 404
    with pytest.raises(FileNotFoundError):
        storage.get(key)

    with pytest.raises(ValueError):
        storage.get("../escape.png")
