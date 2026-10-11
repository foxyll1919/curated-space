"""Shared fixtures: temporary database, storage, settings and a fake extractor."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from PIL import Image

from app.core.config import Settings
from app.main import create_app
from app.services.extraction.base import ExtractionResult, ModelInput
from app.services.extraction.prompts import PROMPT_VERSION
from app.services.extraction.schema import SCHEMA_VERSION, ExtractedMetadata


BACKEND_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def migration_config(database_path: Path) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_path"] = database_path
    return config


def make_settings(tmp_path: Path, **overrides: object) -> Settings:
    settings = Settings(
        database_path=tmp_path / "db" / "test.db",
        storage_path=tmp_path / "uploads",
        gemini_api_key=None,
    )
    return settings.model_copy(update=overrides)


class FakeExtractor:
    """Stands in for Gemini. Records calls so tests can assert on behaviour."""

    def __init__(self, metadata: ExtractedMetadata | None = None) -> None:
        self.metadata = metadata or ExtractedMetadata(
            title="Fake title",
            description="Fake description",
            tags=["alpha", "beta"],
        )
        self.calls: list[ModelInput] = []
        self.error: Exception | None = None
        self.is_configured = True

    def extract(self, image: ModelInput) -> ExtractionResult:
        self.calls.append(image)
        if self.error is not None:
            raise self.error
        return ExtractionResult(
            metadata=self.metadata,
            model="fake-model",
            prompt_version=PROMPT_VERSION,
            schema_version=SCHEMA_VERSION,
            latency_ms=1,
        )


@pytest.fixture
def migrated_settings(tmp_path: Path) -> Settings:
    settings = make_settings(tmp_path)
    # Alembic's engine does not create the parent directory; the app does.
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    command.upgrade(migration_config(settings.database_path), "head")
    return settings


@pytest.fixture
def extractor() -> FakeExtractor:
    return FakeExtractor()


@pytest.fixture
def client(migrated_settings: Settings, extractor: FakeExtractor):
    from fastapi.testclient import TestClient

    app = create_app(migrated_settings, extractor=extractor)
    with TestClient(app) as test_client:
        yield test_client


def make_image(
    width: int = 64,
    height: int = 48,
    image_format: str = "PNG",
    **save_kwargs: object,
) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (10, 20, 30)).save(buffer, format=image_format, **save_kwargs)
    return buffer.getvalue()
