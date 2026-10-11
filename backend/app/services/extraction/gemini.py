from __future__ import annotations

import logging
import threading
import time
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import ExtractionError, ExtractionUnavailableError
from app.services.extraction.base import ExtractionResult, ModelInput, TokenUsage
from app.services.extraction.prompts import PROMPT_VERSION, SYSTEM_INSTRUCTION
from app.services.extraction.schema import (
    SCHEMA_VERSION,
    ExtractedMetadata,
    sanitize_metadata,
)


logger = logging.getLogger(__name__)

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

    def _config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ExtractedMetadata,
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
        started = time.perf_counter()
        try:
            response = self._generate(image)
        except ExtractionError:
            raise
        except genai_errors.APIError as exc:
            # Never surface provider text, keys or URLs to the caller.
            logger.warning("gemini_request_failed", extra={"stage": "extraction"})
            logger.debug("gemini_error_detail", exc_info=exc)
            raise ExtractionError("extraction_provider_error") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)

        self._reject_unusable_response(response)

        try:
            metadata = sanitize_metadata(response.parsed)
        except (ValidationError, ValueError, TypeError) as exc:
            logger.info("extraction_schema_invalid", extra={"stage": "extraction"})
            raise ExtractionError("extraction_invalid") from exc

        return ExtractionResult(
            metadata=metadata,
            model=self.model,
            prompt_version=PROMPT_VERSION,
            schema_version=SCHEMA_VERSION,
            latency_ms=latency_ms,
            usage=self._usage(response),
        )

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
