from functools import lru_cache
from pathlib import Path
from socket import gethostname

from pydantic import Field
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


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_find_env_file(), extra="ignore")
    firebase_project_id: str | None = None
    firebase_service_account_json: str | None = None
    firebase_service_account_path: str | None = None
    log_level: str = "INFO"
    local_storage_path: str = "storage/uploads"
    quarantine_storage_path: str = "storage/quarantine"
    ocr_result_storage_path: str = "storage/ocr"
    privacy_result_storage_path: str = "storage/privacy"
    render_output_storage_path: str = "storage/renders"
    render_timeout_seconds: float = Field(default=60.0, ge=1, le=300)
    render_coordinate_confidence_threshold: float = Field(default=0.85, ge=0, le=1)
    ocr_provider: str = "paddleocr"
    ocr_worker_poll_seconds: float = Field(default=2.0, ge=0.5, le=60.0)
    worker_max_concurrency: int = Field(default=3, ge=1, le=16)
    worker_max_attempts: int = Field(default=3, ge=1, le=10)
    worker_retry_backoff_seconds: float = Field(default=2.0, ge=0.5, le=3600)
    worker_retry_backoff_max_seconds: float = Field(default=60.0, ge=1, le=86400)
    ocr_timeout_seconds: float = Field(default=120.0, ge=1, le=1800)
    retention_timeout_seconds: float = Field(default=120.0, ge=1, le=1800)
    worker_heartbeat_seconds: float = Field(default=15.0, ge=1, le=300)
    worker_instance_id: str = Field(default_factory=gethostname, min_length=1, max_length=128)


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
