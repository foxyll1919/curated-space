from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import LLMUsage
from app.services.extraction.base import TokenUsage


def estimate_cost_usd(settings: Settings, model: str, usage: TokenUsage) -> float:
    """Estimate cost from a config price table.

    This is an estimate, not a bill. The price table is unverified against the
    official pricing page and Milestone 6 replaces it with a checked-in table
    that records when it was verified.
    """
    del model  # Pricing is currently flat across the flash family we use.
    cost = (
        usage.prompt_tokens * settings.gemini_input_price_usd_per_mtok
        + usage.output_tokens * settings.gemini_output_price_usd_per_mtok
        + usage.thinking_tokens * settings.gemini_thinking_price_usd_per_mtok
    ) / 1_000_000
    return round(cost, 8)


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
