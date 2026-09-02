from fastapi import APIRouter, Depends, HTTPException, status

from formwise_api.assignments.models import (
    AssignmentGenerationResponse,
    AssignmentUpdateRequest,
    FieldAssignment,
)
from formwise_api.assignments.repository import FirestoreAssignmentRepository
from formwise_api.assignments.service import AssignmentService
from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.conversations.repository import FirestoreConversationRepository
from formwise_api.dependencies.authentication import get_authenticated_identity
from formwise_api.documents.dependencies import get_document_repository
from formwise_api.documents.repository import DocumentRepository
from formwise_api.privacy.dependencies import get_privacy_summary_refresher
from formwise_api.privacy.refresher import PrivacySummaryRefresher
from formwise_api.understanding.repository import FirestoreUnderstandingRepository

router = APIRouter(tags=["assignments"])


def get_assignment_service() -> AssignmentService:
    client = get_firestore_client()
    return AssignmentService(FirestoreAssignmentRepository(client), FirestoreUnderstandingRepository(client), FirestoreConversationRepository(client))


@router.post("/documents/{document_id}/assignments/generate", response_model=AssignmentGenerationResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def generate_assignments(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), service: AssignmentService = Depends(get_assignment_service)) -> AssignmentGenerationResponse:
    document = documents.get_for_owner(document_id, identity.uid)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    if document.privacy_status == "blocked":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="POLICY_BLOCKED: this document is manual-only.")
    if document.privacy_status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Privacy processing must complete before assignments can be generated.")
    try:
        return AssignmentGenerationResponse(assignments=service.generate(identity.uid, document_id))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/documents/{document_id}/assignments", response_model=list[FieldAssignment], response_model_by_alias=True)
async def list_assignments(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), service: AssignmentService = Depends(get_assignment_service)) -> list[FieldAssignment]:
    if documents.get_for_owner(document_id, identity.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    return service.list(document_id)


@router.patch("/assignments/{assignment_id}", response_model=FieldAssignment, response_model_by_alias=True)
async def update_assignment(assignment_id: str, payload: AssignmentUpdateRequest, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), service: AssignmentService = Depends(get_assignment_service), refresher: PrivacySummaryRefresher = Depends(get_privacy_summary_refresher)) -> FieldAssignment:
    existing = service.get(assignment_id)
    document = documents.get_for_owner(existing.document_id, identity.uid) if existing is not None else None
    if existing is None or document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment was not found.")
    try:
        updated = service.update(assignment_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment was not found.")
    if updated.status == "approved":
        conversation = FirestoreConversationRepository(get_firestore_client()).get_active_for_document(
            identity.uid,
            updated.document_id,
        )
        if conversation is not None:
            refresher.refresh(conversation, document)
    return updated
