import re

from formwise_api.understanding.models import StructuredField


class StandardFieldNormalizer:
    def normalize(self, field: StructuredField) -> StructuredField:
        if not field.value:
            return field
        value = " ".join(field.value.split())
        label = field.label.lower()
        if "email" in label:
            value = value.lower()
        elif "phone" in label:
            value = re.sub(r"[^0-9+]", "", value)
        elif any(token in label for token in ("date", "dob", "birth")):
            value = value.replace(".", "/").replace("-", "/")
        return field.model_copy(update={"normalized_value": value})
