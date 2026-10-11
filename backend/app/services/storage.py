from __future__ import annotations

from pathlib import Path
from typing import Protocol
from uuid import UUID


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


def storage_key(item_id: str) -> str:
    """Derive an opaque, collision-free storage name from the item id."""
    return f"{UUID(item_id)}.png"
