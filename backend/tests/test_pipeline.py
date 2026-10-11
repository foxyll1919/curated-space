"""`process_item` behaviour: idempotency, failure mapping and telemetry."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.core.errors import ExtractionError
from app.db.models import Item, LLMUsage
from app.main import create_app
from app.services.extraction.base import ModelInput
from app.services.pipeline import PipelineContext, process_item
from app.services.storage import LocalDiskStorage
from tests.conftest import FakeExtractor, make_image


def _context(settings: Settings, extractor: FakeExtractor) -> PipelineContext:
    return PipelineContext(
        settings=settings,
        extractor=extractor,
        storage=LocalDiskStorage(settings.storage_path),
        session_factory=create_app(settings, extractor=extractor).state.session_factory,
    )


def _create_ready_item(settings: Settings, extractor: FakeExtractor) -> str:
    context = _context(settings, extractor)
    key = context.storage.put("11111111-1111-1111-1111-111111111111", make_image())
    with context.session_factory() as session:
        session.add(
            Item(
                id="11111111-1111-1111-1111-111111111111",
                owner_id=None,
                status="pending",
                image_key=key,
                content_sha256="hash",
                mime="image/png",
                width=64,
                height=48,
                byte_size=10,
            )
        )
        session.commit()
    return context


def test_process_item_reaches_ready(migrated_settings, extractor):
    context = _create_ready_item(migrated_settings, extractor)
    process_item("11111111-1111-1111-1111-111111111111", context)

    with context.session_factory() as session:
        item = session.get(Item, "11111111-1111-1111-1111-111111111111")
        assert item.status == "ready"
        assert item.title == "Fake title"
        assert item.analyzed_at is not None
        assert item.error_code is None


def test_process_item_is_idempotent(migrated_settings, extractor):
    context = _create_ready_item(migrated_settings, extractor)
    item_id = "11111111-1111-1111-1111-111111111111"

    process_item(item_id, context)
    with context.session_factory() as session:
        first = session.get(Item, item_id).analyzed_at

    process_item(item_id, context)

    with context.session_factory() as session:
        item = session.get(Item, item_id)
        usages = list(session.scalars(select(LLMUsage)))
    assert item.analyzed_at == first
    assert item.status == "ready"
    assert len(extractor.calls) == 1, "a ready item must not be re-billed"
    assert len(usages) == 1


def test_process_item_maps_extraction_error_to_failed(migrated_settings, extractor):
    context = _create_ready_item(migrated_settings, extractor)
    extractor.error = ExtractionError("extraction_truncated")

    process_item("11111111-1111-1111-1111-111111111111", context)

    with context.session_factory() as session:
        item = session.get(Item, "11111111-1111-1111-1111-111111111111")
    assert item.status == "failed"
    assert item.error_code == "extraction_truncated"
    assert item.title is None


def test_process_item_ignores_unknown_item(migrated_settings, extractor):
    context = _context(migrated_settings, extractor)
    process_item("00000000-0000-0000-0000-000000000000", context)
    assert extractor.calls == []


def test_reprocessing_after_failure_clears_the_error(migrated_settings, extractor):
    context = _create_ready_item(migrated_settings, extractor)
    item_id = "11111111-1111-1111-1111-111111111111"
    extractor.error = ExtractionError("extraction_blocked")
    process_item(item_id, context)

    extractor.error = None
    process_item(item_id, context)

    with context.session_factory() as session:
        item = session.get(Item, item_id)
    assert item.status == "ready"
    assert item.error_code is None


@pytest.mark.parametrize(
    "finish_reason,expected",
    [
        ("SAFETY", "extraction_blocked"),
        ("MAX_TOKENS", "extraction_truncated"),
    ],
)
def test_blocked_and_truncated_responses_map_to_error_codes(
    migrated_settings, extractor, finish_reason, expected
):
    from google.genai import types

    from app.services.extraction.gemini import GeminiExtractor

    class StubResponse:
        prompt_feedback = None
        parsed = None
        usage_metadata = None

        def __init__(self) -> None:
            self.candidates = [types.Candidate(finish_reason=types.FinishReason(finish_reason))]

    class StubGemini(GeminiExtractor):
        def _generate(self, image):
            return StubResponse()

    error = None
    try:
        StubGemini(migrated_settings).extract(ModelInput(data=make_image(), mime="image/png"))
    except ExtractionError as exc:
        error = exc.code
    assert error == expected
