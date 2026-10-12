"""A scripted provider, so the harness has something to measure in CI.

The point is not to fake a good model. It is to exercise every code path the real
provider path uses - structured metadata, labels, token usage, cost, latency,
blocking - with numbers that are deterministic and obviously not measurements.

Two failure modes are scriptable so tests can cover them without monkeypatching:
a schema-invalid response and a blocked one. A third, a per-call fault counter,
reproduces the retry behaviour of the real extractor.

Every response is marked by a token count that no real Gemini call produces, and
reports built from this provider record `provider: "fake"`.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

from curated_evals.config import EvalConfig


#: A fixed, implausible token count. If this ever appears in a report labelled
#: "live", the fake provider was used by mistake.
FAKE_PROMPT_TOKENS = 111
FAKE_OUTPUT_TOKENS = 42

_TITLES = {
    "Design": "Colour palette and layout reference",
    "Ideas": "Sketch notes for a side project",
    "Inspiration": "Mood board of interface examples",
    "References": "Saved reference article on typography",
    "Research": "Paper summary kept for reference",
    "Resources": "Link to a tools list",
    "Technology": "Config screen for a running service",
    "Tutorials": "Step-by-step walkthrough with code samples",
}


@dataclass
class FakeExtractor:
    """Mimics the `MetadataExtractor` protocol closely enough to benchmark it."""

    config: EvalConfig
    labels: tuple[str, ...]
    #: Faults left to raise on the next calls, then decremented.
    faults: int = field(default=0)
    #: Return metadata that fails schema validation, to exercise the repair path.
    invalid_responses: int = 0
    calls: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 120

    @property
    def cache_identity(self) -> Any:
        from app.services.extraction.base import CacheIdentity

        return CacheIdentity(
            model=self.config.model,
            prompt_version="prompt-v1",
            schema_version=("metadata-v1+labels" if self.config.provider_labels else "metadata-v1"),
        )

    @property
    def is_configured(self) -> bool:
        return True

    def extract(self, image: Any) -> Any:
        from app.services.extraction.base import ExtractionResult, TokenUsage
        from app.services.extraction.schema import ExtractedMetadata

        if self.faults > 0:
            self.faults -= 1
            from app.core.errors import ExtractionError

            raise ExtractionError("extraction_provider_error")

        self.calls += 1
        label = self._label_for(image)
        title = _TITLES.get(label, "Screenshot")
        if self.invalid_responses > 0:
            self.invalid_responses -= 1
            # A title of "" fails the schema's min_length, which is what the real
            # provider's repair retry exists for.
            metadata = ExtractedMetadata.model_construct(title="", description="", tags=[])
        else:
            metadata = ExtractedMetadata(
                title=title,
                description=f"A {label.lower()} screenshot saved for later.",
                tags=[label.lower(), "screenshot"],
            )

        # Deterministic but image-dependent, so latency varies the way a real
        # call would without making tests flaky.
        started = time.perf_counter()
        digest = hashlib.sha256(image.data).hexdigest()
        latency = self.latency_ms + int(digest[:2], 16)
        time.sleep(0)  # keep the call shape async-free and the timing measurable
        del started

        return ExtractionResult(
            metadata=metadata,
            model=self.config.model,
            prompt_version="prompt-v1",
            schema_version=("metadata-v1+labels" if self.config.provider_labels else "metadata-v1"),
            latency_ms=latency,
            usage=TokenUsage(
                prompt_tokens=FAKE_PROMPT_TOKENS,
                output_tokens=FAKE_OUTPUT_TOKENS,
                thinking_tokens=0,
                total_tokens=FAKE_PROMPT_TOKENS + FAKE_OUTPUT_TOKENS,
            ),
            label=label if self.config.provider_labels else None,
        )

    def _label_for(self, image: Any) -> str:
        """Pick a label deterministically from the image bytes."""
        if not self.labels:
            return ""
        digest = hashlib.sha256(image.data).hexdigest()
        return self.labels[int(digest[:8], 16) % len(self.labels)]


def build_fake_extractor(config: EvalConfig, labels: tuple[str, ...]) -> FakeExtractor:
    return FakeExtractor(config=config, labels=tuple(labels))
