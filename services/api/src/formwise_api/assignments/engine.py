from datetime import UTC, datetime
from uuid import uuid4

from formwise_api.assignments.confidence import ConfidenceCalculator
from formwise_api.assignments.conflicts import ConflictDetector
from formwise_api.assignments.models import AssignmentEvidence, AssignmentSource, FieldAssignment
from formwise_api.assignments.questions import QuestionGenerator
from formwise_api.assignments.validation import FieldValidationEngine
from formwise_api.conversations.models import ConversationMessage
from formwise_api.privacy.field_policy import FieldPrivacyPolicy
from formwise_api.understanding.models import StructuredDocument, StructuredField


class FieldAssignmentEngine:
    def __init__(self) -> None:
        self._policy = FieldPrivacyPolicy()
        self._confidence = ConfidenceCalculator()
        self._conflicts = ConflictDetector()
        self._questions = QuestionGenerator()
        self._validation = FieldValidationEngine()

    def generate(self, document: StructuredDocument, messages: list[ConversationMessage], previous: list[FieldAssignment]) -> list[FieldAssignment]:
        return [self._assignment(document.document_id, field, messages, previous) for field in document.fields]

    def _assignment(self, document_id: str, field: StructuredField, messages: list[ConversationMessage], previous: list[FieldAssignment]) -> FieldAssignment:
        now = datetime.now(UTC)
        tier = self._policy.classify(field)
        if tier != "safe":
            return FieldAssignment(id=uuid4().hex, document_id=document_id, field_id=field.id, label=field.label, value=None, confidence=1, source="unknown", reason="Protected by Privacy Policy", requires_review=True, status="manual_only", privacy_tier=tier, created_at=now, updated_at=now)
        candidates: list[tuple[str, AssignmentSource, str]] = []
        if field.normalized_value or field.value:
            candidates.append((field.normalized_value or field.value or "", "structured_document", field.id))
        for assignment in previous:
            if assignment.field_id == field.id and assignment.status == "approved" and assignment.value:
                candidates.append((assignment.value, "previous_approved_answer", assignment.id))
        candidates.extend(self._conversation_candidates(field, messages))
        values = [candidate[0] for candidate in candidates]
        if self._conflicts.has_conflict(values):
            return FieldAssignment(id=uuid4().hex, document_id=document_id, field_id=field.id, label=field.label, value=None, confidence=0, source="unknown", reason="Multiple candidate values conflict.", evidence=[AssignmentEvidence(source_id=candidate[2], description=candidate[1]) for candidate in candidates], requires_review=True, status="conflict", privacy_tier=tier, created_at=now, updated_at=now)
        if not candidates:
            return FieldAssignment(id=uuid4().hex, document_id=document_id, field_id=field.id, label=field.label, value=None, confidence=0, source="unknown", reason="No supported value is available.", requires_review=True, status="missing", question=self._questions.question_for(field), privacy_tier=tier, created_at=now, updated_at=now)
        value, source, source_id = candidates[-1]
        valid = self._validation.validate(field, value)
        confidence = self._confidence.score(source, valid)
        return FieldAssignment(id=uuid4().hex, document_id=document_id, field_id=field.id, label=field.label, value=value, confidence=confidence, source=source, reason="Value found in approved safe context." if valid else "Value requires validation review.", evidence=[AssignmentEvidence(source_id=source_id, description=source)], requires_review=not valid or confidence < 0.9, status="pending_review", privacy_tier=tier, created_at=now, updated_at=now)

    @staticmethod
    def _conversation_candidates(field: StructuredField, messages: list[ConversationMessage]) -> list[tuple[str, AssignmentSource, str]]:
        prefix = f"{field.label}:".casefold()
        candidates: list[tuple[str, AssignmentSource, str]] = []
        for message in messages:
            if message.role == "user" and message.safe_content.casefold().startswith(prefix):
                value = message.safe_content[len(field.label) + 1 :].strip()
                if value:
                    candidates.append((value, "conversation", message.id))
        return candidates
