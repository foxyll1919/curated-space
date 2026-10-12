from __future__ import annotations

import logging
import random
import threading
import time
from typing import Any

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import ExtractionError, ExtractionUnavailableError
from app.services.extraction.base import (
    CacheIdentity,
    ExtractionResult,
    ModelInput,
    TokenUsage,
)
from app.services.extraction.prompts import PROMPT_VERSION, SYSTEM_INSTRUCTION
from app.services.extraction.schema import (
    LABELED_SCHEMA_VERSION,
    SCHEMA_VERSION,
    ExtractedMetadata,
    build_labeled_schema,
    sanitize_metadata,
    validate_labels,
)


logger = logging.getLogger(__name__)

#: Timeouts and dropped connections are retryable; a 4xx response is not.
#: `google-genai` surfaces transport faults as httpx exceptions and provider
#: faults as `APIError`, so both ends of the SDK are covered.
_RETRYABLE_TRANSPORT_ERRORS = (httpx.TransportError, TimeoutError)

_SAFETY_FINISH_REASONS = frozenset(
    {
        types.FinishReason.SAFETY,
        types.FinishReason.PROHIBITED_CONTENT,
        types.FinishReason.SPII,
        types.FinishReason.BLOCKLIST,
        types.FinishReason.IMAGE_SAFETY,
        types.FinishReason.IMAGE_PROHIBITED_CONTENT,
        types.FinishReason.RECITATION,
        types.FinishReason.IMAGE_RECITATION,
    }
)


class GeminiExtractor:
    """Structured metadata extraction backed by the official google-genai SDK.

    The client is built lazily so importing this module never needs a key or
    the network, and tests never need a key at all.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: genai.Client | None = None
        self._lock = threading.Lock()

    @property
    def model(self) -> str:
        return self._settings.gemini_model

    @property
    def schema_version(self) -> str:
        """The version of the schema actually being requested.

        Keyed on the flag because the labeled variant is a different response
        shape: sharing one version would let a labeled answer be served from the
        cache to an unlabeled request, which is exactly the class of bug the
        version-in-the-key rule exists to prevent.
        """
        return LABELED_SCHEMA_VERSION if self._labels_enabled() else SCHEMA_VERSION

    @property
    def cache_identity(self) -> CacheIdentity:
        return CacheIdentity(
            model=self.model,
            prompt_version=PROMPT_VERSION,
            schema_version=self.schema_version,
        )

    def _labels_enabled(self) -> bool:
        return bool(self._settings.gemini_return_labels)

    @property
    def taxonomy_labels(self) -> tuple[str, ...]:
        """Labels from the taxonomy file. Raises rather than guessing.

        Imported lazily so that turning the flag on in an environment with no
        taxonomy file fails with one clear error instead of an empty enum, which
        the provider would happily satisfy with any string.
        """
        if not self._labels_enabled():
            return ()
        from curated_ml.taxonomy import load_taxonomy

        return load_taxonomy(self._settings.taxonomy_path).labels

    @property
    def is_configured(self) -> bool:
        api_key = self._settings.gemini_api_key
        return api_key is not None and bool(api_key.get_secret_value().strip())

    def _get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client
        with self._lock:
            if self._client is None:
                api_key = self._settings.gemini_api_key
                if api_key is None or not api_key.get_secret_value().strip():
                    raise ExtractionUnavailableError()
                self._client = genai.Client(
                    api_key=api_key.get_secret_value(),
                    http_options=types.HttpOptions(timeout=self._settings.gemini_timeout_ms),
                )
        return self._client

    def _response_schema(self) -> Any:
        labels = self.taxonomy_labels
        return build_labeled_schema(labels) if labels else ExtractedMetadata

    def _config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=self._response_schema(),
            max_output_tokens=self._settings.gemini_max_output_tokens,
            media_resolution=types.MediaResolution(
                f"MEDIA_RESOLUTION_{self._settings.gemini_media_resolution}"
            ),
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel(self._settings.gemini_thinking_level.upper())
            ),
        )

    def _generate(self, image: ModelInput) -> Any:
        client = self._get_client()
        part = types.Part.from_bytes(data=image.data, mime_type=image.mime)
        return client.models.generate_content(
            model=self.model,
            contents=types.Content(parts=[part], role="user"),
            config=self._config(),
        )

    def extract(self, image: ModelInput) -> ExtractionResult:
        """One bounded call: transport retries, then at most one repair retry.

        Transport retries are only for 429/5xx/timeouts. A schema-validation
        failure gets exactly one repair retry, because a malformed response is
        not the provider being unwell and blind retries would just re-bill.
        After that the item fails cleanly with `extraction_invalid`.
        """
        deadline = time.monotonic() + self._settings.gemini_total_timeout_ms / 1000
        started = time.perf_counter()
        repairs = 0
        while True:
            response = self._generate_with_retries(image, deadline)
            self._reject_unusable_response(response)
            label: str | None = None
            try:
                metadata = sanitize_metadata(response.parsed)
                label = self._read_label(response.parsed)
            except (ValidationError, ValueError, TypeError) as exc:
                if repairs >= self._settings.gemini_max_schema_repairs:
                    logger.info("extraction_schema_invalid", extra={"stage": "extraction"})
                    raise ExtractionError("extraction_invalid") from exc
                repairs += 1
                logger.info("extraction_repair_retry", extra={"stage": "extraction"})
                continue
            return ExtractionResult(
                metadata=metadata,
                model=self.model,
                prompt_version=PROMPT_VERSION,
                schema_version=self.schema_version,
                latency_ms=int((time.perf_counter() - started) * 1000),
                usage=self._usage(response),
                label=label,
            )

    def _generate_with_retries(self, image: ModelInput, deadline: float) -> Any:
        attempts = max(0, self._settings.gemini_max_retries) + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return self._generate(image)
            except (genai_errors.APIError, *_RETRYABLE_TRANSPORT_ERRORS) as exc:
                last_error = exc
                if attempt == attempts - 1 or not self._is_retryable(exc):
                    break
                delay = self._backoff_delay(attempt)
                remaining = deadline - time.monotonic()
                if remaining <= delay:
                    break
                time.sleep(delay)
            except ExtractionError:
                raise
        # Never surface provider text, keys or URLs to the caller.
        logger.warning("gemini_request_failed", extra={"stage": "extraction"})
        logger.debug("gemini_error_detail", exc_info=last_error)
        raise ExtractionError("extraction_provider_error") from last_error

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """429, 5xx and transport timeouts only.

        A 4xx that is not 429 is the caller's problem: retrying it burns the
        budget without any chance of a different answer.
        """
        if isinstance(exc, _RETRYABLE_TRANSPORT_ERRORS):
            return True
        if not isinstance(exc, genai_errors.APIError):
            return False
        code = getattr(exc, "code", None) or 0
        return code == 429 or 500 <= code < 600

    def _backoff_delay(self, attempt: int) -> float:
        """Exponential backoff with jitter, clamped to the configured ceiling."""
        base = self._settings.gemini_retry_base_delay_ms / 1000
        ceiling = self._settings.gemini_retry_max_delay_ms / 1000
        return min(base * (2**attempt), ceiling) * random.uniform(0.5, 1.5)

    def _reject_unusable_response(self, response: Any) -> None:
        """Map blocked, truncated and empty responses to stable error codes."""
        if getattr(response, "prompt_feedback", None) and getattr(
            response.prompt_feedback, "block_reason", None
        ):
            raise ExtractionError("extraction_blocked")

        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            raise ExtractionError("extraction_empty")

        candidate = candidates[0]
        finish_reason = getattr(candidate, "finish_reason", None)
        if finish_reason in _SAFETY_FINISH_REASONS:
            raise ExtractionError("extraction_blocked")
        if finish_reason == types.FinishReason.MAX_TOKENS:
            raise ExtractionError("extraction_truncated")
        if getattr(response, "parsed", None) is None:
            raise ExtractionError("extraction_empty")

    def _read_label(self, parsed: Any) -> str | None:
        """Pull the provider's taxonomy label out, or None when not requested.

        An off-taxonomy label raises, so it takes the repair-retry path and ends
        as `extraction_invalid` rather than being stored as an invented category.
        Returning it rather than logging it keeps the eval harness's Gemini arm
        honest: the value it scores is the validated one.
        """
        if not self._labels_enabled():
            return None
        raw = getattr(parsed, "labels", None)
        if raw is None:
            raise ValueError("labeled schema returned no label")
        return validate_labels(raw, self.taxonomy_labels)

    def _usage(self, response: Any) -> TokenUsage:
        metadata = getattr(response, "usage_metadata", None)
        if metadata is None:
            return TokenUsage()
        return TokenUsage(
            prompt_tokens=metadata.prompt_token_count or 0,
            output_tokens=metadata.candidates_token_count or 0,
            thinking_tokens=metadata.thoughts_token_count or 0,
            total_tokens=metadata.total_token_count or 0,
        )
