from pathlib import Path
from typing import Protocol


class DocumentRenderer(Protocol):
    name: str
    def render(self, original: Path, output: Path, field_map: list[dict[str, object]], assignments: list[dict[str, object]]) -> tuple[int, list[str]]: ...
