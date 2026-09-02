from formwise_api.privacy.engine import redact_text, scan_text, summaries


def test_sensitive_values_are_redacted_without_retaining_the_value() -> None:
    source = "Contact alice@example.com or call +91 9876543210."
    findings = scan_text(source)
    protected = redact_text(source, findings)

    assert "alice@example.com" not in protected
    assert "9876543210" not in protected
    assert "[EMAIL REDACTED]" in protected
    assert "[PHONE REDACTED]" in protected


def test_privacy_summaries_contain_categories_and_counts_only() -> None:
    findings = scan_text("a@example.com and b@example.com")

    assert [summary.model_dump() for summary in summaries(findings)] == [
        {"category": "email", "action": "REDACT", "count": 2}
    ]
