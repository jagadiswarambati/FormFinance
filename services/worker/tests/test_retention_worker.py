from datetime import UTC, datetime

from formwise_document_core.retention_models import RetentionJob

from formwise_worker.retention.worker import FirestoreRetentionWorker


class _Jobs:
    def __init__(self, job: RetentionJob) -> None:
        self.job = job
        self.requeues: list[tuple[int, datetime]] = []
        self.failed = 0

    def next_queued(self) -> RetentionJob | None:
        return self.job

    def mark_processing(self, job: RetentionJob) -> RetentionJob:
        return job.model_copy(update={"status": "processing"})

    def mark_completed(self, _: RetentionJob) -> RetentionJob:
        raise AssertionError("failure must not be marked completed")

    def requeue_after_failure(self, _: RetentionJob, retry_count: int, next_attempt_at: datetime) -> RetentionJob:
        self.requeues.append((retry_count, next_attempt_at))
        return self.job

    def mark_failed(self, _: RetentionJob, retry_count: int) -> RetentionJob:
        self.failed += 1
        return self.job


class _Purger:
    def purge(self, *_: object) -> None:
        raise OSError("temporary storage failure")


class _Audits:
    def policy_version_for_conversation(self, _: str) -> str:
        return "v1"

    def append_once(self, **_: object) -> None:
        return None


def test_retention_worker_requeues_transient_failure_with_a_future_retry_time() -> None:
    job = RetentionJob(
        job_id="job-1",
        conversation_id="conversation-1",
        created_at=datetime.now(UTC),
        status="queued",
    )
    jobs = _Jobs(job)

    assert FirestoreRetentionWorker(jobs, _Purger(), _Audits()).process_once()
    assert jobs.failed == 0
    assert jobs.requeues[0][0] == 1
    assert jobs.requeues[0][1] > datetime.now(UTC)
