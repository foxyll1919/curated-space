from __future__ import annotations

from pathlib import Path
from typing import Protocol
from uuid import UUID

import httpx

from app.core.config import Settings


class Storage(Protocol):
    def put(self, item_id: str, data: bytes) -> str: ...

    def get(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...


class LocalDiskStorage:
    """Local-disk implementation behind the Storage interface.

    Keys are generated, opaque identifiers. A caller-supplied filename is never
    joined to a path, and nothing returned here is ever exposed over the API.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def _resolve(self, key: str) -> Path:
        # Defence in depth: reject anything that is not a bare generated name.
        if not key or Path(key).name != key:
            raise ValueError("invalid storage key")
        return self._root / key

    def put(self, item_id: str, data: bytes) -> str:
        self._root.mkdir(parents=True, exist_ok=True)
        key = storage_key(item_id)
        self._resolve(key).write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def delete(self, key: str) -> None:
        self._resolve(key).unlink(missing_ok=True)


class SupabaseStorage:
    """Supabase Storage implementation behind the Storage interface."""

    def __init__(
        self,
        base_url: str,
        service_role_key: str,
        bucket: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._bucket = bucket
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {service_role_key}",
                "apikey": service_role_key,
            },
            timeout=30.0,
            transport=transport,
        )

    def _validate_key(self, key: str) -> str:
        if not key or Path(key).name != key:
            raise ValueError("invalid storage key")
        return key

    def _object_url(self, key: str) -> str:
        safe_key = self._validate_key(key)
        return f"{self._base_url}/storage/v1/object/{self._bucket}/{safe_key}"

    def put(self, item_id: str, data: bytes) -> str:
        key = storage_key(item_id)
        response = self._client.post(
            self._object_url(key),
            content=data,
            headers={"Content-Type": "image/png", "x-upsert": "true"},
        )
        response.raise_for_status()
        return key

    def get(self, key: str) -> bytes:
        response = self._client.get(self._object_url(key))
        if response.status_code == 404:
            raise FileNotFoundError(key)
        response.raise_for_status()
        return response.content

    def delete(self, key: str) -> None:
        response = self._client.delete(self._object_url(key))
        if response.status_code == 404:
            return
        response.raise_for_status()

    def is_healthy(self) -> bool:
        response = self._client.get(f"{self._base_url}/storage/v1/bucket/{self._bucket}")
        return response.status_code == 200


def build_storage(settings: Settings) -> Storage:
    if settings.supabase_url and settings.supabase_service_role_key:
        url = settings.supabase_url.strip()
        key = settings.supabase_service_role_key.get_secret_value().strip()
        if url and key:
            return SupabaseStorage(url, key, settings.supabase_storage_bucket)
    return LocalDiskStorage(settings.storage_path)


def storage_key(item_id: str) -> str:
    """Derive an opaque, collision-free storage name from the item id."""
    return f"{UUID(item_id)}.png"
