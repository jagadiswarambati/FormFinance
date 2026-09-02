"""Durable worker orchestration for queued retention jobs."""

from datetime import UTC, datetime
from typing import Protocol

import structlog
from formwise_document_core.retention_models import RetentionJob

from formwise_worker.operations import (
    FirestoreOperationalReporter,
    WorkerOperationTimeout,
    retry_at,
    run_with_timeout,
)
from formwise_worker.retention.audit import FirestoreRetentionAuditRecorder
from formwise_worker.retention.purge import RetentionPurgeAdapter

logger = structlog.get_logger()


class RetentionJobQueue(Protocol):
    def next_queued(self) -> RetentionJob | None: ...
    def mark_processing(self, job: RetentionJob) -> RetentionJob | None: ...
    def mark_completed(self, job: RetentionJob) -> RetentionJob | None: ...
    def requeue_after_failure(self, job: RetentionJob, retry_count: int, next_attempt_at: datetime) -> RetentionJob | None: ...
    def mark_failed(self, job: RetentionJob, retry_count: int) -> RetentionJob | None: ...


class FirestoreRetentionWorker:
    def __init__(
        self,
        jobs: RetentionJobQueue,
        purger: RetentionPurgeAdapter,
        audits: FirestoreRetentionAuditRecorder,
        max_attempts: int = 3,
        timeout_seconds: float = 120.0,
        retry_backoff_seconds: float = 2.0,
        retry_backoff_max_seconds: float = 60.0,
        reporter: FirestoreOperationalReporter | None = None,
    ) -> None:
        self._jobs = jobs
        self._purger = purger
        self._audits = audits
        self._max_attempts = max_attempts
        self._timeout = timeout_seconds
        self._retry_backoff = retry_backoff_seconds
        self._retry_backoff_max = retry_backoff_max_seconds
        self._reporter = reporter

    def process_once(self) -> bool:
        job = self._jobs.next_queued()
        if job is None:
            return False
        structlog.contextvars.clear_contextvars()
        if job.request_id is not None:
            structlog.contextvars.bind_contextvars(request_id=job.request_id)
        try:
            processing = self._jobs.mark_processing(job)
            if processing is None:
                return True
            policy_version: str | None = None
            audit_prefix: str | None = None
            try:
                policy_version = self._audits.policy_version_for_conversation(processing.conversation_id)
                if policy_version is None:
                    raise ValueError("RETENTION_POLICY_VERSION_UNAVAILABLE")
                audit_prefix = f"retention-{processing.job_id}-"
                self._audits.append_once(
                    event_id=f"{audit_prefix}queued",
                    conversation_id=processing.conversation_id,
                    event_type="retention_queued",
                    policy_version=policy_version,
                    timestamp=datetime.now(UTC),
                    explanation_key="retention.purge.queued",
                )
                self._audits.append_once(
                    event_id=f"{audit_prefix}processing-{processing.retry_count}",
                    conversation_id=processing.conversation_id,
                    event_type="retention_processing",
                    policy_version=policy_version,
                    timestamp=datetime.now(UTC),
                    explanation_key="retention.purge.processing",
                )
                run_with_timeout(
                    lambda: self._purger.purge(processing.conversation_id, audit_prefix),
                    self._timeout,
                )
                self._audits.append_once(
                    event_id=f"{audit_prefix}completed",
                    conversation_id=processing.conversation_id,
                    event_type="retention_completed",
                    policy_version=policy_version,
                    timestamp=datetime.now(UTC),
                    explanation_key="retention.purge.completed",
                )
                if self._jobs.mark_completed(processing) is None:
                    raise RuntimeError("RETENTION_JOB_MISSING")
            except WorkerOperationTimeout as error:
                return self._handle_failure(processing, error, policy_version, audit_prefix, "WORKER_TIMEOUT")
            except Exception as error:
                return self._handle_failure(processing, error, policy_version, audit_prefix)
            logger.info("retention_purge_completed", job_id=processing.job_id)
            return True
        finally:
            structlog.contextvars.clear_contextvars()

    def _handle_failure(
        self,
        job: RetentionJob,
        error: Exception,
        policy_version: str | None = None,
        audit_prefix: str | None = None,
        error_code: str | None = None,
    ) -> bool:
        retry_count = job.retry_count + 1
        if policy_version is not None and audit_prefix is not None:
            try:
                self._audits.append_once(
                    event_id=f"{audit_prefix}failed-{retry_count}",
                    conversation_id=job.conversation_id,
                    event_type="retention_failed",
                    policy_version=policy_version,
                    timestamp=datetime.now(UTC),
                    explanation_key="retention.purge.failed",
                )
            except Exception as audit_error:
                logger.warning(
                    "retention_purge_failure_audit_unavailable",
                    job_id=job.job_id,
                    error_type=type(audit_error).__name__,
                )
        if retry_count < self._max_attempts:
            self._jobs.requeue_after_failure(
                job,
                retry_count,
                retry_at(retry_count, self._retry_backoff, self._retry_backoff_max),
            )
            logger.warning(
                "retention_purge_retry_queued",
                job_id=job.job_id,
                retry_count=retry_count,
                error_type=type(error).__name__,
            )
        else:
            self._jobs.mark_failed(job, retry_count)
            if self._reporter is not None:
                self._reporter.dead_letter(
                    queue="retention",
                    job_id=job.job_id,
                    attempt=retry_count,
                    error_code=error_code or type(error).__name__,
                    request_id=job.request_id,
                )
            logger.warning(
                "retention_purge_failed",
                job_id=job.job_id,
                retry_count=retry_count,
                error_type=type(error).__name__,
            )
        return True
