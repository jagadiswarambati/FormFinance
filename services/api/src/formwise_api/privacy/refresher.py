"""Lifecycle orchestration for persisted privacy-summary refreshes."""

from formwise_api.conversations.models import Conversation
from formwise_api.documents.models import DocumentResponse
from formwise_api.privacy.dashboard_repository import (
    PrivacyAuditEventRepository,
    PrivacySummaryRepository,
)
from formwise_api.privacy.projector import PrivacySummaryProjector
from formwise_api.privacy.repository import PrivacyReportRepository
from formwise_api.understanding.repository import UnderstandingRepository


class PrivacySummaryRefresher:
    """Refreshes an existing summary after a successful API-side lifecycle event."""

    def __init__(
        self,
        summaries: PrivacySummaryRepository,
        events: PrivacyAuditEventRepository,
        reports: PrivacyReportRepository,
        structured_documents: UnderstandingRepository,
        projector: PrivacySummaryProjector,
    ) -> None:
        self._summaries = summaries
        self._events = events
        self._reports = reports
        self._structured_documents = structured_documents
        self._projector = projector

    def refresh(self, conversation: Conversation, document: DocumentResponse) -> bool:
        existing = self._summaries.get(conversation.id)
        structured_document = self._structured_documents.get(conversation.document_id)
        if existing is None or structured_document is None:
            return False

        try:
            summary = self._projector.project(
                conversation=conversation,
                document=document,
                fields=structured_document.fields,
                privacy_report=self._reports.get(conversation.document_id),
                audit_events=self._events.list_for_conversation(conversation.id),
                processing_mode=existing.processing_mode,
            )
        except ValueError:
            return False

        self._summaries.save(conversation.id, summary)
        return True
