import os
from pathlib import Path
from typing import BinaryIO


class LocalRenderArtifactStore:
    def __init__(self, uploads: str, outputs: str) -> None:
        self._uploads, self._outputs = Path(uploads), Path(outputs)

    def original_path(self, document_id: str) -> Path | None:
        matches = list(self._uploads.glob(f"{document_id}_*"))
        return matches[0] if len(matches) == 1 else None

    def output_path(self, render_id: str, renderer_type: str) -> Path:
        self._outputs.mkdir(parents=True, exist_ok=True)
        suffix = ".pdf" if renderer_type in {"fillable_pdf", "static_pdf"} else ".png"
        return self._outputs / f"{render_id}{suffix}"

    def temporary_output_path(self, render_id: str, execution_token: str, renderer_type: str) -> Path:
        final = self.output_path(render_id, renderer_type)
        return final.with_name(f".{render_id}.{execution_token}.tmp{final.suffix}")

    def promote(self, temporary: Path, final: Path) -> None:
        os.replace(temporary, final)

    def discard(self, temporary: Path) -> None:
        temporary.unlink(missing_ok=True)

    def open_completed_artifact(self, output_key: str) -> BinaryIO | None:
        output_directory = self._outputs.resolve()
        requested = Path(output_key)
        target = requested.resolve()
        if not target.is_relative_to(output_directory):
            target = (output_directory / requested).resolve()
        try:
            target.relative_to(output_directory)
        except ValueError:
            return None
        if not target.is_file():
            return None
        try:
            return target.open("rb")
        except OSError:
            return None
