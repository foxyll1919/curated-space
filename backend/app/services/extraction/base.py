from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.services.extraction.schema import ExtractedMetadata


@dataclass(frozen=True)
class CacheIdentity:
    """The versions that determine what the provider would answer.

    Declared on the extractor so the analysis cache can build its key *before*
    any call is made. Lives here, next to the protocol that exposes it, so the
    cache never has to import the provider modules.
    """

    model: str
    prompt_version: str
    schema_version: str


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class ModelInput:
    """The downscaled image bytes actually sent to the provider."""

    data: bytes
    mime: str


@dataclass(frozen=True)
class ExtractionResult:
    metadata: ExtractedMetadata
    model: str
    prompt_version: str
    schema_version: str
    latency_ms: int
    usage: TokenUsage = field(default_factory=TokenUsage)
    #: Taxonomy label the provider returned, only when the labeled schema was
    #: requested (`GEMINI_RETURN_LABELS`). None otherwise. It exists so the eval
    #: harness can compare Gemini's label against the local classifier's without
    #: a second provider call; the serving pipeline ignores it.
    label: str | None = None


class MetadataExtractor(Protocol):
    """The swappable provider boundary. Tests substitute a fake; nothing else changes."""

    @property
    def cache_identity(self) -> CacheIdentity:
        """Versions that determine the answer, known before any call is made.

        The analysis cache needs this to build its key up front; a provider that
        cannot name its own versions simply disables caching.
        """
        ...

    def extract(self, image: ModelInput) -> ExtractionResult: ...
