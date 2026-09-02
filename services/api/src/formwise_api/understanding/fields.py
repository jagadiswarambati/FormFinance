import re

from formwise_api.privacy.field_policy import FieldPrivacyPolicy
from formwise_api.understanding.models import (
    BoundingRegion,
    FieldRenderMetadata,
    StructuredField,
    StructuredSection,
)


class RuleBasedFieldExtractor:
    _field = re.compile(r"(?m)^\s*([A-Za-z][A-Za-z0-9 ()/&.-]{1,80}?)(\*)?\s*:\s*(.*?)\s*$")

    def extract(self, text: str, sections: list[StructuredSection]) -> list[StructuredField]:
        fields: list[StructuredField] = []
        for index, match in enumerate(self._field.finditer(text)):
            label, required, value = match.group(1).strip(), bool(match.group(2)), match.group(3).strip()
            section_id = next((section.id for section in sections if section.start <= match.start() < section.end), None)
            field = StructuredField(id=f"field-{index + 1}", label=label, value=value or None, section_id=section_id, confidence=0.9 if value else 0.75, region=BoundingRegion(start=match.start(), end=match.end()), required=required)
            tier = FieldPrivacyPolicy().classify(field)
            reason = "Approved safe field" if tier == "safe" else "Protected by Privacy Policy"
            fields.append(field.model_copy(update={"render_metadata": FieldRenderMetadata(privacy_tier=tier, privacy_reason=reason)}))
        return fields
