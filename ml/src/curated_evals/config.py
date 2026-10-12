"""Eval configurations: the grid the brief wants to compare, as data.

A config is a provider knob combination plus which labeler runs. Keeping them in
one declarative structure means "compare flash-lite vs 3.1-flash-lite vs flash
at three media resolutions" is a list, not a code edit, and every run in a report
records the exact config that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MediaResolution = Literal["LOW", "MEDIUM", "HIGH"]
ThinkingLevel = Literal["minimal", "low", "medium", "high"]

#: Models the brief names for comparison. `gemini-2.5-*` is deliberately absent:
#: Milestone 3 found it scheduled for shutdown, and a benchmark of a dying model
#: is not a decision.
CANDIDATE_MODELS = ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash")

DEFAULT_RESOLUTIONS: tuple[MediaResolution, ...] = ("MEDIUM",)
DEFAULT_THINKING: tuple[ThinkingLevel, ...] = ("minimal",)


@dataclass(frozen=True)
class EvalConfig:
    """One cell of the benchmark grid."""

    name: str
    model: str
    media_resolution: MediaResolution = "MEDIUM"
    thinking_level: ThinkingLevel = "minimal"
    max_output_tokens: int = 300
    #: Ask the provider for a taxonomy enum label in the same call. This is the
    #: "Gemini does labels too" arm; it costs output tokens, which the report
    #: shows rather than hides.
    provider_labels: bool = False
    #: Run the local classifier on the extracted text. Always on for the
    #: comparison, off for a provider-only latency measurement.
    use_classifier: bool = True

    def provider_overrides(self) -> dict[str, object]:
        """Settings overrides for this cell. No code edit is needed to sweep."""
        return {
            "gemini_model": self.model,
            "gemini_media_resolution": self.media_resolution,
            "gemini_thinking_level": self.thinking_level,
            "gemini_max_output_tokens": self.max_output_tokens,
            "gemini_return_labels": self.provider_labels,
            # The harness measures the call itself; the budget guard and the
            # cache would otherwise silently change what is being measured.
            "analysis_cache_enabled": False,
            "daily_cost_cap_usd": 0.0,
            "max_analyses_per_minute": 0,
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "model": self.model,
            "media_resolution": self.media_resolution,
            "thinking_level": self.thinking_level,
            "max_output_tokens": self.max_output_tokens,
            "provider_labels": self.provider_labels,
            "use_classifier": self.use_classifier,
        }


def cell_name(model: str, resolution: str, thinking: str) -> str:
    """A stable, sortable name so two runs of the same cell compare cleanly."""
    return f"{model}|{resolution.lower()}|{thinking}"


def matrix(
    models: tuple[str, ...] = CANDIDATE_MODELS,
    resolutions: tuple[MediaResolution, ...] = DEFAULT_RESOLUTIONS,
    thinking_levels: tuple[ThinkingLevel, ...] = DEFAULT_THINKING,
    *,
    provider_labels: bool = False,
    use_classifier: bool = True,
) -> tuple[EvalConfig, ...]:
    """The full cross product, in a deterministic order."""
    return tuple(
        EvalConfig(
            name=cell_name(model, resolution, thinking),
            model=model,
            media_resolution=resolution,
            thinking_level=thinking,
            provider_labels=provider_labels,
            use_classifier=use_classifier,
        )
        for model in models
        for resolution in resolutions
        for thinking in thinking_levels
    )


def by_name(configs: tuple[EvalConfig, ...], name: str) -> EvalConfig:
    for config in configs:
        if config.name == name:
            return config
    available = ", ".join(c.name for c in configs)
    raise KeyError(f"unknown config {name!r}; available: {available}")
