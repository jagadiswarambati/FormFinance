"""API-side retention revocation and durable purge-job enqueueing."""

from datetime import UTC, datetime

from formwise_document_core.retention_models import RetentionJob, RetentionState

from formwise_api.conversations.models import Conversation
from formwise_api.conversations.repository import ConversationRepository
from formwise_api.observability import current_request_id
from formwise_api.retention.repository import (
    RetainedConversationSelector,
    RetentionJobRepository,
    RetentionStateRepository,
)


class RetentionOrchestrator:
    """Revokes access and queues idempotent conversation-purge jobs."""

    def __init__(
        self,
        conversations: ConversationRepository,
        states: RetentionStateRepository,
        jobs: RetentionJobRepository,
        selector: RetainedConversationSelector,
    ) -> None:
        self._conversations = conversations
        self._states = states
        self._jobs = jobs
        self._selector = selector

    def enforce_quota(self, user_id: str, maximum: int = 5) -> RetentionJob | None:
        if self._selector.retained_count(user_id) <= maximum:
            return None
        conversation_id = self._selector.oldest_retained_conversation_id(user_id)
        if conversation_id is None:
            return None
        conversation = self._conversations.get_for_owner(conversation_id, user_id)
        return self.revoke_and_enqueue(conversation) if conversation is not None else None

    def revoke_and_enqueue(self, conversation: Conversation) -> RetentionJob:
        self._conversations.revoke(conversation.id)
        job_id = f"retention-{conversation.id}"
        existing_job = self._jobs.get(job_id)
        existing_state = self._states.get(conversation.id)
        if existing_job is not None:
            if existing_state is None:
                self._states.save(self._queued_state(conversation.id, datetime.now(UTC)))
            return existing_job

        now = datetime.now(UTC)
        self._states.save(self._revoked_state(conversation.id, existing_state, now))
        job = RetentionJob(
            job_id=job_id,
            conversation_id=conversation.id,
            created_at=now,
            status="queued",
            retry_count=0,
            request_id=current_request_id(),
        )
        self._states.save(self._queued_state(conversation.id, now, existing_state))
        self._jobs.enqueue(job)
        return job

    @staticmethod
    def _revoked_state(
        conversation_id: str,
        existing: RetentionState | None,
        now: datetime,
    ) -> RetentionState:
        return RetentionState(
            conversation_id=conversation_id,
            state="revoked",
            revoked_at=existing.revoked_at if existing and existing.revoked_at else now,
            queued_at=existing.queued_at if existing else None,
            started_at=existing.started_at if existing else None,
            completed_at=existing.completed_at if existing else None,
            failure_count=existing.failure_count if existing else 0,
            last_failure_at=existing.last_failure_at if existing else None,
        )

    @classmethod
    def _queued_state(
        cls,
        conversation_id: str,
        now: datetime,
        existing: RetentionState | None = None,
    ) -> RetentionState:
        revoked = cls._revoked_state(conversation_id, existing, now)
        return RetentionState(
            conversation_id=conversation_id,
            state="queued",
            revoked_at=revoked.revoked_at,
            queued_at=existing.queued_at if existing and existing.queued_at else now,
            started_at=existing.started_at if existing else None,
            completed_at=existing.completed_at if existing else None,
            failure_count=existing.failure_count if existing else 0,
            last_failure_at=existing.last_failure_at if existing else None,
        )
