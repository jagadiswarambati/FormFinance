from datetime import UTC, datetime
from typing import Any, Protocol

from formwise_api.assignments.models import FieldAssignment


class AssignmentRepository(Protocol):
    def list_for_document(self, document_id: str) -> list[FieldAssignment]: ...
    def replace_for_document(self, document_id: str, assignments: list[FieldAssignment]) -> None: ...
    def get(self, assignment_id: str) -> FieldAssignment | None: ...
    def update(self, assignment_id: str, updates: dict[str, Any]) -> FieldAssignment | None: ...


class FirestoreAssignmentRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def list_for_document(self, document_id: str) -> list[FieldAssignment]:
        return [FieldAssignment.model_validate(snapshot.to_dict() or {}) for snapshot in self._client.collection("field_assignments").where("documentId", "==", document_id).order_by("createdAt").stream()]

    def replace_for_document(self, document_id: str, assignments: list[FieldAssignment]) -> None:
        for snapshot in self._client.collection("field_assignments").where("documentId", "==", document_id).stream():
            snapshot.reference.delete()
        for assignment in assignments:
            self._client.collection("field_assignments").document(assignment.id).create(assignment.model_dump(by_alias=True, mode="python"))

    def get(self, assignment_id: str) -> FieldAssignment | None:
        snapshot = self._client.collection("field_assignments").document(assignment_id).get()
        return FieldAssignment.model_validate(snapshot.to_dict() or {}) if snapshot.exists else None

    def update(self, assignment_id: str, updates: dict[str, Any]) -> FieldAssignment | None:
        reference = self._client.collection("field_assignments").document(assignment_id)
        snapshot = reference.get()
        if not snapshot.exists:
            return None
        updates["updatedAt"] = datetime.now(UTC)
        reference.update(updates)
        data = snapshot.to_dict() or {}
        data.update(updates)
        return FieldAssignment.model_validate(data)
