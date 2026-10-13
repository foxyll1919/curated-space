from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
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

    # Milestone 9: one configured key maps to one stable owner identity.
    api_key: SecretStr | None = None
    api_key_owner_id: str = "legacy-owner"

    # User accounts. Registration is always allowed for the very first account
    # so a fresh install is usable; afterwards it needs `auth_allow_registration`
    # or the `bootstrap-user` CLI. Password hashing uses the standard library,
    # so the only tunable is the PBKDF2 iteration count.
    auth_allow_registration: bool = False
    auth_session_ttl_days: int = Field(default=30, ge=1)
    auth_cookie_name: str = "cs_session"
    # Set true once the app is served over HTTPS; a session cookie must never
    # travel in plaintext on a public deployment.
    auth_cookie_secure: bool = False
    auth_password_min_length: int = Field(default=10, ge=8)
    password_hash_iterations: int = Field(default=600_000, ge=1)
    login_rate_limit: int = Field(default=10, ge=1)
    allowed_origins: list[str] = Field(default_factory=list)
    upload_rate_limit: int = Field(default=10, ge=1)
    reanalyze_rate_limit: int = Field(default=5, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    max_request_body_bytes: int = Field(default=8 * 1024 * 1024 + 64 * 1024, ge=1024)
    item_retention_days: int = Field(default=0, ge=0)

    # Milestone 9 replaces this per-upload flag with a real form field.
    analysis_enabled: bool = True

    # Milestone 4. A scikit-learn version mismatch refuses startup in
    # production and only warns in development; derived from `environment`.
    classifier_artifact: Path = (
        BACKEND_DIR.parent / "ml" / "model" / "curated_space_classifier_v2.pkl"
    )
    classifier_required: bool = True

    max_upload_bytes: int = 8 * 1024 * 1024
    max_image_edge: int = 8000
    max_image_pixels: int = 40_000_000
    model_input_max_edge: int = 1280

    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_timeout_ms: int = 30_000
    gemini_max_output_tokens: int = 300
    gemini_media_resolution: GeminiMediaResolution = "MEDIUM"
    gemini_thinking_level: GeminiThinkingLevel = "minimal"

    # Bounded retry policy (brief section 7.6). Transport retries are only for
    # 429/5xx/timeouts; `gemini_total_timeout_ms` bounds the whole `extract`
    # call including every backoff sleep, so a retry storm cannot hang a job.
    gemini_max_retries: int = 2
    gemini_max_schema_repairs: int = 1
    gemini_total_timeout_ms: int = 30_000
    gemini_retry_base_delay_ms: int = 250
    gemini_retry_max_delay_ms: int = 4_000

    # Pixel-hash cache (brief section 7.5). A hit costs no provider call.
    analysis_cache_enabled: bool = True

    # Budget guard (brief section 7.8). Both 0 disables the corresponding
    # check; a blocked item is stored as `deferred`, never dropped.
    daily_cost_cap_usd: float = 1.00
    max_analyses_per_minute: int = 30

    # Milestone 8 in-process job bounds and crash recovery.
    max_concurrent_analyses: int = Field(default=2, ge=1)
    stuck_job_timeout_minutes: int = Field(default=15, ge=1)

    # Prices come from app/core/gemini_pricing.json, not from settings. The
    # table records verified_on and source; a model missing from it has unknown
    # cost and is never priced by a default.

    # Milestone 6. `gemini_return_labels` makes the provider emit taxonomy enum
    # labels alongside the metadata, so the eval harness can compare "Gemini
    # labels it" against "the local classifier labels it" in one call. Default
    # off: it is a benchmark affordance, not a product behaviour, and enabling
    # it changes the response schema, so it must never be on by accident.
    gemini_return_labels: bool = False
    taxonomy_path: Path = BACKEND_DIR.parent / "ml" / "taxonomy" / "legacy-8.json"

    @field_validator("allowed_origins")
    @classmethod
    def validate_allowed_origins(cls, origins: list[str]) -> list[str]:
        if "*" in origins or any(
            not origin.startswith(("http://", "https://")) for origin in origins
        ):
            raise ValueError("allowed_origins must contain explicit http(s) origins, never '*'")
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
