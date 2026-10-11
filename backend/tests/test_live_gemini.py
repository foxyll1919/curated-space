"""Real-key Gemini checks.

Skipped unless `GEMINI_API_KEY` is present, so CI stays offline and free. The
committed fixture is a non-sensitive developer screenshot: the configured AI
Studio project is on the Free plan and must not receive sensitive images.
See `readme.md`, "Gemini data handling status", and build brief section 7a.
"""

from __future__ import annotations

import io

import pytest

from app.core.config import Settings
from app.main import create_app
from app.services.extraction.gemini import GeminiExtractor
from tests.conftest import FIXTURES_DIR, make_settings


LIVE_SCREENSHOT = FIXTURES_DIR / "test_image.jpg"


def _live_settings(tmp_path) -> Settings:
    base = Settings()
    if base.gemini_api_key is None or not base.gemini_api_key.get_secret_value().strip():
        pytest.skip("GEMINI_API_KEY is not configured")
    return make_settings(tmp_path, gemini_api_key=base.gemini_api_key)


@pytest.mark.live
def test_live_extraction_returns_validated_metadata(tmp_path):
    settings = _live_settings(tmp_path)
    from app.services.extraction.base import ModelInput

    image = ModelInput(data=LIVE_SCREENSHOT.read_bytes(), mime="image/jpeg")
    result = GeminiExtractor(settings).extract(image)

    assert 1 <= len(result.metadata.title) <= 80
    assert 1 <= len(result.metadata.description) <= 280
    assert len(result.metadata.tags) <= 8
    assert result.usage.prompt_tokens > 0


@pytest.mark.live
def test_live_upload_reaches_ready(tmp_path):
    from fastapi.testclient import TestClient

    from alembic import command

    from tests.conftest import migration_config

    settings = _live_settings(tmp_path)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    command.upgrade(migration_config(settings.database_path), "head")

    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/items",
            files={"file": ("shot.jpg", io.BytesIO(LIVE_SCREENSHOT.read_bytes()), "image/jpeg")},
        )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "ready", body
    assert body["title"]
    assert body["prompt_version"] == "prompt-v1"
