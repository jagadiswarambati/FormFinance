from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import structlog

from formwise_api.documents.repository import DocumentRepository
from formwise_api.observability import current_request_id

logger = structlog.get_logger()


class OcrJobRepository(Protocol):
    def enqueue(self, document_id: str, owner_uid: str, provider: str) -> None: ...


class FirestoreOcrJobRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def enqueue(self, document_id: str, owner_uid: str, provider: str) -> None:
        self._client.collection("ocr_jobs").document(document_id).set(
            {
                "documentId": document_id,
                "ownerUid": owner_uid,
                "provider": provider,
                "status": "queued",
                "attempt": 0,
                "nextAttemptAt": None,
                "requestId": current_request_id(),
                "createdAt": datetime.now(UTC),
                "startedAt": None,
                "completedAt": None,
            }
        )


class InMemoryOcrJobRepository:
    """Demo-mode OCR job repository.

    There is no background worker process consuming a Firestore queue in pure
    demo mode, so this repository runs the *real* configured OCR provider
    (e.g. PaddleOCR, from `formwise_worker.ocr`) synchronously when a job is
    enqueued, and records the genuine success/failure outcome on the document
    via `DocumentRepository.update_fields`.

    It never fabricates OCR text, confidence, or status - if the real
    provider fails (e.g. model download blocked by network restrictions),
    the document is marked `ocr_status="failed"` just like the Firestore
    worker would do, and the original exception type/message is preserved
    on the in-memory job record for diagnostics.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        local_storage_path: str,
        ocr_result_storage_path: str,
        ocr_timeout_seconds: float = 120.0,
    ) -> None:
        self._document_repo = document_repo
        self._local_storage_path = local_storage_path
        self._ocr_result_storage_path = ocr_result_storage_path
        self._ocr_timeout_seconds = ocr_timeout_seconds
        self._jobs: dict[str, dict[str, Any]] = {}

    def enqueue(self, document_id: str, owner_uid: str, provider: str) -> None:
        # Imported lazily so the api service only pulls in worker OCR/operations
        # code paths when a job is actually run, matching how the rest of the
        # codebase (settlements/processing.py, rendering/router.py) borrows
        # from formwise_worker.
        from formwise_worker.ocr.factory import get_ocr_provider
        from formwise_worker.ocr.store import LocalOcrResultStore
        from formwise_worker.operations import run_with_timeout

        request_id = current_request_id()
        started_at = datetime.now(UTC)
        job_record: dict[str, Any] = {
            "documentId": document_id,
            "ownerUid": owner_uid,
            "provider": provider,
            "status": "processing",
            "attempt": 1,
            "requestId": request_id,
            "createdAt": started_at,
            "startedAt": started_at,
            "completedAt": None,
            "error": None,
        }
        self._jobs[document_id] = job_record

        document = self._document_repo.get_for_owner(document_id, owner_uid)
        if document is None:
            job_record.update({"status": "failed", "error": "DOCUMENT_NOT_FOUND", "completedAt": datetime.now(UTC)})
            logger.warning("ocr_failed", document_id=document_id, error_type="DOCUMENT_NOT_FOUND")
            return

        self._document_repo.update_fields(
            document_id,
            owner_uid,
            {
                "status": "ocr_processing",
                "ocr_status": "processing",
                "ocr_started_at": started_at,
                "ocr_completed_at": None,
                "ocr_provider": provider,
                "ocr_confidence": None,
                "text_length": None,
                "ocr_text_storage_key": None,
                "ocr_layout_storage_key": None,
            },
        )

        try:
            ocr_provider = get_ocr_provider(provider)
            document_path = Path(self._local_storage_path) / document.stored_filename
            result = run_with_timeout(
                lambda: ocr_provider.extract(document_path),
                self._ocr_timeout_seconds,
            )
        except Exception as error:  # mirrors FirestoreOcrWorker's genuine-failure handling (timeouts included)
            completed_at = datetime.now(UTC)
            self._document_repo.update_fields(
                document_id,
                owner_uid,
                {"status": "ocr_failed", "ocr_status": "failed", "ocr_completed_at": completed_at},
            )
            job_record.update(
                {"status": "failed", "error": type(error).__name__, "completedAt": completed_at}
            )
            logger.warning(
                "ocr_failed",
                document_id=document_id,
                provider=provider,
                error_type=type(error).__name__,
            )
            return

        results_store = LocalOcrResultStore(self._ocr_result_storage_path)
        storage_key = results_store.write(document_id, result.text)
        layout_key = results_store.write_layout(document_id, result.layout_tokens)
        completed_at = datetime.now(UTC)
        self._document_repo.update_fields(
            document_id,
            owner_uid,
            {
                "status": "ocr_completed",
                "ocr_status": "completed",
                "ocr_completed_at": completed_at,
                "ocr_provider": provider,
                "ocr_confidence": result.confidence,
                "text_length": len(result.text),
                "ocr_text_storage_key": storage_key,
                "ocr_layout_storage_key": layout_key,
            },
        )
        job_record.update({"status": "completed", "completedAt": completed_at})
        logger.info("ocr_completed", document_id=document_id, provider=provider)
