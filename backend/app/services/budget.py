"""Budget guard (brief section 7.8).

Two independent ceilings, both read from `llm_usage` so they are measured rather
than assumed:

* `daily_cost_cap_usd` - sum of today's estimated cost.
* `max_analyses_per_minute` - provider calls started in the last 60 seconds.

Both are checked only on a cache miss: a cached answer costs nothing, so
blocking it would degrade the service for no reason. A blocked item is stored as
`deferred` and is never dropped, so a re-analyze endpoint or the Milestone 8
sweep can pick it up later.

These are estimates from an unverified price table. Treat the daily cap as a
coarse brake, not as an accounting system.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import LLMUsage
from app.services.analysis_cache import CACHE_HIT_STATUS


BUDGET_EXCEEDED = "budget_exceeded"
RATE_LIMITED = "rate_limited"

_RATE_WINDOW = timedelta(minutes=1)


@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    error_code: str | None = None
    spent_today_usd: float = 0.0
    calls_last_minute: int = 0


def evaluate_budget(
    session: Session, settings: Settings, *, now: datetime | None = None
) -> BudgetDecision:
    """Decide whether one provider call may be made right now."""
    moment = now or datetime.now(UTC)
    day_start = moment.replace(hour=0, minute=0, second=0, microsecond=0)

    spent_today = _sum_cost(session, since=day_start)
    recent = _count_calls(session, since=moment - _RATE_WINDOW)

    # Rate first: it is the cheaper, tighter constraint to enforce.
    if settings.max_analyses_per_minute > 0 and recent >= settings.max_analyses_per_minute:
        return BudgetDecision(
            allowed=False,
            error_code=RATE_LIMITED,
            spent_today_usd=spent_today,
            calls_last_minute=recent,
        )
    if settings.daily_cost_cap_usd > 0 and spent_today >= settings.daily_cost_cap_usd:
        return BudgetDecision(
            allowed=False,
            error_code=BUDGET_EXCEEDED,
            spent_today_usd=spent_today,
            calls_last_minute=recent,
        )
    return BudgetDecision(
        allowed=True,
        spent_today_usd=spent_today,
        calls_last_minute=recent,
    )


def _sum_cost(session: Session, *, since: datetime) -> float:
    total = session.scalar(
        select(func.coalesce(func.sum(LLMUsage.estimated_cost_usd), 0.0)).where(
            LLMUsage.created_at >= since,
            LLMUsage.status != CACHE_HIT_STATUS,
        )
    )
    return float(total or 0.0)


def _count_calls(session: Session, *, since: datetime) -> int:
    """Count provider calls, including failed ones.

    A cache hit made no API call, so it does not consume rate budget. A failed
    call did, and its tokens are still billed, so it counts.
    """
    count = session.scalar(
        select(func.count(LLMUsage.id)).where(
            LLMUsage.created_at >= since,
            LLMUsage.status != CACHE_HIT_STATUS,
        )
    )
    return int(count or 0)
