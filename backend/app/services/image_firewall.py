from __future__ import annotations

import hashlib
import io
import warnings
from dataclasses import dataclass
from typing import Final

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import Settings
from app.core.errors import (
    AnimatedImageError,
    PayloadTooLargeError,
    TooManyPixelsError,
    UnprocessableImageError,
    UnsupportedMediaTypeError,
)


READ_CHUNK_BYTES: Final = 64 * 1024

#: Decoded formats we accept. The client-declared MIME type is never consulted.
ALLOWED_FORMATS: Final = frozenset({"PNG", "JPEG", "WEBP"})

#: Deterministic storage and model-input format. PNG is lossless, so the
#: re-encode introduces no quality drift and no encoder-dependent quality knob.
STORAGE_FORMAT: Final = "PNG"
STORAGE_MIME: Final = "image/png"


@dataclass(frozen=True)
class SanitizedImage:
    """The two outputs of the firewall plus the identity of the pixels."""

    content_sha256: str
    mime: str
    width: int
    height: int
    byte_size: int
    stored_bytes: bytes
    model_input_bytes: bytes


def read_bounded(file, max_bytes: int) -> bytes:
    """Stream an upload in chunks, aborting as soon as the cap is exceeded.

    Never read the whole thing at once: a client can send a body far larger
    than it declared. Reads the sync spooled file that multipart parsing has
    already populated, so it is safe to call from a threadpool route.
    """
    buffer = bytearray()
    while True:
        chunk = file.read(READ_CHUNK_BYTES)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise PayloadTooLargeError()
    return bytes(buffer)


def _open_image(data: bytes) -> Image.Image:
    try:
        with warnings.catch_warnings():
            # Pillow warns between MAX_IMAGE_PIXELS and twice that limit, then
            # raises beyond twice the limit. Treat both cases as a stable
            # firewall rejection before a full decode can allocate the raster.
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            probe = Image.open(io.BytesIO(data))
            decoded_format = probe.format
            if decoded_format not in ALLOWED_FORMATS:
                raise UnsupportedMediaTypeError()
            if getattr(probe, "is_animated", False) or getattr(probe, "n_frames", 1) > 1:
                raise AnimatedImageError()
            probe.verify()
    except UnsupportedMediaTypeError:
        raise
    except UnprocessableImageError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise TooManyPixelsError() from exc
    except (
        UnidentifiedImageError,
        SyntaxError,
        ValueError,
        OSError,
    ):
        # Covers .jpg-that-is-really-HTML, truncated streams and zero-byte files.
        raise UnprocessableImageError()

    try:
        # verify() leaves the image unusable, so reopen to decode the pixels.
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            return Image.open(io.BytesIO(data))
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise TooManyPixelsError() from exc
    except (
        UnidentifiedImageError,
        SyntaxError,
        ValueError,
        OSError,
    ):
        raise UnprocessableImageError()


def _normalized(image: Image.Image) -> Image.Image:
    """Drop metadata and flatten to a known mode, deterministically."""
    transposed = ImageOps.exif_transpose(image)
    if transposed.mode not in ("RGB", "RGBA"):
        background = Image.new("RGB", transposed.size, (255, 255, 255))
        converted = transposed.convert("RGBA")
        background.paste(converted, mask=converted.split()[-1])
        transposed = background
    # Build the encode from scratch so no EXIF, ICC profile or text chunk rides
    # along; re-saving the source image would re-attach what we are removing.
    clean = Image.new(transposed.mode, transposed.size)
    clean.paste(transposed)
    clean.info.clear()
    return clean


def _encode(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=STORAGE_FORMAT, optimize=False)
    return buffer.getvalue()


def _downscale(image: Image.Image, max_edge: int) -> Image.Image:
    longest = max(image.size)
    if longest <= max_edge:
        return image.copy()
    ratio = max_edge / longest
    size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
    return image.resize(size, Image.Resampling.LANCZOS)


def _pixel_hash(image: Image.Image) -> str:
    """Hash the decoded, normalized pixel buffer.

    Hashing the re-encoded file would invalidate every stored hash whenever
    Pillow or the encoder changes, which would silently defeat dedupe.
    """
    digest = hashlib.sha256()
    digest.update(f"{image.mode}|{image.width}x{image.height}|".encode())
    digest.update(image.tobytes())
    return digest.hexdigest()


def sanitize_image(data: bytes, settings: Settings) -> SanitizedImage:
    """Pure function: raw upload bytes -> sanitized image or a stable AppError."""
    if not data:
        raise UnprocessableImageError("The uploaded file is empty.")
    if len(data) > settings.max_upload_bytes:
        raise PayloadTooLargeError()

    previous_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels
    try:
        image = _open_image(data)
        width, height = image.size
        if width == 0 or height == 0:
            raise UnprocessableImageError()
        if width > settings.max_image_edge or height > settings.max_image_edge:
            raise TooManyPixelsError()
        if width * height > settings.max_image_pixels:
            raise TooManyPixelsError()

        normalized = _normalized(image)
    finally:
        Image.MAX_IMAGE_PIXELS = previous_limit

    stored_bytes = _encode(normalized)
    return SanitizedImage(
        content_sha256=_pixel_hash(normalized),
        mime=STORAGE_MIME,
        width=normalized.width,
        height=normalized.height,
        byte_size=len(stored_bytes),
        stored_bytes=stored_bytes,
        model_input_bytes=_encode(_downscale(normalized, settings.model_input_max_edge)),
    )


def prepare_model_input(stored_bytes: bytes, settings: Settings) -> bytes:
    """Regenerate the provider payload from already-sanitized stored bytes.

    Deterministic: sanitizing an already-sanitized image is a no-op, so this is
    safe to call again when re-analyzing an item.
    """
    return sanitize_image(stored_bytes, settings).model_input_bytes
