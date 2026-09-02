from collections.abc import AsyncIterable
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, status

from formwise_api.storage.interfaces import StoredObject


@dataclass(frozen=True)
class LocalStoredObject:
    content_type: str
    file_size: int


class LocalStorageAdapter:
    def __init__(self, directory: str, quarantine_directory: str) -> None:
        self._directory = Path(directory)
        self._quarantine_directory = Path(quarantine_directory)

    async def write_upload(self, stored_filename: str, content_type: str, content: AsyncIterable[bytes], maximum_size: int) -> StoredObject:
        self._quarantine_directory.mkdir(parents=True, exist_ok=True)
        target = self._quarantine_directory / stored_filename
        if target.exists():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A document with this storage name already exists.")
        total = 0
        try:
            with target.open("xb") as handle:
                async for chunk in content:
                    total += len(chunk)
                    if total > maximum_size:
                        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Files must not exceed 10 MB.")
                    handle.write(chunk)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return LocalStoredObject(content_type=content_type, file_size=total)

    def inspect(self, stored_filename: str) -> StoredObject | None:
        target = self._quarantine_directory / stored_filename
        if not target.is_file():
            return None
        return LocalStoredObject(content_type="", file_size=target.stat().st_size)

    def release_quarantined(self, stored_filename: str) -> bool:
        source = self._quarantine_directory / stored_filename
        target = self._directory / stored_filename
        if not source.is_file() or target.exists():
            return False
        self._directory.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        return True

    def delete(self, stored_filename: str) -> None:
        (self._directory / stored_filename).unlink(missing_ok=True)
        (self._quarantine_directory / stored_filename).unlink(missing_ok=True)
