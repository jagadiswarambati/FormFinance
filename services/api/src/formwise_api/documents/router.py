import re
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.dependencies.authentication import get_authenticated_identity
from formwise_api.documents.dependencies import (
    get_document_repository,
    get_storage_adapter,
    get_upload_signer,
)
from formwise_api.documents.models import (
    DocumentResponse,
    UploadIntentRequest,
    UploadIntentResponse,
)
from formwise_api.documents.repository import DocumentRepository
from formwise_api.documents.signing import UploadSigner
from formwise_api.documents.validation import MAX_UPLOAD_BYTES, validate_document_metadata
from formwise_api.ocr.router import router as ocr_router
from formwise_api.privacy.router import router as privacy_router
from formwise_api.storage.interfaces import StorageAdapter
from formwise_api.understanding.router import router as understanding_router

router = APIRouter(prefix="/documents", tags=["documents"])
router.include_router(ocr_router)
router.include_router(privacy_router)
router.include_router(understanding_router)


def safe_storage_filename(document_id: str, original_filename: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]", "_", original_filename)
    return f"{document_id}_{normalized[:180]}"


@router.post("/upload-intents", response_model=UploadIntentResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_upload_intent(request: Request, payload: UploadIntentRequest, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), repository: DocumentRepository = Depends(get_document_repository), signer: UploadSigner = Depends(get_upload_signer)) -> UploadIntentResponse:
    original_filename, _ = validate_document_metadata(payload.original_filename, payload.content_type, payload.file_size)
    document_id = uuid4().hex
    now = datetime.now(UTC)
    document = DocumentResponse(document_id=document_id, owner_uid=identity.uid, original_filename=original_filename, stored_filename=safe_storage_filename(document_id, original_filename), content_type=payload.content_type, file_size=payload.file_size, uploaded_at=now, status="upload_pending")
    repository.create_pending(document)
    token, expires_at = signer.issue(document_id, identity.uid)
    upload_url = f"{request.url_for('put_local_upload', document_id=document_id)}?token={token}"
    return UploadIntentResponse(document_id=document_id, upload_url=upload_url, expires_at=datetime.fromtimestamp(expires_at, UTC))


@router.put("/{document_id}/upload", name="put_local_upload", status_code=status.HTTP_204_NO_CONTENT)
async def put_local_upload(document_id: str, request: Request, token: str = Query(min_length=1), repository: DocumentRepository = Depends(get_document_repository), storage: StorageAdapter = Depends(get_storage_adapter), signer: UploadSigner = Depends(get_upload_signer)) -> Response:
    owner_uid = signer.verify(token, document_id)
    document = repository.get_for_owner(document_id, owner_uid)
    if document is None or document.status != "upload_pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload intent was not found.")
    content_type = request.headers.get("content-type", "")
    validate_document_metadata(document.original_filename, content_type, document.file_size)
    stored = await storage.write_upload(document.stored_filename, document.content_type, request.stream(), MAX_UPLOAD_BYTES)
    if stored.file_size != document.file_size:
        storage.delete(document.stored_filename)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded file size does not match the upload intent.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{document_id}/complete", response_model=DocumentResponse, response_model_by_alias=True)
async def complete_upload(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), repository: DocumentRepository = Depends(get_document_repository), storage: StorageAdapter = Depends(get_storage_adapter)) -> DocumentResponse:
    document = repository.get_for_owner(document_id, identity.uid)
    if document is None or document.status != "upload_pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload intent was not found.")
    stored = storage.inspect(document.stored_filename)
    if stored is None or stored.file_size != document.file_size:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded file could not be verified.")
    return repository.mark_quarantined(document_id)


@router.get("", response_model=list[DocumentResponse], response_model_by_alias=True)
async def list_documents(limit: int = Query(default=5, ge=1, le=5), identity: AuthenticatedIdentity = Depends(get_authenticated_identity), repository: DocumentRepository = Depends(get_document_repository)) -> list[DocumentResponse]:
    return repository.list_for_owner(identity.uid, limit)
