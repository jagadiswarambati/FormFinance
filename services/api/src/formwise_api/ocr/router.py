from fastapi import APIRouter, Depends, HTTPException, status

from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.config import Settings, get_settings
from formwise_api.dependencies.authentication import get_authenticated_identity
from formwise_api.documents.dependencies import get_document_repository
from formwise_api.documents.models import DocumentResponse, OcrStatusResponse
from formwise_api.documents.repository import DocumentRepository
from formwise_api.ocr.jobs import FirestoreOcrJobRepository, OcrJobRepository

router = APIRouter(tags=["ocr"])


def get_ocr_job_repository() -> OcrJobRepository:
    return FirestoreOcrJobRepository(get_firestore_client())


@router.post("/{document_id}/ocr", response_model=DocumentResponse, response_model_by_alias=True, status_code=status.HTTP_202_ACCEPTED)
async def start_ocr(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), repository: DocumentRepository = Depends(get_document_repository), jobs: OcrJobRepository = Depends(get_ocr_job_repository), settings: Settings = Depends(get_settings)) -> DocumentResponse:
    document = repository.start_ocr(document_id, identity.uid, settings.ocr_provider)
    if document is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document is not available for OCR processing.")
    jobs.enqueue(document.document_id, identity.uid, settings.ocr_provider)
    return document


@router.get("/{document_id}/ocr", response_model=OcrStatusResponse, response_model_by_alias=True)
async def get_ocr_status(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), repository: DocumentRepository = Depends(get_document_repository)) -> OcrStatusResponse:
    document = repository.get_for_owner(document_id, identity.uid)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    return OcrStatusResponse(status=document.ocr_status, provider=document.ocr_provider, confidence=document.ocr_confidence, text_length=document.text_length)
