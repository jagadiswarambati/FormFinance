import pytest
from fastapi import HTTPException

from formwise_api.documents.validation import MAX_UPLOAD_BYTES, validate_document_metadata


def test_upload_validation_normalizes_the_filename_and_accepts_matching_metadata() -> None:
    assert validate_document_metadata("../document.PDF", "application/pdf; charset=binary", 10) == (
        "document.PDF",
        ".pdf",
    )


@pytest.mark.parametrize(
    ("filename", "content_type", "size"),
    [
        ("payload.exe", "application/octet-stream", 1),
        ("document.pdf", "image/png", 1),
        ("document.pdf", "application/pdf", MAX_UPLOAD_BYTES + 1),
    ],
)
def test_upload_validation_rejects_unsupported_or_mismatched_files(
    filename: str, content_type: str, size: int
) -> None:
    with pytest.raises(HTTPException):
        validate_document_metadata(filename, content_type, size)
