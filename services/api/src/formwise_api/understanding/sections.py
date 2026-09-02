import re

from formwise_api.understanding.models import StructuredSection


class RuleBasedSectionDetector:
    _heading = re.compile(r"(?m)^(?:\d+(?:\.\d+)*[.)]\s*)?([A-Z][A-Z &/,-]{3,}|[A-Z][A-Za-z &/,-]{3,}:)\s*$")

    def detect(self, text: str) -> list[StructuredSection]:
        matches = list(self._heading.finditer(text))
        sections: list[StructuredSection] = []
        for index, match in enumerate(matches):
            title = match.group(1).rstrip(":").strip().title()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append(StructuredSection(id=f"section-{index + 1}", title=title, start=match.start(), end=end))
        return sections
