"""Deterministic server-side projection of privacy-dashboard metadata."""

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from formwise_document_core.privacy_models import PrivacyAuditEvent, PrivacySummary

from formwise_api.conversations.models import Conversation
from formwise_api.documents.models import DocumentResponse
from formwise_api.understanding.models import StructuredField


class PrivacySummaryProjector:
    """Builds a response-safe summary from already persisted system state."""

    def project(
        self,
        *,
        conversation: Conversation,
        document: DocumentResponse,
        fields: Iterable[StructuredField],
        privacy_report: Mapping[str, Any] | None,
        audit_events: Iterable[PrivacyAuditEvent],
        provider_id: str | None = None,
        processing_mode: str | None = None,
    ) -> PrivacySummary:
        events = tuple(sorted(audit_events, key=lambda event: event.timestamp))
        field_counts = self._field_counts(fields)

        policy_version = self._first_text(
            self._report_value(privacy_report, "policyVersion"),
            document.privacy_policy_version,
            *(event.policy_version for event in reversed(events)),
        )
        resolved_provider = self._first_text(
            provider_id,
            conversation.provider,
            *(event.provider_id for event in reversed(events)),
        )
        resolved_mode = self._first_text(
            processing_mode,
            *(event.processing_mode for event in reversed(events)),
        )
        evaluated_at = self._latest_evaluation_time(document, privacy_report, events)

        if policy_version is None:
            raise ValueError("POLICY_VERSION_UNAVAILABLE")
        if resolved_provider is None:
            raise ValueError("PROVIDER_ID_UNAVAILABLE")
        if resolved_mode is None:
            raise ValueError("PROCESSING_MODE_UNAVAILABLE")
        if evaluated_at is None:
            raise ValueError("PRIVACY_EVALUATION_TIME_UNAVAILABLE")

        report_categories = self._report_categories(privacy_report)
        ai_categories = self._ai_categories(field_counts["safe"], document)
        excluded_categories = self._excluded_categories(field_counts, report_categories)

        return PrivacySummary(
            policy_version=policy_version,
            provider_id=resolved_provider,
            processing_mode=resolved_mode,
            safe_field_count=field_counts["safe"],
            restricted_field_count=field_counts["restricted"],
            sensitive_field_count=field_counts["sensitive"],
            ai_data_categories=ai_categories,
            excluded_data_categories=excluded_categories,
            last_evaluated_at=evaluated_at,
            explanation_locale=conversation.locale,
        )

    @staticmethod
    def _field_counts(fields: Iterable[StructuredField]) -> dict[str, int]:
        counts = {"safe": 0, "restricted": 0, "sensitive": 0}
        for field in fields:
            tier = field.render_metadata.privacy_tier
            counts[tier] += 1
        return counts

    @staticmethod
    def _first_text(*values: str | None) -> str | None:
        return next((value for value in values if isinstance(value, str) and value), None)

    @staticmethod
    def _report_value(report: Mapping[str, Any] | None, key: str) -> str | None:
        value = report.get(key) if report is not None else None
        return value if isinstance(value, str) else None

    @staticmethod
    def _report_categories(report: Mapping[str, Any] | None) -> tuple[str, ...]:
        categories = report.get("piiCategories") if report is not None else None
        if not isinstance(categories, list):
            return ()
        return tuple(sorted({category for category in categories if isinstance(category, str)}))

    @staticmethod
    def _ai_categories(safe_field_count: int, document: DocumentResponse) -> tuple[str, ...]:
        categories: list[str] = []
        if safe_field_count > 0:
            categories.append("safe_field_schema")
        if document.redacted_text_storage_key:
            categories.append("sanitized_form_text")
        return tuple(categories)

    @staticmethod
    def _excluded_categories(
        field_counts: Mapping[str, int],
        report_categories: tuple[str, ...],
    ) -> tuple[str, ...]:
        categories = set(report_categories)
        if field_counts["restricted"] > 0:
            categories.add("restricted_field_values")
        if field_counts["sensitive"] > 0:
            categories.add("sensitive_field_values")
        return tuple(sorted(categories))

    @staticmethod
    def _latest_evaluation_time(
        document: DocumentResponse,
        report: Mapping[str, Any] | None,
        events: Iterable[PrivacyAuditEvent],
    ) -> datetime | None:
        timestamps = [
            value
            for value in (
                document.privacy_completed_at,
                report.get("completedAt") if report is not None else None,
                *(event.timestamp for event in events),
            )
            if isinstance(value, datetime)
        ]
        return max(timestamps) if timestamps else None
