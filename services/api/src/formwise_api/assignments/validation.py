import re

from formwise_api.understanding.models import StructuredField


class FieldValidationEngine:
    def validate(self, field: StructuredField, value: str) -> bool:
        label = field.label.lower()
        if "email" in label:
            return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value))
        if "phone" in label:
            return bool(re.fullmatch(r"\+?\d{10,15}", re.sub(r"[\s()-]", "", value)))
        if any(token in label for token in ("date", "dob")):
            return bool(re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", value))
        if "pin" in label or "postal" in label:
            return bool(re.fullmatch(r"\d{5,6}", value))
        if "currency" in label or "amount" in label:
            return bool(re.fullmatch(r"[₹$€]?\s?\d+(?:[,.]\d{1,2})?", value))
        return bool(value.strip())
