from fastapi import APIRouter, Depends, HTTPException, status
from formwise_document_core.privacy_models import PrivacyAuditEvent, PrivacySummary

from formwise_api.ai_provider.factory import get_ai_provider
from formwise_api.ai_provider.interfaces import AIProvider
from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.config import Settings, get_settings
from formwise_api.conversations.models import (
    ChatMessageRequest,
    ChatResponse,
    Conversation,
    ConversationDetail,
    ConversationMessage,
    CreateConversationRequest,
)
from formwise_api.conversations.repository import FirestoreConversationRepository
from formwise_api.conversations.service import ConversationService
from formwise_api.dependencies.authentication import get_authenticated_identity
from formwise_api.documents.dependencies import get_document_repository
from formwise_api.documents.repository import DocumentRepository
from formwise_api.privacy.dashboard_repository import (
    PrivacyAuditEventRepository,
    PrivacySummaryRepository,
)
from formwise_api.privacy.dependencies import (
    get_privacy_audit_event_repository,
    get_privacy_summary_refresher,
    get_privacy_summary_repository,
)
from formwise_api.privacy.refresher import PrivacySummaryRefresher
from formwise_api.retention.repository import (
    FirestoreRetainedConversationSelector,
    FirestoreRetentionJobRepository,
    FirestoreRetentionStateRepository,
)
from formwise_api.retention.service import RetentionOrchestrator
from formwise_api.understanding.repository import FirestoreUnderstandingRepository

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_service(settings: Settings = Depends(get_settings), documents: DocumentRepository = Depends(get_document_repository), refresher: PrivacySummaryRefresher = Depends(get_privacy_summary_refresher)) -> ConversationService:
    client = get_firestore_client()
    repository = FirestoreConversationRepository(client)
    provider: AIProvider = get_ai_provider(settings)
    retention = RetentionOrchestrator(
        repository,
        FirestoreRetentionStateRepository(client),
        FirestoreRetentionJobRepository(client),
        FirestoreRetainedConversationSelector(client),
    )
    return ConversationService(repository, FirestoreUnderstandingRepository(client), provider, retention, documents, refresher)


@router.post("", response_model=Conversation, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_conversation(payload: CreateConversationRequest, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), service: ConversationService = Depends(get_conversation_service)) -> Conversation:
    document = documents.get_for_owner(payload.document_id, identity.uid)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    if document.privacy_status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Privacy processing must complete before creating a conversation.")
    try:
        return service.create(identity.uid, payload.document_id, payload.locale)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/{conversation_id}", response_model=ConversationDetail, response_model_by_alias=True)
async def get_conversation(conversation_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), service: ConversationService = Depends(get_conversation_service)) -> ConversationDetail:
    conversation = service.get_for_owner(conversation_id, identity.uid)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation was not found.")
    return ConversationDetail(**conversation.model_dump(), messages=service.history(conversation))


@router.post("/{conversation_id}/messages", response_model=ChatResponse, response_model_by_alias=True)
async def send_message(conversation_id: str, payload: ChatMessageRequest, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), service: ConversationService = Depends(get_conversation_service)) -> ChatResponse:
    conversation = service.get_for_owner(conversation_id, identity.uid)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation was not found.")
    return await service.ask(conversation, payload.message)


@router.get("/{conversation_id}/messages", response_model=list[ConversationMessage], response_model_by_alias=True)
async def get_messages(conversation_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), service: ConversationService = Depends(get_conversation_service)) -> list[ConversationMessage]:
    conversation = service.get_for_owner(conversation_id, identity.uid)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation was not found.")
    return service.history(conversation)


@router.get(
    "/{conversation_id}/privacy-summary",
    response_model=PrivacySummary,
    response_model_by_alias=True,
)
async def get_privacy_summary(
    conversation_id: str,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    service: ConversationService = Depends(get_conversation_service),
    summaries: PrivacySummaryRepository = Depends(get_privacy_summary_repository),
) -> PrivacySummary:
    conversation = service.get_for_owner(conversation_id, identity.uid)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation was not found.")
    summary = summaries.get(conversation.id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Privacy summary was not found.")
    return summary


@router.get(
    "/{conversation_id}/privacy-events",
    response_model=list[PrivacyAuditEvent],
    response_model_by_alias=True,
)
async def list_privacy_events(
    conversation_id: str,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    service: ConversationService = Depends(get_conversation_service),
    events: PrivacyAuditEventRepository = Depends(get_privacy_audit_event_repository),
) -> list[PrivacyAuditEvent]:
    conversation = service.get_for_owner(conversation_id, identity.uid)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation was not found.")
    return events.list_for_conversation(conversation.id)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), service: ConversationService = Depends(get_conversation_service)) -> None:
    conversation = service.get_for_owner(conversation_id, identity.uid)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation was not found.")
    service.delete(conversation)
