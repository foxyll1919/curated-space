from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.services.extraction.schema import ExtractedMetadata


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


class MetadataExtractor(Protocol):
    """The swappable provider boundary. Tests substitute a fake; nothing else changes."""

    def extract(self, image: ModelInput) -> ExtractionResult: ...
