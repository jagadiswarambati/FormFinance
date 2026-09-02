from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from formwise_worker.config import WorkerSettings
from formwise_worker.ocr.factory import get_ocr_provider
from formwise_worker.ocr.quarantine import UnavailableUploadScanner, UploadScanner
from formwise_worker.ocr.store import LocalOcrResultStore
from formwise_worker.operations import (
    FirestoreOperationalReporter,
    WorkerOperationTimeout,
    claim_next_queued_job,
    retry_at,
    run_with_timeout,
)

logger = structlog.get_logger()


class FirestoreOcrWorker:
    def __init__(
        self,
        client: Any,
        settings: WorkerSettings,
        scanner: UploadScanner | None = None,
        reporter: FirestoreOperationalReporter | None = None,
    ) -> None:
        self._client = client
        self._settings = settings
        self._provider = get_ocr_provider(settings.ocr_provider)
        self._results = LocalOcrResultStore(settings.ocr_result_storage_path)
        self._scanner = scanner or UnavailableUploadScanner()
        self._reporter = reporter

    def process_once(self) -> bool:
        claimed = claim_next_queued_job(self._client, "ocr_jobs")
        if claimed is None:
            return False
        job_id, job = claimed
        request_id = job.get("requestId")
        if isinstance(request_id, str):
            structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            return self._process_claimed(job_id, job)
        finally:
            structlog.contextvars.clear_contextvars()

    def _process_claimed(self, job_id: str, job: dict[str, Any]) -> bool:
        document_id = str(job["documentId"])
        job_reference = self._client.collection("ocr_jobs").document(job_id)
        document_reference = self._client.collection("documents").document(document_id)
        try:
            document_snapshot = document_reference.get()
            if not document_snapshot.exists:
                self._retry_or_dead_letter(job_id, job, "DOCUMENT_NOT_FOUND", terminal=True)
                return True
            document = document_snapshot.to_dict() or {}
            if not self._release_clean_upload(document_reference, document, job_id, job):
                return True
            document = document_reference.get().to_dict() or {}
            if not self._is_scan_released(document):
                self._retry_or_dead_letter(job_id, job, "QUARANTINE_GATE_BLOCKED", terminal=True)
                return True
            ocr_started_at = datetime.now(UTC)
            document_reference.update(
                {
                    "status": "ocr_processing",
                    "ocrStatus": "processing",
                    "ocrStartedAt": ocr_started_at,
                    "ocrCompletedAt": None,
                    "ocrProvider": self._provider.name,
                    "ocrConfidence": None,
                    "textLength": None,
                    "ocrTextStorageKey": None,
                    "ocrLayoutStorageKey": None,
                }
            )
            original_path = Path(self._settings.local_storage_path) / str(document["storedFilename"])
            result = run_with_timeout(
                lambda: self._provider.extract(original_path),
                self._settings.ocr_timeout_seconds,
            )
            storage_key = self._results.write(document_id, result.text)
            layout_key = self._results.write_layout(document_id, result.layout_tokens)
            completed_at = datetime.now(UTC)
            document_reference.update(
                {
                    "status": "ocr_completed",
                    "ocrStatus": "completed",
                    "ocrCompletedAt": completed_at,
                    "ocrProvider": self._provider.name,
                    "ocrConfidence": result.confidence,
                    "textLength": len(result.text),
                    "ocrTextStorageKey": storage_key,
                    "ocrLayoutStorageKey": layout_key,
                }
            )
            job_reference.update({"status": "completed", "completedAt": completed_at})
            logger.info("ocr_completed", document_id=document_id, provider=self._provider.name)
        except WorkerOperationTimeout:
            document_reference.update(
                {"status": "ocr_failed", "ocrStatus": "failed", "ocrCompletedAt": datetime.now(UTC)}
            )
            self._retry_or_dead_letter(job_id, job, "WORKER_TIMEOUT")
        except Exception as error:
            document_reference.update(
                {"status": "ocr_failed", "ocrStatus": "failed", "ocrCompletedAt": datetime.now(UTC)}
            )
            self._retry_or_dead_letter(job_id, job, type(error).__name__)
            logger.warning("ocr_failed", document_id=document_id, error_type=type(error).__name__)
        return True

    def _release_clean_upload(
        self,
        document_reference: Any,
        document: dict[str, Any],
        job_id: str,
        job: dict[str, Any],
    ) -> bool:
        if self._is_scan_released(document):
            return True
        stored_filename = document.get("storedFilename")
        if (
            isinstance(stored_filename, str)
            and document.get("scanStatus") == "scanning"
            and not (Path(self._settings.quarantine_storage_path) / stored_filename).exists()
            and (Path(self._settings.local_storage_path) / stored_filename).is_file()
        ):
            document_reference.update(
                {
                    "status": "uploaded",
                    "quarantineStatus": "released",
                    "scanStatus": "clean",
                    "scanCompletedAt": datetime.now(UTC),
                    "scanReason": None,
                }
            )
            return True
        if document.get("scanStatus") == "blocked" or document.get("quarantineStatus") == "blocked":
            self._retry_or_dead_letter(job_id, job, "QUARANTINE_BLOCKED", terminal=True)
            return False
        if document.get("status") != "quarantined" or document.get("scanStatus") not in {
            "pending",
            "queued",
            "failed",
        }:
            self._record_scan_failure(document_reference, job_id, job, "QUARANTINE_GATE_BLOCKED")
            return False
        started_at = datetime.now(UTC)
        document_reference.update(
            {
                "quarantineStatus": "scanning",
                "scanStatus": "scanning",
                "scanStartedAt": started_at,
                "scanCompletedAt": None,
                "scanReason": None,
            }
        )
        if not isinstance(stored_filename, str):
            self._record_scan_failure(document_reference, job_id, job, "SCAN_SOURCE_MISSING")
            return False
        try:
            result = run_with_timeout(
                lambda: self._scanner.scan(
                    Path(self._settings.quarantine_storage_path) / stored_filename
                ),
                self._settings.ocr_timeout_seconds,
            )
        except WorkerOperationTimeout:
            self._record_scan_failure(document_reference, job_id, job, "WORKER_TIMEOUT")
            return False
        completed_at = datetime.now(UTC)
        if result.outcome != "clean":
            self._record_scan_failure(
                document_reference,
                job_id,
                job,
                result.reason_code or "SCAN_BLOCKED",
                result.provider,
                completed_at,
                result.outcome == "blocked",
            )
            return False
        if not self._release_file(stored_filename):
            self._record_scan_failure(
                document_reference,
                job_id,
                job,
                "QUARANTINE_RELEASE_FAILED",
                result.provider,
                completed_at,
            )
            return False
        document_reference.update(
            {
                "status": "uploaded",
                "quarantineStatus": "released",
                "scanStatus": "clean",
                "scanCompletedAt": completed_at,
                "scanProvider": result.provider,
                "scanReason": None,
            }
        )
        return True

    @staticmethod
    def _is_scan_released(document: dict[str, Any]) -> bool:
        return (
            document.get("quarantineStatus") == "released"
            and document.get("scanStatus") == "clean"
        )

    def _release_file(self, stored_filename: str) -> bool:
        source = Path(self._settings.quarantine_storage_path) / stored_filename
        target = Path(self._settings.local_storage_path) / stored_filename
        if target.is_file() and not source.exists():
            return True
        if not source.is_file() or target.exists():
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        return True

    def _record_scan_failure(
        self,
        document_reference: Any,
        job_id: str,
        job: dict[str, Any],
        reason_code: str,
        provider: str | None = None,
        completed_at: datetime | None = None,
        blocked: bool = False,
    ) -> None:
        finished_at = completed_at or datetime.now(UTC)
        document_reference.update(
            {
                "status": "quarantined",
                "quarantineStatus": "blocked" if blocked else "pending",
                "scanStatus": "blocked" if blocked else "failed",
                "scanCompletedAt": finished_at,
                "scanProvider": provider or self._scanner.provider,
                "scanReason": reason_code,
            }
        )
        self._retry_or_dead_letter(job_id, job, reason_code, terminal=blocked)

    def _retry_or_dead_letter(
        self,
        job_id: str,
        job: dict[str, Any],
        error_code: str,
        *,
        terminal: bool = False,
    ) -> None:
        attempt = int(job.get("attempt", 1))
        request_id = job.get("requestId") if isinstance(job.get("requestId"), str) else None
        if terminal or attempt >= self._settings.worker_max_attempts:
            self._client.collection("ocr_jobs").document(job_id).update(
                {"status": "failed", "completedAt": datetime.now(UTC), "error": error_code}
            )
            if self._reporter is not None:
                self._reporter.dead_letter(
                    queue="ocr",
                    job_id=job_id,
                    attempt=attempt,
                    error_code=error_code,
                    request_id=request_id,
                )
            return
        self._client.collection("ocr_jobs").document(job_id).update(
            {
                "status": "queued",
                "nextAttemptAt": retry_at(
                    attempt,
                    self._settings.worker_retry_backoff_seconds,
                    self._settings.worker_retry_backoff_max_seconds,
                ),
                "error": error_code,
            }
        )
