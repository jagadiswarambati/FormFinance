from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.config import Settings, get_settings
from formwise_api.dependencies.authentication import get_authenticated_identity
from formwise_api.documents.dependencies import get_document_repository
from formwise_api.documents.repository import DocumentRepository
from formwise_api.understanding.models import StructuredDocument
from formwise_api.understanding.pipeline import UnderstandingPipeline
from formwise_api.understanding.repository import (
    FirestoreUnderstandingRepository,
    UnderstandingRepository,
)
from formwise_api.understanding.service import UnderstandingService

router = APIRouter(tags=["understanding"])


def get_understanding_repository() -> UnderstandingRepository:
    return FirestoreUnderstandingRepository(get_firestore_client())


def get_understanding_service(repository: UnderstandingRepository = Depends(get_understanding_repository), settings: Settings = Depends(get_settings)) -> UnderstandingService:
    return UnderstandingService(repository, UnderstandingPipeline(), settings.understanding_provider_version)


@router.post("/{document_id}/understand", response_model=StructuredDocument, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def understand_document(
    document_id: str,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    documents: DocumentRepository = Depends(get_document_repository),
    service: UnderstandingService = Depends(get_understanding_service),
    settings: Settings = Depends(get_settings),
) -> StructuredDocument:
    document = documents.get_for_owner(document_id, identity.uid)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    if document.privacy_status != "completed" or not document.redacted_text_storage_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Protected privacy processing must complete before form understanding.")
    original_pdf_path = Path(settings.local_storage_path) / document.stored_filename if document.content_type == "application/pdf" else None
    return service.understand(document_id, document.redacted_text_storage_key, document.protected_layout_storage_key, original_pdf_path)


@router.get("/{document_id}/understanding", response_model=StructuredDocument, response_model_by_alias=True)
async def get_understanding(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), repository: UnderstandingRepository = Depends(get_understanding_repository)) -> StructuredDocument:
    if documents.get_for_owner(document_id, identity.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    structured = repository.get(document_id)
    if structured is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Structured document was not found.")
    return structured
