from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.pricing import estimate_cost_usd as price_from_table, load_pricing_table
from app.db.models import LLMUsage
from app.services.analysis_cache import CACHE_HIT_STATUS
from app.services.extraction.base import TokenUsage


#: A call that reached the provider. `cache_hit` rows cost nothing and carry no
#: tokens, so they are counted separately and never folded into these totals.
PROVIDER_STATUSES = ("ok",)


def estimate_cost_usd(settings: Settings, model: str, usage: TokenUsage) -> float:
    """Estimated cost from the checked-in price table.

    An unpriced model records 0.0 rather than raising: one unknown price must not
    break an upload. The consequence is that the running total silently excludes
    that model, so `unknown_cost_models` on the usage summary is what makes the
    gap visible instead of hiding it as a smaller bill.
    """
    del settings  # Pricing is a table lookup keyed by model, not a setting.
    # Google bills thinking tokens at the output rate and the output figure
    # already says "including thinking tokens", so the two are summed and billed
    # once. Charging the thinking tokens a second time was the old behaviour.
    cost = price_from_table(
        model,
        prompt_tokens=usage.prompt_tokens,
        output_tokens=usage.output_tokens + usage.thinking_tokens,
    )
    return cost if cost is not None else 0.0


def record_usage(
    session: Session,
    *,
    item_id: str | None,
    settings: Settings,
    model: str,
    usage: TokenUsage,
    latency_ms: int,
    status: str,
) -> None:
    """Persist token counts, latency and cost estimate. Carries no user content."""
    session.add(
        LLMUsage(
            item_id=item_id,
            model=model,
            prompt_tokens=usage.prompt_tokens,
            output_tokens=usage.output_tokens,
            thinking_tokens=usage.thinking_tokens,
            latency_ms=latency_ms,
            status=status,
            estimated_cost_usd=estimate_cost_usd(settings, model, usage),
        )
    )


def record_cache_hit(
    session: Session, *, item_id: str | None, settings: Settings, model: str
) -> None:
    """Record a zero-cost row so cache hit rate is measurable.

    The row is the evidence that no API call happened. The budget guard treats
    it as free, and the usage summary divides by it to report the hit rate.
    """
    del settings
    session.add(
        LLMUsage(
            item_id=item_id,
            model=model,
            prompt_tokens=0,
            output_tokens=0,
            thinking_tokens=0,
            latency_ms=0,
            status=CACHE_HIT_STATUS,
            estimated_cost_usd=0.0,
        )
    )


@dataclass(frozen=True)
class UsageBucket:
    """One window of `llm_usage`. Counts and totals only, never content."""

    calls: int
    provider_calls: int
    cache_hits: int
    failed_calls: int
    prompt_tokens: int
    output_tokens: int
    thinking_tokens: int
    est_cost_usd: float
    cache_hit_rate: float
    unknown_cost_models: tuple[str, ...] = ()

    @classmethod
    def empty(cls) -> "UsageBucket":
        return cls(0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, ())


def summarize_usage(session: Session, *, since: datetime) -> UsageBucket:
    """Aggregate `llm_usage` rows created at or after `since`."""
    rows = list(session.scalars(select(LLMUsage).where(LLMUsage.created_at >= since)))
    if not rows:
        return UsageBucket.empty()

    cache_hits = sum(1 for row in rows if row.status == CACHE_HIT_STATUS)
    provider_calls = len(rows) - cache_hits
    failed_calls = sum(
        1 for row in rows if row.status != CACHE_HIT_STATUS and row.status not in PROVIDER_STATUSES
    )
    denominator = cache_hits + provider_calls
    return UsageBucket(
        calls=len(rows),
        provider_calls=provider_calls,
        cache_hits=cache_hits,
        failed_calls=failed_calls,
        prompt_tokens=sum(row.prompt_tokens for row in rows),
        output_tokens=sum(row.output_tokens for row in rows),
        thinking_tokens=sum(row.thinking_tokens for row in rows),
        est_cost_usd=round(sum(row.estimated_cost_usd or 0.0 for row in rows), 8),
        cache_hit_rate=round(cache_hits / denominator, 4) if denominator else 0.0,
        unknown_cost_models=_unknown_cost_models(rows),
    )


def _unknown_cost_models(rows: Sequence[LLMUsage]) -> tuple[str, ...]:
    """Models whose calls contributed a zero estimate for lack of a price.

    ``record_usage`` stores 0.0 rather than failing for an unpriced model, so
    this list is the only way a reader can tell "free" from "not priced".
    """
    priced = load_pricing_table().models
    return tuple(sorted({row.model for row in rows if row.model not in priced and row.model}))


def usage_windows(now: datetime | None = None) -> dict[str, datetime]:
    """The `since` bounds the `/usage` endpoint reports on."""
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    return {
        "today": moment.replace(hour=0, minute=0, second=0, microsecond=0),
        "last_7_days": moment - timedelta(days=7),
    }
