from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> Path:
    """Locate the workspace environment file independently of the service CWD."""
    directories = (Path.cwd(), *Path.cwd().parents)
    for directory in directories:
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file() and "[tool.uv.workspace]" in pyproject.read_text(encoding="utf-8"):
            candidate = directory / ".env"
            if candidate.is_file():
                return candidate
    for directory in directories:
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return Path(".env")


def resolve_env_relative_path(value: str) -> Path:
    """Resolve a relative configured path beside the discovered environment file."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return _find_env_file().resolve().parent / path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        extra="ignore",
    )

    formwise_env: str = Field(
        default="development",
        pattern="^(development|staging|production)$",
    )

    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    app_name: str = "FormWise AI API"
    cors_allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    cors_allow_credentials: bool = True
    cors_allowed_methods: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    cors_allowed_headers: tuple[str, ...] = (
        "Authorization",
        "Content-Type",
        "Origin",
        "Accept",
        "Idempotency-Key",
        "X-Request-ID",
    )
    cors_expose_headers: tuple[str, ...] = ("X-Request-ID",)
    cors_max_age_seconds: int = Field(default=600, ge=0, le=86400)
    security_hsts_max_age_seconds: int = Field(default=0, ge=0, le=63072000)
    security_hsts_include_subdomains: bool = True
    security_content_security_policy: str = (
        "default-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    )
    readiness_require_worker_heartbeat: bool = False
    readiness_worker_heartbeat_max_age_seconds: int = Field(default=60, ge=5, le=3600)

    firebase_project_id: str | None = None

    firebase_service_account_json: str | None = None

    # NEW
    firebase_service_account_path: str | None = None

    terms_version: str = "v1"
    local_storage_path: str = "storage/uploads"
    quarantine_storage_path: str = "storage/quarantine"
    upload_signing_secret: str | None = None
    upload_intent_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    ocr_provider: str = "paddleocr"
    ocr_result_storage_path: str = "storage/ocr"
    privacy_result_storage_path: str = "storage/privacy"
    privacy_policy_version: str = "v1"
    understanding_provider_version: str = "deterministic-v1"
    render_coordinate_confidence_threshold: float = Field(default=0.85, ge=0, le=1)
    render_output_storage_path: str = "storage/renders"
    ai_provider: Literal["ollama"] = "ollama"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen3:8b"
    ollama_temperature: float = Field(default=0.2, ge=0, le=1)
    ollama_context_length: int = Field(default=8192, ge=1024, le=32768)
    ollama_max_tokens: int = Field(default=512, ge=64, le=2048)
    ollama_timeout_seconds: float = Field(default=30, gt=0, le=120)

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        if "*" in self.cors_allowed_origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must not contain '*'.")
        if self.formwise_env == "production" and self.security_hsts_max_age_seconds == 0:
            raise ValueError(
                "SECURITY_HSTS_MAX_AGE_SECONDS must be configured for production."
            )
        if self.formwise_env == "production" and not self.readiness_require_worker_heartbeat:
            raise ValueError("READINESS_REQUIRE_WORKER_HEARTBEAT must be enabled for production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
