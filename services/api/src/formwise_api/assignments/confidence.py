from formwise_api.assignments.models import AssignmentSource


class ConfidenceCalculator:
    _scores: dict[AssignmentSource, float] = {"conversation": 0.99, "previous_approved_answer": 0.99, "structured_document": 0.95, "document_metadata": 0.8, "system_generated": 0.45, "unknown": 0.0}

    def score(self, source: AssignmentSource, valid: bool) -> float:
        return self._scores[source] if valid else min(self._scores[source], 0.45)
