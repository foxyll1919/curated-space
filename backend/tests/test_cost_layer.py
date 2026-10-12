"""Milestone 5 cost layer: cache, budget guard, retries and usage telemetry."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.core.errors import ExtractionError
from app.db.models import AnalysisCache, Item, LLMUsage
from app.services.analysis_cache import CacheIdentity, cache_key, lookup
from app.services.budget import BUDGET_EXCEEDED, RATE_LIMITED, evaluate_budget
from app.services.extraction.base import CacheIdentity as BaseCacheIdentity
from app.services.extraction.base import ModelInput, TokenUsage
from app.services.extraction.gemini import GeminiExtractor
from app.services.usage import record_usage, summarize_usage
from app.services.pipeline import process_item
from tests.conftest import make_image
from tests.test_pipeline import ITEM_ID, _create_ready_item


# --------------------------------------------------------------------------
# Pixel-hash cache: a hit must cost zero API calls
# --------------------------------------------------------------------------


def test_second_identical_item_makes_no_provider_call(migrated_settings, extractor):
    first = _create_ready_item(migrated_settings, extractor)
    process_item(ITEM_ID, first)

    second_id = "22222222-2222-2222-2222-222222222222"
    key = first.storage.put(second_id, make_image())
    with first.session_factory() as session:
        session.add(
            Item(
                id=second_id,
                owner_id=None,
                status="pending",
                image_key=key,
                # Same pixel hash: the image bytes are identical.
                content_sha256="hash",
                mime="image/png",
                width=64,
                height=48,
                byte_size=10,
            )
        )
        session.commit()

    process_item(second_id, first)

    with first.session_factory() as session:
        item = session.get(Item, second_id)
        usages = list(session.scalars(select(LLMUsage)))
    assert item.status == "ready"
    assert item.title == "Fake title"
    assert len(extractor.calls) == 1, "the cached item must not re-bill"
    assert [row.status for row in usages] == ["ok", "cache_hit"]


def test_cache_miss_when_versions_change(migrated_settings, extractor):
    context = _create_ready_item(migrated_settings, extractor)
    process_item(ITEM_ID, context)

    # Same pixels, new prompt version: a different key, so a real call.
    extractor.cache_identity = BaseCacheIdentity(
        model="fake-model", prompt_version="metadata-v2", schema_version="metadata-v1"
    )
    other_id = "33333333-3333-3333-3333-333333333333"
    key = context.storage.put(other_id, make_image())
    with context.session_factory() as session:
        session.add(
            Item(
                id=other_id,
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

    process_item(other_id, context)
    assert len(extractor.calls) == 2


def test_cache_key_covers_every_version():
    base = CacheIdentity(model="m", prompt_version="p", schema_version="s")
    assert cache_key("h", base) == "h|m|p|s"
    assert cache_key("h", base) != cache_key("other", base)
    assert cache_key("h", base) != cache_key(
        "h", CacheIdentity(model="m2", prompt_version="p", schema_version="s")
    )
    assert cache_key("h", base) != cache_key(
        "h", CacheIdentity(model="m", prompt_version="p2", schema_version="s")
    )
    assert cache_key("h", base) != cache_key(
        "h", CacheIdentity(model="m", prompt_version="p", schema_version="s2")
    )


def test_disabled_cache_always_calls_the_provider(migrated_settings, extractor):
    settings = migrated_settings.model_copy(update={"analysis_cache_enabled": False})
    context = _create_ready_item(settings, extractor)
    process_item(ITEM_ID, context)

    other_id = "44444444-4444-4444-4444-444444444444"
    key = context.storage.put(other_id, make_image())
    with context.session_factory() as session:
        session.add(
            Item(
                id=other_id,
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

    process_item(other_id, context)
    assert len(extractor.calls) == 2


def test_unusable_cache_row_is_a_miss_not_a_failure(migrated_settings, extractor):
    """A row we cannot validate must fall back to the provider, not fail."""
    identity = CacheIdentity(model="fake-model", prompt_version="p", schema_version="s")
    context = _create_ready_item(migrated_settings, extractor)
    with context.session_factory() as session:
        session.add(AnalysisCache(key=cache_key("hash", identity), value={"title": ""}))
        session.commit()

    process_item(ITEM_ID, context)

    with context.session_factory() as session:
        item = session.get(Item, ITEM_ID)
    assert item.status == "ready"
    assert item.title == "Fake title"
    assert len(extractor.calls) == 1


def test_lookup_returns_none_for_an_absent_key(migrated_settings, extractor):
    context = _create_ready_item(migrated_settings, extractor)
    with context.session_factory() as session:
        assert lookup(session, "not-a-key") is None


# --------------------------------------------------------------------------
# Budget guard
# --------------------------------------------------------------------------


def _seed_usage(context, *, cost: float, minutes_ago: int = 0, status: str = "ok") -> None:
    with context.session_factory() as session:
        row = LLMUsage(
            item_id=None,
            model="fake-model",
            prompt_tokens=100,
            output_tokens=10,
            thinking_tokens=0,
            latency_ms=5,
            status=status,
            estimated_cost_usd=cost,
        )
        row.created_at = datetime.now(UTC) - timedelta(minutes=minutes_ago)
        session.add(row)
        session.commit()


def test_budget_allows_a_fresh_daily_budget(migrated_settings, extractor):
    context = _create_ready_item(migrated_settings, extractor)
    with context.session_factory() as session:
        decision = evaluate_budget(session, context.settings)
    assert decision.allowed is True


def test_daily_cap_defers_the_item(migrated_settings, extractor):
    settings = migrated_settings.model_copy(update={"daily_cost_cap_usd": 0.10})
    context = _create_ready_item(settings, extractor)
    _seed_usage(context, cost=0.10)

    process_item(ITEM_ID, context)

    with context.session_factory() as session:
        item = session.get(Item, ITEM_ID)
    assert item.status == "deferred"
    assert item.error_code == BUDGET_EXCEEDED
    assert item.title is None
    assert extractor.calls == [], "a deferred item must not call the provider"


def test_rate_limit_defers_the_item(migrated_settings, extractor):
    settings = migrated_settings.model_copy(update={"max_analyses_per_minute": 2})
    context = _create_ready_item(settings, extractor)
    _seed_usage(context, cost=0.0)
    _seed_usage(context, cost=0.0)

    process_item(ITEM_ID, context)

    with context.session_factory() as session:
        item = session.get(Item, ITEM_ID)
    assert item.status == "deferred"
    assert item.error_code == RATE_LIMITED


def test_cache_hits_do_not_consume_rate_budget(migrated_settings, extractor):
    settings = migrated_settings.model_copy(update={"max_analyses_per_minute": 1})
    context = _create_ready_item(settings, extractor)
    _seed_usage(context, cost=0.0, status="cache_hit")

    process_item(ITEM_ID, context)

    with context.session_factory() as session:
        item = session.get(Item, ITEM_ID)
    assert item.status == "ready"
    assert len(extractor.calls) == 1


def test_zero_caps_disable_the_guard(migrated_settings, extractor):
    settings = migrated_settings.model_copy(
        update={"daily_cost_cap_usd": 0.0, "max_analyses_per_minute": 0}
    )
    context = _create_ready_item(settings, extractor)
    _seed_usage(context, cost=99.0)

    with context.session_factory() as session:
        decision = evaluate_budget(session, context.settings)
    assert decision.allowed is True


def test_yesterday_spend_does_not_count_towards_today(migrated_settings, extractor):
    context = _create_ready_item(migrated_settings, extractor)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    with context.session_factory() as session:
        row = LLMUsage(
            item_id=None,
            model="fake-model",
            prompt_tokens=1,
            output_tokens=1,
            thinking_tokens=0,
            latency_ms=1,
            status="ok",
            estimated_cost_usd=50.0,
        )
        row.created_at = yesterday.replace(hour=12, minute=0, second=0, microsecond=0)
        session.add(row)
        session.commit()

    with context.session_factory() as session:
        decision = evaluate_budget(session, context.settings)
    assert decision.allowed is True


def test_cache_hit_still_serves_under_a_budget_block(migrated_settings, extractor):
    """The guard protects spend, not correctness: a cached answer is free."""
    context = _create_ready_item(migrated_settings, extractor)
    process_item(ITEM_ID, context)

    capped = context.settings.model_copy(update={"daily_cost_cap_usd": 0.0})
    context.settings = capped
    other_id = "55555555-5555-5555-5555-555555555555"
    key = context.storage.put(other_id, make_image())
    with context.session_factory() as session:
        session.add(
            Item(
                id=other_id,
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

    # Cap exhausted by the first call.
    _seed_usage(context, cost=5.0)
    process_item(other_id, context)

    with context.session_factory() as session:
        item = session.get(Item, other_id)
    assert item.status == "ready"
    assert len(extractor.calls) == 1


# --------------------------------------------------------------------------
# Retry policy
# --------------------------------------------------------------------------


class _CountingExtractor(GeminiExtractor):
    """Stubbed transport that raises a scripted sequence, then succeeds."""

    def __init__(self, settings: Settings, outcomes: list[object]) -> None:
        super().__init__(settings)
        self.outcomes = list(outcomes)
        self.attempts = 0

    def _generate(self, image):  # type: ignore[no-untyped-def]
        self.attempts += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _response(parsed):
    """A response shaped like the SDK's, with a pre-parsed `parsed` object.

    The real SDK builds `parsed` from `response_schema`, so it is already an
    `ExtractedMetadata`; a stub returning a raw dict would test nothing real.
    """
    from google.genai import types

    class StubResponse:
        prompt_feedback = None
        usage_metadata = types.GenerateContentResponseUsageMetadata(
            prompt_token_count=10, candidates_token_count=5, total_token_count=15
        )
        candidates = [types.Candidate(finish_reason=types.FinishReason.STOP)]

        def __init__(self) -> None:
            self.parsed = parsed

    return StubResponse()


def _good_response():
    from app.services.extraction.schema import ExtractedMetadata

    return _response(
        ExtractedMetadata(title="T", description="D", tags=["ab"]),
    )


def _unusable_response():
    """Whitespace-only title: valid per the schema, empty after sanitizing.

    This is the realistic failure the repair retry exists for, and it is not
    reachable by constructing `ExtractedMetadata` normally.
    """
    from app.services.extraction.schema import ExtractedMetadata

    return _response(ExtractedMetadata.model_construct(title="   ", description="D", tags=[]))


def _rate_limited():
    from google.genai import errors as genai_errors

    return genai_errors.ClientError(429, {"error": {"code": 429, "message": "slow down"}})


def _server_error():
    from google.genai import errors as genai_errors

    return genai_errors.ServerError(503, {"error": {"code": 503, "message": "unavailable"}})


def test_429_then_success_is_retried(migrated_settings):
    extractor = _CountingExtractor(
        migrated_settings.model_copy(update={"gemini_retry_base_delay_ms": 1}),
        [_rate_limited(), _good_response()],
    )
    result = extractor.extract(ModelInput(data=make_image(), mime="image/png"))
    assert result.metadata.title == "T"
    assert extractor.attempts == 2


def test_retries_are_bounded(migrated_settings):
    extractor = _CountingExtractor(
        migrated_settings.model_copy(
            update={"gemini_retry_base_delay_ms": 1, "gemini_max_retries": 2}
        ),
        [_rate_limited(), _rate_limited(), _rate_limited(), _good_response()],
    )
    with pytest.raises(ExtractionError) as excinfo:
        extractor.extract(ModelInput(data=make_image(), mime="image/png"))
    assert excinfo.value.code == "extraction_provider_error"
    assert extractor.attempts == 3, "one initial call plus at most two retries"


def test_server_errors_are_retried(migrated_settings):
    extractor = _CountingExtractor(
        migrated_settings.model_copy(update={"gemini_retry_base_delay_ms": 1}),
        [_server_error(), _good_response()],
    )
    extractor.extract(ModelInput(data=make_image(), mime="image/png"))
    assert extractor.attempts == 2


def test_400_is_not_retried(migrated_settings):
    from google.genai import errors as genai_errors

    extractor = _CountingExtractor(
        migrated_settings.model_copy(update={"gemini_retry_base_delay_ms": 1}),
        [
            genai_errors.ClientError(400, {"error": {"code": 400, "message": "bad"}}),
            _good_response(),
        ],
    )
    with pytest.raises(ExtractionError):
        extractor.extract(ModelInput(data=make_image(), mime="image/png"))
    assert extractor.attempts == 1, "a malformed request will fail the same way forever"


def test_timeout_is_retried(migrated_settings):
    import httpx

    extractor = _CountingExtractor(
        migrated_settings.model_copy(update={"gemini_retry_base_delay_ms": 1}),
        [httpx.ReadTimeout("slow"), _good_response()],
    )
    extractor.extract(ModelInput(data=make_image(), mime="image/png"))
    assert extractor.attempts == 2


def test_schema_failure_gets_exactly_one_repair(migrated_settings):
    extractor = _CountingExtractor(
        migrated_settings, [_unusable_response(), _unusable_response(), _good_response()]
    )
    with pytest.raises(ExtractionError) as excinfo:
        extractor.extract(ModelInput(data=make_image(), mime="image/png"))
    assert excinfo.value.code == "extraction_invalid"
    assert extractor.attempts == 2, "one call plus one repair, then a clean failure"


def test_repair_recovers_a_bad_response(migrated_settings):
    extractor = _CountingExtractor(migrated_settings, [_unusable_response(), _good_response()])
    result = extractor.extract(ModelInput(data=make_image(), mime="image/png"))
    assert result.metadata.title == "T"
    assert extractor.attempts == 2


def test_repairs_can_be_disabled(migrated_settings):
    settings = migrated_settings.model_copy(update={"gemini_max_schema_repairs": 0})
    extractor = _CountingExtractor(settings, [_unusable_response(), _good_response()])
    with pytest.raises(ExtractionError) as excinfo:
        extractor.extract(ModelInput(data=make_image(), mime="image/png"))
    assert excinfo.value.code == "extraction_invalid"
    assert extractor.attempts == 1


def test_total_timeout_bounds_the_whole_call(migrated_settings):
    """A backoff must not push the call past the configured total timeout."""
    settings = migrated_settings.model_copy(
        update={
            "gemini_retry_base_delay_ms": 5_000,
            "gemini_total_timeout_ms": 100,
            "gemini_max_retries": 5,
        }
    )
    extractor = _CountingExtractor(settings, [_rate_limited() for _ in range(6)])
    with pytest.raises(ExtractionError):
        extractor.extract(ModelInput(data=make_image(), mime="image/png"))
    assert extractor.attempts == 1, "no backoff sleep may start without budget for it"


# --------------------------------------------------------------------------
# Usage telemetry
# --------------------------------------------------------------------------


def test_usage_endpoint_reports_calls_tokens_and_hit_rate(client):
    response = client.get("/api/v1/usage")
    assert response.status_code == 200
    body = response.json()
    assert body["today"]["calls"] == 0
    assert body["today"]["cache_hit_rate"] == 0.0
    assert body["last_7_days"]["est_cost_usd"] == 0.0


def test_usage_endpoint_counts_a_real_upload(client, migrated_settings):
    upload = client.post("/api/v1/items", files={"file": ("shot.png", make_image(), "image/png")})
    assert upload.status_code == 202

    body = client.get("/api/v1/usage").json()
    assert body["today"]["calls"] == 1
    assert body["today"]["provider_calls"] == 1
    assert body["today"]["cache_hits"] == 0
    assert body["today"]["failed_calls"] == 0
    assert body["today"]["est_cost_usd"] == 0.0, "the fake provider reports no tokens"
    del migrated_settings


def test_usage_endpoint_counts_a_cache_hit(client):
    image = make_image()
    client.post("/api/v1/items", files={"file": ("shot.png", image, "image/png")})
    client.post("/api/v1/items", files={"file": ("shot.png", image, "image/png")})

    body = client.get("/api/v1/usage").json()
    assert body["today"]["calls"] == 2
    assert body["today"]["provider_calls"] == 1
    assert body["today"]["cache_hits"] == 1
    assert body["today"]["cache_hit_rate"] == 0.5


def test_a_blocked_extraction_records_no_cost_row(migrated_settings, extractor):
    """A blocked response returns no `usage_metadata`, so there is nothing to bill.

    This is a real gap, not a win: a request that fails *after* the provider
    generated tokens spends money we cannot see from the error path. Milestone 6
    should reconcile provider-side billing against these rows.
    """
    context = _create_ready_item(migrated_settings, extractor)
    extractor.error = ExtractionError("extraction_blocked")
    process_item(ITEM_ID, context)

    with context.session_factory() as session:
        bucket = summarize_usage(session, since=datetime.now(UTC) - timedelta(minutes=1))
    assert bucket.calls == 0


def test_summarize_usage_separates_failures(migrated_settings, extractor):
    context = _create_ready_item(migrated_settings, extractor)
    with context.session_factory() as session:
        session.add(
            LLMUsage(
                item_id=None,
                model="m",
                prompt_tokens=5,
                output_tokens=5,
                thinking_tokens=0,
                latency_ms=1,
                status="extraction_blocked",
                estimated_cost_usd=0.001,
            )
        )
        session.commit()

    with context.session_factory() as session:
        bucket = summarize_usage(session, since=datetime.now(UTC) - timedelta(minutes=1))
    assert bucket.calls == 1
    assert bucket.failed_calls == 1
    assert bucket.provider_calls == 1


def test_estimate_cost_uses_the_price_table(migrated_settings, extractor):
    """Cost comes from the checked-in table, keyed by model id.

    Milestone 6 replaced the per-setting prices with `gemini_pricing.json`, so
    this now pins the arithmetic against a real row of that table rather than
    against numbers injected into settings.
    """
    context = _create_ready_item(migrated_settings, extractor)
    with context.session_factory() as session:
        record_usage(
            session,
            item_id=None,
            settings=context.settings,
            model="gemini-3.5-flash-lite",
            usage=TokenUsage(prompt_tokens=1_000_000, output_tokens=1_000_000, thinking_tokens=0),
            latency_ms=1,
            status="ok",
        )
        session.commit()
        bucket = summarize_usage(session, since=datetime.now(UTC) - timedelta(minutes=1))
    # $0.30 in / $2.50 out per Mtok, verified 2026-10-11.
    assert bucket.est_cost_usd == pytest.approx(2.80)
    assert bucket.unknown_cost_models == ()


def test_unpriced_model_is_reported_rather_than_silently_free(migrated_settings, extractor):
    """An unknown model costs 0.0 in the total, and says so.

    Without the second assertion this is a bug that hides: the bill would look
    smaller than it is.
    """
    context = _create_ready_item(migrated_settings, extractor)
    with context.session_factory() as session:
        record_usage(
            session,
            item_id=None,
            settings=context.settings,
            model="gemini-not-a-real-model",
            usage=TokenUsage(prompt_tokens=1_000_000, output_tokens=1_000_000),
            latency_ms=1,
            status="ok",
        )
        session.commit()
        bucket = summarize_usage(session, since=datetime.now(UTC) - timedelta(minutes=1))
    assert bucket.est_cost_usd == 0.0
    assert bucket.unknown_cost_models == ("gemini-not-a-real-model",)


def test_extract_result_carries_no_content(migrated_settings, extractor):
    """Telemetry rows must never be a place user text can leak into."""
    context = _create_ready_item(migrated_settings, extractor)
    process_item(ITEM_ID, context)
    with context.session_factory() as session:
        row = session.scalars(select(LLMUsage)).one()
    assert row.status == "ok"
    assert row.item_id == ITEM_ID
    assert "Fake title" not in str(row.__dict__)
