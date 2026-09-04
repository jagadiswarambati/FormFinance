"""Regression test: BatchMetricsResponse must not silently drop fields that
BatchMetrics.to_dict() actually computes.

Before this fix, BatchMetricsResponse declared only a subset of
BatchMetrics's fields. Pydantic's default `extra="ignore"` behavior meant
`BatchMetricsResponse(**metrics.to_dict())` silently dropped
evidence_match_rate, exception_rate, extraction_success_rate, total_records,
processed, and successfully_extracted from the JSON the frontend receives,
even though the batch processor had already computed them.
"""

from formwise_api.settlements.batch_processor import BatchMetrics
from formwise_api.settlements.router import BatchMetricsResponse

PREVIOUSLY_DROPPED_FIELDS = [
    "evidence_match_rate",
    "exception_rate",
    "extraction_success_rate",
    "total_records",
    "processed",
    "successfully_extracted",
]


def test_batch_metrics_response_includes_previously_dropped_fields() -> None:
    metrics = BatchMetrics()
    metrics.total_records = 10
    metrics.processed = 10
    metrics.successfully_extracted = 9
    metrics.evidence_checked = 8
    metrics.evidence_matched = 6
    metrics.evidence_match_rate = 0.75
    metrics.exception_count = 4
    metrics.exception_rate = 0.4
    metrics.extraction_success_rate = 0.9
    metrics.total_settlements = 10
    metrics.total_deductions = 20
    metrics.approved_count = 6
    metrics.flagged_count = 3
    metrics.escalated_count = 1
    metrics.verified_deductions = 15
    metrics.disputed_deductions = 4
    metrics.unverifiable_deductions = 1
    metrics.settlement_approval_rate = 0.6
    metrics.deduction_verification_rate = 0.75
    metrics.agent_investigations = 4
    metrics.agent_successes = 3
    metrics.agent_failures = 1

    response = BatchMetricsResponse(**metrics.to_dict())
    payload = response.model_dump()

    for field_name in PREVIOUSLY_DROPPED_FIELDS:
        assert field_name in payload, f"{field_name} missing from BatchMetricsResponse"
        assert payload[field_name] == getattr(metrics, field_name)


def test_batch_metrics_response_defaults_are_safe_when_unset() -> None:
    """A response built from a freshly-constructed BatchMetrics() must not error."""
    response = BatchMetricsResponse(**BatchMetrics().to_dict())
    assert response.total_records == 0
    assert response.evidence_match_rate == 0.0
    assert response.exception_rate == 0.0
    assert response.extraction_success_rate == 0.0
