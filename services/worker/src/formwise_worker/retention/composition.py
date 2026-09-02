"""Worker composition root for retention purge processing."""

from typing import Any

from formwise_worker.config import WorkerSettings
from formwise_worker.operations import FirestoreOperationalReporter
from formwise_worker.retention.audit import FirestoreRetentionAuditRecorder
from formwise_worker.retention.jobs import FirestoreRetentionJobRepository
from formwise_worker.retention.purge import FirestoreRetentionPurgeAdapter
from formwise_worker.retention.worker import FirestoreRetentionWorker


def build_retention_worker(client: Any, settings: WorkerSettings) -> FirestoreRetentionWorker:
    return FirestoreRetentionWorker(
        FirestoreRetentionJobRepository(client),
        FirestoreRetentionPurgeAdapter(
            client,
            settings.local_storage_path,
            settings.quarantine_storage_path,
            settings.ocr_result_storage_path,
            settings.privacy_result_storage_path,
            settings.render_output_storage_path,
        ),
        FirestoreRetentionAuditRecorder(client),
        max_attempts=settings.worker_max_attempts,
        timeout_seconds=settings.retention_timeout_seconds,
        retry_backoff_seconds=settings.worker_retry_backoff_seconds,
        retry_backoff_max_seconds=settings.worker_retry_backoff_max_seconds,
        reporter=FirestoreOperationalReporter(client, settings.worker_instance_id),
    )
