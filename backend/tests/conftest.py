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
from app.services.classification.base import Prediction
from app.services.extraction.base import CacheIdentity, ExtractionResult, ModelInput
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
        api_key="test-api-key",
        # PBKDF2 at 600k iterations would dominate the suite's runtime; the
        # cost of a slow hash is a security property these tests do not check.
        password_hash_iterations=1_000,
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
        self.cache_identity = CacheIdentity(
            model="fake-model", prompt_version=PROMPT_VERSION, schema_version=SCHEMA_VERSION
        )

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


class FakeClassifier:
    """Stands in for the sklearn adapter. Records calls for assertions."""

    is_ready = True

    def __init__(
        self,
        prediction: Prediction | None = None,
        *,
        ready: bool = True,
        error: Exception | None = None,
    ) -> None:
        self.prediction = prediction or Prediction(
            labels={"category": "Tutorials"},
            score=1.25,
            abstained=False,
            model_version="fake-model",
            taxonomy_version="legacy-8",
        )
        self.calls: list[str] = []
        self.error = error
        if not ready:
            self.is_ready = False

    @property
    def status(self):
        from app.services.classification.sklearn_svc import ClassifierStatus

        return ClassifierStatus("ok" if self.is_ready else "unavailable")

    @property
    def taxonomy_version(self):
        return self.prediction.taxonomy_version if self.is_ready else None

    @property
    def model_version(self):
        return self.prediction.model_version if self.is_ready else None

    def predict(self, text: str) -> Prediction:
        self.calls.append(text)
        if self.error is not None:
            raise self.error
        return self.prediction


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
def classifier() -> FakeClassifier:
    return FakeClassifier()


@pytest.fixture
def client(migrated_settings: Settings, extractor: FakeExtractor, classifier: FakeClassifier):
    from fastapi.testclient import TestClient

    app = create_app(migrated_settings, extractor=extractor, classifier=classifier)
    with TestClient(app, headers={"X-API-Key": "test-api-key"}) as test_client:
        yield test_client


@pytest.fixture
def make_client(extractor: FakeExtractor, classifier: FakeClassifier):
    """Build a client with custom settings. No API key header is attached."""
    from fastapi.testclient import TestClient

    created: list[TestClient] = []

    def factory(settings: Settings) -> TestClient:
        app = create_app(settings, extractor=extractor, classifier=classifier)
        test_client = TestClient(app)
        created.append(test_client)
        return test_client

    yield factory
    for test_client in created:
        test_client.close()


@pytest.fixture
def auth_settings(migrated_settings: Settings) -> Settings:
    """Settings with no API key, so only a session cookie can authenticate."""
    return migrated_settings.model_copy(update={"api_key": None})


def make_image(
    width: int = 64,
    height: int = 48,
    image_format: str = "PNG",
    **save_kwargs: object,
) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (10, 20, 30)).save(buffer, format=image_format, **save_kwargs)
    return buffer.getvalue()
