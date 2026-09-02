from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import UTC, datetime
from typing import Any, Protocol

import structlog

logger = structlog.get_logger()


class RenderJobRepository(Protocol):
    def claim_next(self) -> dict[str, Any] | None: ...
    def update(self, job_id: str, status: str, **details: Any) -> None: ...


class FirestoreRenderWorker:
    """Durable render-job lifecycle; rendering dependencies are injected by composition root."""
    def __init__(self, jobs: RenderJobRepository, service: Any, field_maps: Any, assignments: Any, documents: Any, timeout_seconds: float, max_attempts: int = 3, retry_backoff_seconds: float = 2.0, retry_backoff_max_seconds: float = 60.0, reporter: Any | None = None) -> None:
        self._jobs, self._service, self._field_maps, self._assignments, self._documents, self._timeout, self._max_attempts = jobs, service, field_maps, assignments, documents, timeout_seconds, max_attempts
        self._retry_backoff, self._retry_backoff_max, self._reporter = retry_backoff_seconds, retry_backoff_max_seconds, reporter

    def process_once(self) -> bool:
        job = self._jobs.claim_next()
        if job is None:
            return False
        structlog.contextvars.clear_contextvars()
        request_id = job.get("requestId")
        if isinstance(request_id, str):
            structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            job_id = str(job["id"])
            attempt = int(job.get("attempt", 1))
            execution_token = f"{job_id}:{attempt}"
            if job.get("cancelled"):
                self._jobs.update(job_id, "cancelled", completedAt=datetime.now(UTC))
                return True
            self._jobs.update(job_id, "processing", executionToken=execution_token, startedAt=datetime.now(UTC))
            try:
                document_id = str(job["documentId"])
                document = self._documents.get(document_id)
                field_map = self._field_maps.get(document_id)
                assignments = self._assignments.approved_for_document(document_id)
                if document is None or field_map is None:
                    raise ValueError("RENDER_INPUT_NOT_FOUND")
                executor = ThreadPoolExecutor(max_workers=1)
                future = executor.submit(self._service.render, document_id, str(document["contentType"]), field_map, assignments, str(job.get("renderId", job_id)), execution_token)
                try:
                    result = future.result(timeout=self._timeout)
                except FutureTimeoutError as error:
                    future.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
                    logger.warning("render_job_timeout", job_id=job_id, timeout_seconds=self._timeout)
                    raise TimeoutError("RENDER_TIMEOUT") from error
                else:
                    executor.shutdown(wait=True)
                if result.error_code in {"RENDER_IO_FAILURE", "REPOSITORY_FAILURE"}:
                    self._retry_or_fail(job, result.error_code)
                    return True
                status = "completed" if result.error_code is None else "failed"
                self._jobs.update(job_id, status, renderId=result.record.id, errorCode=result.error_code, completedAt=datetime.now(UTC))
                logger.info("render_job_finished", job_id=job_id, status=status)
            except TimeoutError:
                self._retry_or_fail(job, "WORKER_TIMEOUT")
            except (OSError, ValueError) as error:
                self._retry_or_fail(job, type(error).__name__)
            return True
        finally:
            structlog.contextvars.clear_contextvars()

    def _retry_or_fail(self, job: dict[str, Any], error_code: str) -> None:
        from formwise_worker.operations import retry_at

        job_id = str(job["id"])
        attempt = int(job.get("attempt", 1))
        status = "queued" if attempt < self._max_attempts else "failed"
        self._jobs.update(job_id, status, errorCode=error_code, completedAt=datetime.now(UTC) if status == "failed" else None, nextAttemptAt=retry_at(attempt, self._retry_backoff, self._retry_backoff_max) if status == "queued" else None)
        if status == "failed" and self._reporter is not None:
            request_id = job.get("requestId") if isinstance(job.get("requestId"), str) else None
            self._reporter.dead_letter(queue="render", job_id=job_id, attempt=attempt, error_code=error_code, request_id=request_id)
        logger.warning("render_job_failure", job_id=job_id, status=status, error_code=error_code)
