"""Firewall cases from build.md section 5, plus the invariants around hashing."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.core.errors import (
    AnimatedImageError,
    PayloadTooLargeError,
    UnprocessableImageError,
    UnsupportedMediaTypeError,
)
from app.services.image_firewall import prepare_model_input, sanitize_image
from tests.conftest import make_image, make_settings


HTML_AS_JPEG = b"<!doctype html><html><body>not an image</body></html>"


def _settings(tmp_path, **overrides):
    return make_settings(tmp_path, **overrides)


def test_accepts_png_jpeg_and_webp(tmp_path):
    settings = _settings(tmp_path)
    for image_format in ("PNG", "JPEG", "WEBP"):
        result = sanitize_image(make_image(image_format=image_format), settings)
        assert result.mime == "image/png"
        assert (result.width, result.height) == (64, 48)
        assert result.byte_size == len(result.stored_bytes)


def test_rejects_html_disguised_as_jpeg(tmp_path):
    with pytest.raises(UnprocessableImageError):
        sanitize_image(HTML_AS_JPEG, _settings(tmp_path))


def test_rejects_empty_file(tmp_path):
    with pytest.raises(UnprocessableImageError):
        sanitize_image(b"", _settings(tmp_path))


def test_rejects_truncated_jpeg(tmp_path):
    truncated = make_image(width=200, height=200, image_format="JPEG")[:200]
    with pytest.raises(UnprocessableImageError):
        sanitize_image(truncated, _settings(tmp_path))


def test_rejects_unsupported_decoded_format(tmp_path):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, format="BMP")
    with pytest.raises(UnsupportedMediaTypeError):
        sanitize_image(buffer.getvalue(), _settings(tmp_path))


def test_rejects_animated_gif(tmp_path):
    buffer = io.BytesIO()
    frames = [Image.new("P", (10, 10), color=i) for i in range(2)]
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:], duration=50)
    with pytest.raises(UnsupportedMediaTypeError):
        sanitize_image(buffer.getvalue(), _settings(tmp_path))


def test_rejects_animated_webp(tmp_path):
    buffer = io.BytesIO()
    frames = [Image.new("RGB", (10, 10), (i, i, i)) for i in range(2)]
    frames[0].save(
        buffer, format="WEBP", save_all=True, append_images=frames[1:], duration=100, lossless=True
    )
    with pytest.raises(AnimatedImageError):
        sanitize_image(buffer.getvalue(), _settings(tmp_path))


def test_rejects_oversized_upload(tmp_path):
    settings = _settings(tmp_path, max_upload_bytes=512)
    with pytest.raises(PayloadTooLargeError):
        sanitize_image(make_image(width=200, height=200, image_format="JPEG"), settings)


def test_rejects_too_many_pixels(tmp_path):
    settings = _settings(tmp_path, max_image_pixels=64)
    with pytest.raises(UnprocessableImageError):
        sanitize_image(make_image(width=64, height=48), settings)


def test_rejects_oversized_edge(tmp_path):
    settings = _settings(tmp_path, max_image_edge=32)
    with pytest.raises(UnprocessableImageError):
        sanitize_image(make_image(width=64, height=48), settings)


def test_rejects_pixel_bomb(tmp_path):
    """A tiny file that declares enormous dimensions must not be decoded."""
    settings = _settings(tmp_path, max_image_pixels=100_000)
    with pytest.raises(UnprocessableImageError) as error:
        sanitize_image(make_image(width=4000, height=4000), settings)
    assert error.value.code == "too_many_pixels"


def test_pixel_limit_uses_stable_error_code(tmp_path):
    settings = _settings(tmp_path, max_image_pixels=64)
    with pytest.raises(UnprocessableImageError) as error:
        sanitize_image(make_image(width=64, height=48), settings)
    assert error.value.code == "too_many_pixels"


def test_strips_trailing_polyglot_payload(tmp_path):
    """Image-like content with an appended script stays an inert PNG."""
    polyglot = make_image() + b"\n<html><script>alert('x')</script></html>"

    result = sanitize_image(polyglot, _settings(tmp_path))

    assert result.mime == "image/png"
    assert b"<script>" not in result.stored_bytes
    assert Image.open(io.BytesIO(result.stored_bytes)).format == "PNG"


def test_strips_exif_metadata(tmp_path):
    buffer = io.BytesIO()
    image = Image.new("RGB", (32, 32), (5, 5, 5))
    exif = Image.Exif()
    exif[0x010F] = "Canon"  # Make
    exif[0x0110] = "EOS R"  # Model
    image.save(buffer, format="JPEG", exif=exif)
    source = Image.open(io.BytesIO(buffer.getvalue()))
    assert source.getexif().get(0x010F) == "Canon", "fixture must carry EXIF"

    result = sanitize_image(buffer.getvalue(), _settings(tmp_path))
    stored = Image.open(io.BytesIO(result.stored_bytes))
    assert stored.getexif().get(0x010F) is None
    assert stored.getexif().get(0x0110) is None
    assert "exif" not in stored.info
    assert b"Exif" not in result.stored_bytes


def test_strips_exif_gps_metadata(tmp_path):
    buffer = io.BytesIO()
    image = Image.new("RGB", (32, 32), (5, 5, 5))
    exif = Image.Exif()
    exif[0x8825] = {
        1: "N",
        2: (37, 46, 29),
        3: "W",
        4: (122, 25, 9),
    }
    image.save(buffer, format="JPEG", exif=exif)
    source = Image.open(io.BytesIO(buffer.getvalue()))
    assert source.getexif().get_ifd(0x8825)[1] == "N"

    result = sanitize_image(buffer.getvalue(), _settings(tmp_path))
    stored = Image.open(io.BytesIO(result.stored_bytes))
    assert stored.getexif().get_ifd(0x8825) == {}
    assert b"GPS" not in result.stored_bytes


def test_pixel_hash_is_stable_across_reencodes(tmp_path):
    """Two byte-different encodings of the same pixels share one identity."""
    settings = _settings(tmp_path)
    png = sanitize_image(make_image(image_format="PNG"), settings)
    jpeg = sanitize_image(make_image(image_format="JPEG", quality=95), settings)
    assert png.content_sha256 == jpeg.content_sha256


def test_model_input_is_downscaled_and_deterministic(tmp_path):
    settings = _settings(tmp_path, model_input_max_edge=32)
    result = sanitize_image(make_image(width=200, height=100), settings)
    model_input = Image.open(io.BytesIO(result.model_input_bytes))
    assert max(model_input.size) == 32
    assert prepare_model_input(result.stored_bytes, settings) == result.model_input_bytes


def test_normalizes_palette_and_alpha_to_opaque(tmp_path):
    buffer = io.BytesIO()
    Image.new("P", (16, 16)).save(buffer, format="PNG")
    result = sanitize_image(buffer.getvalue(), _settings(tmp_path))
    stored = Image.open(io.BytesIO(result.stored_bytes))
    assert stored.mode == "RGB"
