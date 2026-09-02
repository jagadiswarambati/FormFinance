from formwise_api.assignments.engine import FieldAssignmentEngine
from formwise_api.assignments.models import AssignmentUpdateRequest, FieldAssignment
from formwise_api.assignments.repository import AssignmentRepository
from formwise_api.assignments.validation import FieldValidationEngine
from formwise_api.conversations.repository import ConversationRepository
from formwise_api.understanding.models import StructuredField
from formwise_api.understanding.repository import UnderstandingRepository


class AssignmentService:
    def __init__(self, assignments: AssignmentRepository, structured_documents: UnderstandingRepository, conversations: ConversationRepository) -> None:
        self._assignments = assignments
        self._structured_documents = structured_documents
        self._conversations = conversations
        self._engine = FieldAssignmentEngine()
        self._validation = FieldValidationEngine()

    def generate(self, user_id: str, document_id: str) -> list[FieldAssignment]:
        document = self._structured_documents.get(document_id)
        if document is None:
            raise ValueError("The document must be structured before assignments can be generated.")
        previous = self._assignments.list_for_document(document_id)
        assignments = self._engine.generate(document, self._conversations.list_messages_for_document(user_id, document_id), previous)
        self._assignments.replace_for_document(document_id, assignments)
        return assignments

    def list(self, document_id: str) -> list[FieldAssignment]:
        return self._assignments.list_for_document(document_id)

    def get(self, assignment_id: str) -> FieldAssignment | None:
        return self._assignments.get(assignment_id)

    def update(self, assignment_id: str, payload: AssignmentUpdateRequest) -> FieldAssignment | None:
        assignment = self._assignments.get(assignment_id)
        if assignment is None:
            return None
        if assignment.privacy_tier != "safe" or assignment.status == "manual_only":
            raise ValueError("Protected fields are manual-only and cannot be edited or approved.")
        if payload.action == "approve":
            return self._assignments.update(assignment_id, {"status": "approved", "requiresReview": False})
        if payload.action == "reject":
            return self._assignments.update(assignment_id, {"status": "rejected", "requiresReview": True})
        if not payload.value:
            raise ValueError("An edited value is required.")
        field = self._field_for_assignment(assignment)
        if field is None or not self._validation.validate(field, payload.value):
            raise ValueError("The edited value did not pass field validation.")
        return self._assignments.update(assignment_id, {"value": payload.value, "source": "conversation", "reason": "Edited by the user and pending review.", "status": "pending_review", "requiresReview": True})

    def _field_for_assignment(self, assignment: FieldAssignment) -> StructuredField | None:
        document = self._structured_documents.get(assignment.document_id)
        return next((field for field in document.fields if field.id == assignment.field_id), None) if document else None
