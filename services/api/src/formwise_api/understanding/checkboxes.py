import re

from formwise_api.understanding.models import CheckState, StructuredCheckbox, StructuredSection


class MarkupCheckboxDetector:
    _checkbox = re.compile(r"(?m)^\s*(\[x\]|\[X\]|\[ \]|\[-\])\s*(.+?)\s*$")

    def detect(self, text: str, sections: list[StructuredSection]) -> list[StructuredCheckbox]:
        checkboxes: list[StructuredCheckbox] = []
        for index, match in enumerate(self._checkbox.finditer(text)):
            token = match.group(1).lower()
            state: CheckState = "checked" if token == "[x]" else "unchecked" if token == "[ ]" else "unknown"
            section_id = next((section.id for section in sections if section.start <= match.start() < section.end), None)
            checkboxes.append(StructuredCheckbox(id=f"checkbox-{index + 1}", label=match.group(2).strip(), state=state, section_id=section_id, confidence=0.9))
        return checkboxes
