import mimetypes
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from formwise_worker.rendering.artifacts import LocalRenderArtifactStore

from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.config import Settings, get_settings
from formwise_api.dependencies.authentication import get_authenticated_identity
from formwise_api.documents.dependencies import get_document_repository
from formwise_api.documents.repository import DocumentRepository
from formwise_api.observability import current_request_id
from formwise_api.rendering.models import RenderRecord, RenderValidationReport
from formwise_api.rendering.repository import FirestoreRenderRepository

router = APIRouter(tags=["rendering"])


def get_render_repository() -> FirestoreRenderRepository:
    return FirestoreRenderRepository(get_firestore_client())


def _response_record(record: RenderRecord) -> RenderRecord:
    """Keep internal artifact locations out of status responses."""
    return record.model_copy(update={"output_key": None, "preview_key": None})


def _artifact_chunks(stream: BinaryIO) -> Iterator[bytes]:
    try:
        while chunk := stream.read(64 * 1024):
            yield chunk
    finally:
        stream.close()


@router.post("/documents/{document_id}/render", response_model=RenderRecord, response_model_by_alias=True, status_code=status.HTTP_202_ACCEPTED)
async def create_render(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), repository: FirestoreRenderRepository = Depends(get_render_repository)) -> RenderRecord:
    document = documents.get_for_owner(document_id, identity.uid)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    if document.privacy_status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="POLICY_BLOCKED")
    now, render_id = datetime.now(UTC), uuid4().hex
    renderer_type: Literal["fillable_pdf", "static_pdf", "image"] = "static_pdf" if document.content_type == "application/pdf" else "image"
    record = RenderRecord(id=render_id, document_id=document_id, renderer_type=renderer_type, render_status="queued", validation_result=RenderValidationReport(valid=False), page_count=0, started_at=now, render_version="v1")
    repository.create(record)
    get_firestore_client().collection("render_jobs").document(render_id).create({"renderId": render_id, "documentId": document_id, "ownerUid": identity.uid, "status": "queued", "attempt": 0, "nextAttemptAt": None, "requestId": current_request_id(), "createdAt": now, "startedAt": None, "completedAt": None, "errorCode": None})
    return _response_record(record)


@router.get("/documents/{document_id}/render", response_model=RenderRecord, response_model_by_alias=True)
async def latest_render(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), repository: FirestoreRenderRepository = Depends(get_render_repository)) -> RenderRecord:
    if documents.get_for_owner(document_id, identity.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    record = repository.latest_for_document(document_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render was not found.")
    return _response_record(record)


@router.get("/renders/{render_id}", response_model=RenderRecord, response_model_by_alias=True)
async def get_render(render_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), repository: FirestoreRenderRepository = Depends(get_render_repository)) -> RenderRecord:
    record = repository.get(render_id)
    if record is None or documents.get_for_owner(record.document_id, identity.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render was not found.")
    return _response_record(record)


@router.get("/renders/{render_id}/download", response_class=StreamingResponse)
async def download_render(
    render_id: str,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    documents: DocumentRepository = Depends(get_document_repository),
    repository: FirestoreRenderRepository = Depends(get_render_repository),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    record = repository.get(render_id)
    if record is None or documents.get_for_owner(record.document_id, identity.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render was not found.")
    if record.render_status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="RENDER_NOT_COMPLETED")
    if not record.output_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RENDER_OUTPUT_UNAVAILABLE")

    artifacts = LocalRenderArtifactStore(
        settings.local_storage_path,
        settings.render_output_storage_path,
    )
    stream = artifacts.open_completed_artifact(record.output_key)
    if stream is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RENDER_ARTIFACT_UNAVAILABLE")

    filename = Path(record.output_key).name
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return StreamingResponse(
        _artifact_chunks(stream),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
