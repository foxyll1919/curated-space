from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.usage import UsageBucket


class UsageWindow(BaseModel):
    """Counts, tokens and estimated cost for one window. Carries no content."""

    calls: int
    provider_calls: int
    cache_hits: int
    failed_calls: int
    prompt_tokens: int
    output_tokens: int
    thinking_tokens: int
    est_cost_usd: float
    cache_hit_rate: float
    #: Models in this window with no entry in the price table. Their calls were
    #: stored at zero cost, so the estimate above understates the real bill by
    #: whatever they cost. Empty means every model in the window is priced.
    unknown_cost_models: list[str] = Field(default_factory=list)

    @classmethod
    def from_bucket(cls, bucket: UsageBucket) -> "UsageWindow":
        return cls(
            calls=bucket.calls,
            provider_calls=bucket.provider_calls,
            cache_hits=bucket.cache_hits,
            failed_calls=bucket.failed_calls,
            prompt_tokens=bucket.prompt_tokens,
            output_tokens=bucket.output_tokens,
            thinking_tokens=bucket.thinking_tokens,
            est_cost_usd=bucket.est_cost_usd,
            cache_hit_rate=bucket.cache_hit_rate,
            unknown_cost_models=list(bucket.unknown_cost_models),
        )


class UsageResponse(BaseModel):
    today: UsageWindow
    last_7_days: UsageWindow
