"""Fail-closed scanning boundary for quarantined source uploads."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

ScanOutcome = Literal["clean", "blocked", "unavailable"]


@dataclass(frozen=True)
class UploadScanResult:
    outcome: ScanOutcome
    provider: str
    reason_code: str | None = None


class UploadScanner(Protocol):
    provider: str

    def scan(self, source: Path) -> UploadScanResult: ...


class UnavailableUploadScanner:
    """Placeholder hook that fails closed until a scanner adapter is configured."""

    provider = "unconfigured"

    def scan(self, source: Path) -> UploadScanResult:
        del source
        return UploadScanResult(
            outcome="unavailable",
            provider=self.provider,
            reason_code="SCAN_UNAVAILABLE",
        )
