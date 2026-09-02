"""Dependency wiring for privacy-dashboard orchestration."""

from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.privacy.dashboard_repository import (
    FirestorePrivacyAuditEventRepository,
    FirestorePrivacySummaryRepository,
    PrivacyAuditEventRepository,
    PrivacySummaryRepository,
)
from formwise_api.privacy.projector import PrivacySummaryProjector
from formwise_api.privacy.refresher import PrivacySummaryRefresher
from formwise_api.privacy.repository import FirestorePrivacyReportRepository
from formwise_api.understanding.repository import FirestoreUnderstandingRepository


def get_privacy_summary_refresher() -> PrivacySummaryRefresher:
    client = get_firestore_client()
    return PrivacySummaryRefresher(
        FirestorePrivacySummaryRepository(client),
        FirestorePrivacyAuditEventRepository(client),
        FirestorePrivacyReportRepository(client),
        FirestoreUnderstandingRepository(client),
        PrivacySummaryProjector(),
    )


def get_privacy_summary_repository() -> PrivacySummaryRepository:
    return FirestorePrivacySummaryRepository(get_firestore_client())


def get_privacy_audit_event_repository() -> PrivacyAuditEventRepository:
    return FirestorePrivacyAuditEventRepository(get_firestore_client())
