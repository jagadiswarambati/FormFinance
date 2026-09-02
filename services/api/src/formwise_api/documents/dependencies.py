import structlog
from fastapi import Depends, HTTPException, status

from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.config import Settings, get_settings
from formwise_api.documents.repository import DocumentRepository, FirestoreDocumentRepository
from formwise_api.documents.signing import UploadSigner
from formwise_api.storage.interfaces import StorageAdapter
from formwise_api.storage.local import LocalStorageAdapter

logger = structlog.get_logger()


def get_document_repository() -> DocumentRepository:
    return FirestoreDocumentRepository(get_firestore_client())


def get_storage_adapter(settings: Settings = Depends(get_settings)) -> StorageAdapter:
    return LocalStorageAdapter(settings.local_storage_path, settings.quarantine_storage_path)


def get_upload_signer(settings: Settings = Depends(get_settings)) -> UploadSigner:
    try:
        if not settings.upload_signing_secret:
            raise RuntimeError("UPLOAD_SIGNING_SECRET is not configured.")
        return UploadSigner(settings.upload_signing_secret, settings.upload_intent_ttl_seconds)
    except RuntimeError as error:
        logger.exception(
            "dependency_unavailable",
            dependency="upload_signing",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload signing is not configured.",
        ) from error
