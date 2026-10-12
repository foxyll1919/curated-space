from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ErrorBody:
    code: str
    message: str


@dataclass(frozen=True)
class ErrorResponse:
    error: ErrorBody
    request_id: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return {"error": {"code": self.error.code, "message": self.error.message}}


class AppError(Exception):
    """Base class for errors that map to a stable API response.

    The message is a short, safe string. Provider text, filesystem paths and
    exception reprs go to the server log only, never to the caller.
    """

    code = "internal_error"
    status_code = 500
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.public_message = message or self.message


class BadRequestError(AppError):
    code = "bad_request"
    status_code = 400
    message = "The request could not be processed."


class AuthenticationError(AppError):
    code = "unauthorized"
    status_code = 401
    message = "Authentication is required."


class RateLimitError(AppError):
    code = "rate_limited"
    status_code = 429
    message = "Too many requests. Please try again later."


class ConflictError(AppError):
    code = "conflict"
    status_code = 409
    message = "The item cannot be changed in its current state."


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404
    message = "The requested resource does not exist."


class PayloadTooLargeError(AppError):
    code = "too_large"
    status_code = 413
    message = "The uploaded image exceeds the maximum allowed size."


class UnsupportedMediaTypeError(AppError):
    code = "unsupported_type"
    status_code = 415
    message = "The uploaded image format is not supported."


class UnprocessableImageError(AppError):
    code = "corrupt_image"
    status_code = 422
    message = "The uploaded image could not be processed."


class TooManyPixelsError(UnprocessableImageError):
    code = "too_many_pixels"
    message = "The uploaded image exceeds the allowed dimensions."


class AnimatedImageError(UnprocessableImageError):
    code = "animated"
    message = "Animated or multi-frame images are not supported."


class ExtractionError(AppError):
    """A provider-side failure that belongs on the item, not on the response."""

    code = "extraction_failed"
    status_code = 502
    message = "Metadata extraction failed."

    def __init__(self, error_code: str, message: str | None = None) -> None:
        super().__init__(message)
        self.code = error_code


class ExtractionUnavailableError(AppError):
    code = "extraction_unavailable"
    status_code = 503
    message = "Metadata extraction is not configured."
