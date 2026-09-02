"""Concrete retention purge adapters; worker orchestration remains deletion-agnostic."""

from pathlib import Path
from typing import Any, Protocol

from google.cloud.firestore_v1.base_query import FieldFilter


class RetentionPurgeAdapter(Protocol):
    def purge(self, conversation_id: str, retention_audit_prefix: str) -> None: ...


class FirestoreRetentionPurgeAdapter:
    def __init__(
        self,
        client: Any,
        uploads_path: str,
        quarantine_path: str,
        ocr_path: str,
        privacy_path: str,
        render_path: str,
    ) -> None:
        self._client = client
        self._uploads = Path(uploads_path)
        self._quarantine = Path(quarantine_path)
        self._ocr = Path(ocr_path)
        self._privacy = Path(privacy_path)
        self._renders = Path(render_path)

    def purge(self, conversation_id: str, retention_audit_prefix: str) -> None:
        conversation_reference = self._client.collection("conversations").document(conversation_id)
        conversation_snapshot = conversation_reference.get()
        if not conversation_snapshot.exists:
            return
        conversation = conversation_snapshot.to_dict() or {}
        document_id = conversation.get("documentId")
        if not isinstance(document_id, str):
            raise ValueError("RETENTION_DOCUMENT_ID_MISSING")

        document_reference = self._client.collection("documents").document(document_id)
        document_snapshot = document_reference.get()
        document = document_snapshot.to_dict() or {} if document_snapshot.exists else {}

        artifact_references = [
            (document.get("storedFilename"), self._uploads),
            (document.get("storedFilename"), self._quarantine),
            (document.get("ocrTextStorageKey"), self._ocr),
            (document.get("ocrLayoutStorageKey"), self._ocr),
            (document.get("redactedTextStorageKey"), self._privacy),
            (document.get("protectedLayoutStorageKey"), self._privacy),
        ]
        artifact_references.extend(self._render_artifact_references(document_id))
        errors: list[OSError] = []
        for value, root in artifact_references:
            self._delete_scoped(value, root, errors)
        if errors:
            raise OSError("RETENTION_ARTIFACT_DELETE_FAILED")
        if not self._artifacts_absent(artifact_references):
            raise OSError("RETENTION_ARTIFACT_VERIFICATION_FAILED")

        self._delete_where("field_assignments", "documentId", document_id)
        self._delete_where("render_records", "documentId", document_id)
        self._delete_where("render_jobs", "documentId", document_id)
        self._delete_where("messages", "conversationId", conversation_id)
        self._delete_where("fieldAnswers", "conversationId", conversation_id)
        self._delete_where("renderedOutputs", "conversationId", conversation_id)
        self._delete_audit_events(conversation_id, retention_audit_prefix)
        self._client.collection("structured_documents").document(document_id).delete()
        self._client.collection("privacy_reports").document(document_id).delete()
        self._client.collection("ocr_jobs").document(document_id).delete()
        document_reference.delete()
        conversation_reference.delete()
        if not self._verify_completed(document_id, conversation_id, retention_audit_prefix):
            raise OSError("RETENTION_PURGE_VERIFICATION_FAILED")

    def _render_artifact_references(self, document_id: str) -> list[tuple[object, Path]]:
        references: list[tuple[object, Path]] = []
        for snapshot in self._client.collection("render_records").where(
            filter=FieldFilter("documentId", "==", document_id)
        ).stream():
            record = snapshot.to_dict() or {}
            references.extend(
                (
                    (record.get("outputKey"), self._renders),
                    (record.get("previewKey"), self._renders),
                )
            )
        return references

    @staticmethod
    def _delete_scoped(value: object, root: Path, errors: list[OSError]) -> None:
        target = FirestoreRetentionPurgeAdapter._scoped_target(value, root)
        if target is None or not target.exists():
            return
        try:
            target.unlink()
        except OSError as error:
            errors.append(error)

    @staticmethod
    def _scoped_target(value: object, root: Path) -> Path | None:
        if not isinstance(value, str):
            return None
        requested = Path(value)
        root_path = root.resolve()
        target = requested.resolve()
        if not target.is_relative_to(root_path):
            target = (root_path / requested).resolve()
        return target if target.is_relative_to(root_path) else None

    @classmethod
    def _artifacts_absent(cls, references: list[tuple[object, Path]]) -> bool:
        return all(
            (target := cls._scoped_target(value, root)) is None or not target.exists()
            for value, root in references
        )

    def _delete_where(self, collection: str, field: str, value: str) -> None:
        for snapshot in self._client.collection(collection).where(
            filter=FieldFilter(field, "==", value)
        ).stream():
            snapshot.reference.delete()

    def _delete_audit_events(self, conversation_id: str, retention_audit_prefix: str) -> None:
        for snapshot in self._client.collection("auditEvents").where(
            filter=FieldFilter("conversationId", "==", conversation_id)
        ).stream():
            if not snapshot.id.startswith(retention_audit_prefix):
                snapshot.reference.delete()

    def _verify_completed(
        self,
        document_id: str,
        conversation_id: str,
        retention_audit_prefix: str,
    ) -> bool:
        direct_documents = (
            ("documents", document_id),
            ("structured_documents", document_id),
            ("privacy_reports", document_id),
            ("ocr_jobs", document_id),
            ("conversations", conversation_id),
        )
        if any(
            self._client.collection(name).document(identifier).get().exists
            for name, identifier in direct_documents
        ):
            return False
        scoped_resources = (
            ("field_assignments", "documentId", document_id),
            ("render_records", "documentId", document_id),
            ("render_jobs", "documentId", document_id),
            ("messages", "conversationId", conversation_id),
            ("fieldAnswers", "conversationId", conversation_id),
            ("renderedOutputs", "conversationId", conversation_id),
        )
        if any(
            next(
                iter(
                    self._client.collection(name)
                    .where(filter=FieldFilter(field, "==", value))
                    .limit(1)
                    .stream()
                ),
                None,
            )
            is not None
            for name, field, value in scoped_resources
        ):
            return False
        return all(
            snapshot.id.startswith(retention_audit_prefix)
            for snapshot in self._client.collection("auditEvents")
            .where(filter=FieldFilter("conversationId", "==", conversation_id))
            .stream()
        )
