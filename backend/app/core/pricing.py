"""Gemini price lookup backed by a checked-in table with provenance.

The price settings that used to live in `Settings` were placeholders copied from
the build brief and never checked against Google. This module reads
`gemini_pricing.json`, which records the date it was verified and the page it
came from, so a stale number is at least visibly stale.

A model missing from the table has **unknown** cost, not zero cost. Guessing a
price would corrupt the budget guard and the `/usage` summary, both of which
treat a missing or wrong figure as a real number, so `price_for` returns None and
callers decide what an unknown price means.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PRICING_TABLE_PATH = Path(__file__).resolve().parent / "gemini_pricing.json"


@dataclass(frozen=True)
class ModelPrice:
    input_usd_per_mtok: float
    output_usd_per_mtok: float
    cached_input_usd_per_mtok: float | None = None
    note: str = ""


@dataclass(frozen=True)
class PricingTable:
    verified_on: str
    source: str
    tier: str
    output_includes_thinking_tokens: bool
    models: dict[str, ModelPrice]

    def price_for(self, model: str) -> ModelPrice | None:
        return self.models.get(model)


@lru_cache(maxsize=1)
def load_pricing_table(path: Path | None = None) -> PricingTable:
    data = json.loads((path or PRICING_TABLE_PATH).read_text(encoding="utf-8"))
    models = {
        name: ModelPrice(
            input_usd_per_mtok=float(entry["input_usd_per_mtok"]),
            output_usd_per_mtok=float(entry["output_usd_per_mtok"]),
            cached_input_usd_per_mtok=(
                float(entry["cached_input_usd_per_mtok"])
                if entry.get("cached_input_usd_per_mtok") is not None
                else None
            ),
            note=str(entry.get("note", "")),
        )
        for name, entry in data["models"].items()
    }
    return PricingTable(
        verified_on=str(data["verified_on"]),
        source=str(data["source"]),
        tier=str(data.get("tier", "paid")),
        output_includes_thinking_tokens=bool(data.get("output_includes_thinking_tokens", True)),
        models=models,
    )


def estimate_cost_usd(model: str, *, prompt_tokens: int, output_tokens: int) -> float | None:
    """Estimated USD for one call, or None when the model is unpriced.

    `output_tokens` must already include thinking tokens, because Google bills
    thinking tokens at the output rate. `TokenUsage.output_tokens` is the
    candidates count and `thinking_tokens` is separate, so callers pass the sum.
    """
    price = load_pricing_table().price_for(model)
    if price is None:
        return None
    cost = (
        prompt_tokens * price.input_usd_per_mtok + output_tokens * price.output_usd_per_mtok
    ) / 1_000_000
    return round(cost, 10)
