from formwise_api.understanding.models import MissingField, StructuredField


class RequiredFieldAnalyzer:
    def analyze(self, fields: list[StructuredField]) -> list[MissingField]:
        missing: list[MissingField] = []
        for field in fields:
            if field.required and not field.value:
                missing.append(MissingField(field_id=field.id, label=field.label, certainty="missing", confidence=field.confidence))
            elif not field.value:
                missing.append(MissingField(field_id=field.id, label=field.label, certainty="potentially_missing", confidence=field.confidence))
        return missing
