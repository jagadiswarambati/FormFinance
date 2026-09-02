from typing import Any, Protocol

from formwise_api.evidence.models import EvidenceLink


class EvidenceLinkRepository(Protocol):
    def create(self, link: EvidenceLink) -> str: ...
    def get(self, link_id: str) -> EvidenceLink | None: ...
    def list_for_deduction(self, deduction_id: str) -> list[EvidenceLink]: ...


class FirestoreEvidenceLinkRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, link: EvidenceLink) -> str:
        self._client.collection("evidenceLinks").document(link.id).create(
            link.model_dump(by_alias=True, mode="python")
        )
        return link.id

    def get(self, link_id: str) -> EvidenceLink | None:
        snapshot = self._client.collection("evidenceLinks").document(link_id).get()
        return EvidenceLink.model_validate(snapshot.to_dict() or {}) if snapshot.exists else None

    def list_for_deduction(self, deduction_id: str) -> list[EvidenceLink]:
        return [
            EvidenceLink.model_validate(snapshot.to_dict() or {})
            for snapshot in self._client.collection("evidenceLinks")
            .where("deductionId", "==", deduction_id)
            .order_by("matchedAt")
            .stream()
        ]
