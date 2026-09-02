from typing import Any

from formwise_document_core.rendering_models import RenderRecord
from formwise_document_core.rendering_service import RenderService
from formwise_document_core.rendering_validator import RenderValidator
from google.cloud.firestore_v1.base_query import FieldFilter

from formwise_worker.config import WorkerSettings
from formwise_worker.operations import FirestoreOperationalReporter
from formwise_worker.rendering.artifacts import LocalRenderArtifactStore
from formwise_worker.rendering.factory import RendererFactory
from formwise_worker.rendering.jobs import FirestoreRenderJobRepository
from formwise_worker.rendering.worker import FirestoreRenderWorker


class WorkerFirestoreRenderRecordRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def save(self, record: RenderRecord) -> None:
        self._client.collection("render_records").document(record.id).set(record.model_dump(by_alias=True, mode="python"))

    def is_active_execution(self, render_id: str, execution_token: str) -> bool:
        snapshot = self._client.collection("render_jobs").document(render_id).get()
        data = snapshot.to_dict() or {}
        return snapshot.exists and data.get("status") == "processing" and data.get("executionToken") == execution_token


class _Inputs:
    def __init__(self, client: Any) -> None: self._client = client
    def get(self, document_id: str) -> dict[str, Any] | None:
        snapshot = self._client.collection("documents").document(document_id).get()
        return snapshot.to_dict() if snapshot.exists else None


class _FieldMaps:
    def __init__(self, client: Any) -> None: self._client = client
    def get(self, document_id: str) -> list[dict[str, Any]] | None:
        snapshot = self._client.collection("structured_documents").document(document_id).get()
        data = snapshot.to_dict() if snapshot.exists else None
        return data.get("fields") if isinstance(data, dict) and isinstance(data.get("fields"), list) else None


class _Assignments:
    def __init__(self, client: Any) -> None: self._client = client
    def approved_for_document(self, document_id: str) -> list[dict[str, Any]]:
        query = self._client.collection("field_assignments").where(
            filter=FieldFilter("documentId", "==", document_id)
        ).where(filter=FieldFilter("status", "==", "approved"))
        return [item.to_dict() or {} for item in query.stream()]


def build_render_worker(client: Any, settings: WorkerSettings) -> FirestoreRenderWorker:
    records = WorkerFirestoreRenderRecordRepository(client)
    service = RenderService(RenderValidator(), RendererFactory(), LocalRenderArtifactStore(settings.local_storage_path, settings.render_output_storage_path), records, settings.render_coordinate_confidence_threshold)
    return FirestoreRenderWorker(
        FirestoreRenderJobRepository(client),
        service,
        _FieldMaps(client),
        _Assignments(client),
        _Inputs(client),
        settings.render_timeout_seconds,
        settings.worker_max_attempts,
        settings.worker_retry_backoff_seconds,
        settings.worker_retry_backoff_max_seconds,
        FirestoreOperationalReporter(client, settings.worker_instance_id),
    )
