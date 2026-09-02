from formwise_api.understanding.models import StructuredField


class QuestionGenerator:
    def question_for(self, field: StructuredField) -> str:
        return f"What is the value for {field.label}? (Field {field.id})"
