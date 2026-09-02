from datetime import UTC, datetime
from typing import Any, Protocol

from formwise_api.rendering.models import RenderRecord


class RenderRepository(Protocol):
    def create(self, record: RenderRecord) -> None: ...
    def get(self, render_id: str) -> RenderRecord | None: ...
    def list_for_document(self, document_id: str) -> list[RenderRecord]: ...
    def latest_for_document(self, document_id: str) -> RenderRecord | None: ...
    def update(self, render_id: str, updates: dict[str, Any]) -> RenderRecord | None: ...
    def update_status(self, render_id: str, status: str, **metadata: Any) -> RenderRecord | None: ...


class FirestoreRenderRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, record: RenderRecord) -> None:
        self._client.collection("render_records").document(record.id).create(record.model_dump(by_alias=True, mode="python"))

    def save(self, record: RenderRecord) -> None:
        self.create(record)

    def get(self, render_id: str) -> RenderRecord | None:
        snapshot = self._client.collection("render_records").document(render_id).get()
        return RenderRecord.model_validate(snapshot.to_dict() or {}) if snapshot.exists else None

    def list_for_document(self, document_id: str) -> list[RenderRecord]:
        query = self._client.collection("render_records").where("documentId", "==", document_id).order_by("startedAt", direction="DESCENDING")
        return [RenderRecord.model_validate(snapshot.to_dict() or {}) for snapshot in query.stream()]

    def latest_for_document(self, document_id: str) -> RenderRecord | None:
        records = self.list_for_document(document_id)
        return records[0] if records else None

    def update(self, render_id: str, updates: dict[str, Any]) -> RenderRecord | None:
        reference = self._client.collection("render_records").document(render_id)
        snapshot = reference.get()
        if not snapshot.exists:
            return None
        safe_updates = {key: value for key, value in updates.items() if key in {"renderStatus", "validationResult", "pageCount", "previewKey", "outputKey", "startedAt", "completedAt", "renderVersion"}}
        reference.update(safe_updates)
        data = snapshot.to_dict() or {}
        data.update(safe_updates)
        return RenderRecord.model_validate(data)

    def update_status(self, render_id: str, status: str, **metadata: Any) -> RenderRecord | None:
        updates = {"renderStatus": status, **metadata}
        if status in {"completed", "failed"} and "completedAt" not in updates:
            updates["completedAt"] = datetime.now(UTC)
        return self.update(render_id, updates)
