from pathlib import Path

from fastapi import HTTPException, status

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def validate_document_metadata(filename: str, content_type: str, file_size: int) -> tuple[str, str]:
    basename = Path(filename).name
    extension = Path(basename).suffix.lower()
    expected_content_type = ALLOWED_CONTENT_TYPES.get(extension)
    if not expected_content_type:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only PDF, PNG, JPG, and JPEG files are supported.")
    if content_type.lower().split(";", maxsplit=1)[0].strip() != expected_content_type:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The file extension and content type do not match.")
    if file_size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Files must not exceed 10 MB.")
    return basename, extension
