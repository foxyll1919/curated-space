import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import Settings
from app.main import create_app


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _migration_config(database_path: Path) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_path"] = database_path
    return config


def _migrate(database_path: Path) -> None:
    config = _migration_config(database_path)
    command.upgrade(config, "head")


def test_readiness_checks_schema_and_storage(tmp_path):
    database_path = tmp_path / "db" / "test.db"
    storage_path = tmp_path / "uploads"
    app = create_app(Settings(database_path=database_path, storage_path=storage_path))

    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        not_ready = client.get("/api/v1/ready")

        assert health.status_code == 200
        assert health.json() == {"status": "ok"}
        assert not_ready.status_code == 503
        assert not_ready.json()["components"]["database"] == "schema_not_migrated"

        _migrate(database_path)
        ready = client.get("/api/v1/ready")

    assert ready.status_code == 200
    assert ready.json() == {
        "status": "ready",
        "components": {
            "database": "ok",
            "storage": "ok",
            "classifier": "deferred_until_milestone_4",
            "extractor": "ok",
        },
    }
    assert storage_path.is_dir()


def test_migration_preserves_legacy_item_fields(tmp_path):
    database_path = tmp_path / "legacy.db"
    raw = sqlite3.connect(database_path)
    raw.execute(
        """CREATE TABLE items (
            id VARCHAR NOT NULL PRIMARY KEY,
            image_url VARCHAR NOT NULL,
            title VARCHAR,
            description TEXT,
            category VARCHAR,
            tags VARCHAR,
            confidence FLOAT,
            created_at DATETIME
        )"""
    )
    raw.execute(
        """INSERT INTO items
        (id, image_url, title, description, category, tags, confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "item-123",
            r"uploads\item-123.png",
            "Saved title",
            "Saved description",
            "Research",
            "notes, paper",
            0.91,
            "2026-10-10 12:30:00",
        ),
    )
    raw.commit()
    raw.close()

    _migrate(database_path)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.connect() as connection:
        item = (
            connection.execute(text("SELECT * FROM items WHERE id = 'item-123'")).mappings().one()
        )
        tables = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).all()
    engine.dispose()

    assert item["image_key"] == "item-123.png"
    assert item["title"] == "Saved title"
    assert item["description"] == "Saved description"
    assert item["tags"] == '["notes", "paper"]'
    assert item["labels"] == '{"category": "Research"}'
    assert item["status"] == "ready"
    assert item["classifier_score"] is None
    assert {row[0] for row in tables} >= {"items", "analysis_cache", "llm_usage"}
    assert "items_legacy" not in {row[0] for row in tables}

    command.downgrade(_migration_config(database_path), "base")
    restored = sqlite3.connect(database_path)
    old_item = restored.execute(
        "SELECT image_url, category, tags, confidence FROM items WHERE id = ?",
        ("item-123",),
    ).fetchone()
    restored.close()
    assert old_item == ("uploads/item-123.png", "Research", "notes, paper", None)
