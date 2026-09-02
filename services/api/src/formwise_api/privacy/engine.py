import re
from dataclasses import dataclass

from formwise_api.privacy.models import PrivacyAction, PrivacyFindingSummary


@dataclass(frozen=True)
class PrivacyFinding:
    category: str
    confidence: float
    matched_text: str
    start: int
    end: int
    action: PrivacyAction


_PATTERNS: tuple[tuple[str, re.Pattern[str], PrivacyAction], ...] = (
    ("aadhaar", re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)"), "REDACT"),
    ("pan", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE), "ASK_USER"),
    ("passport", re.compile(r"\b[A-PR-WY][1-9]\d{6}\b", re.IGNORECASE), "REDACT"),
    ("driving_licence", re.compile(r"\b[A-Z]{2}[ -]?\d{2}[ -]?\d{4,11}\b", re.IGNORECASE), "REDACT"),
    ("voter_id", re.compile(r"\b[A-Z]{3}\d{7}\b", re.IGNORECASE), "REDACT"),
    ("bank_account", re.compile(r"(?<!\d)\d{9,18}(?!\d)"), "REDACT"),
    ("ifsc", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.IGNORECASE), "REDACT"),
    ("upi", re.compile(r"\b[a-zA-Z0-9._-]{2,}@[a-zA-Z]{2,}\b"), "REDACT"),
    ("payment_card", re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"), "BLOCK"),
    ("phone", re.compile(r"(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)"), "ASK_USER"),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "REDACT"),
    ("date_of_birth", re.compile(r"\b(?:0?[1-9]|[12]\d|3[01])[/-](?:0?[1-9]|1[0-2])[/-](?:19|20)\d{2}\b"), "BLOCK"),
    ("insurance_number", re.compile(r"\b(?:insurance|policy)\s*(?:no\.?|number)?\s*[:#-]?\s*[A-Z0-9-]{6,}\b", re.IGNORECASE), "BLOCK"),
    ("patient_id", re.compile(r"\b(?:patient|mrn)\s*(?:id|no\.?|number)?\s*[:#-]?\s*[A-Z0-9-]{4,}\b", re.IGNORECASE), "BLOCK"),
)


def scan_text(text: str) -> list[PrivacyFinding]:
    findings: list[PrivacyFinding] = []
    occupied: list[tuple[int, int]] = []
    for category, pattern, action in _PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            if any(start < taken_end and end > taken_start for taken_start, taken_end in occupied):
                continue
            occupied.append((start, end))
            findings.append(PrivacyFinding(category, 0.98, match.group(0), start, end, action))
    return sorted(findings, key=lambda finding: finding.start)


def redact_text(text: str, findings: list[PrivacyFinding]) -> str:
    protected = text
    for finding in sorted(findings, key=lambda item: item.start, reverse=True):
        marker = f"[{finding.category.upper()} REDACTED]"
        protected = protected[:finding.start] + marker + protected[finding.end:]
    return protected


def summaries(findings: list[PrivacyFinding]) -> list[PrivacyFindingSummary]:
    grouped: dict[tuple[str, PrivacyAction], int] = {}
    for finding in findings:
        key = (finding.category, finding.action)
        grouped[key] = grouped.get(key, 0) + 1
    return [PrivacyFindingSummary(category=category, action=action, count=count) for (category, action), count in sorted(grouped.items())]
