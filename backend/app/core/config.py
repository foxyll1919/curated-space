from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]

GeminiMediaResolution = Literal["LOW", "MEDIUM", "HIGH"]
GeminiThinkingLevel = Literal["minimal", "low", "medium", "high"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"
    log_level: str = "INFO"
    database_path: Path = BACKEND_DIR / "curated_space.db"
    storage_path: Path = BACKEND_DIR / "uploads"
    gemini_api_key: SecretStr | None = None

    # Milestone 9 replaces this per-upload flag with a real form field.
    analysis_enabled: bool = True

    max_upload_bytes: int = 8 * 1024 * 1024
    max_image_edge: int = 8000
    max_image_pixels: int = 40_000_000
    model_input_max_edge: int = 1280

    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_timeout_ms: int = 30_000
    gemini_max_output_tokens: int = 300
    gemini_media_resolution: GeminiMediaResolution = "MEDIUM"
    gemini_thinking_level: GeminiThinkingLevel = "minimal"

    # USD per million tokens. Verify against the official Gemini API pricing
    # page before trusting a cost estimate; Milestone 6 replaces these with a
    # checked-in table plus provenance.
    gemini_input_price_usd_per_mtok: float = Field(default=0.25)
    gemini_output_price_usd_per_mtok: float = Field(default=1.50)
    gemini_thinking_price_usd_per_mtok: float = Field(default=0.25)


@lru_cache
def get_settings() -> Settings:
    return Settings()
