from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.config import Settings, get_settings
from formwise_api.dependencies.authentication import get_authenticated_identity
from formwise_api.documents.dependencies import get_document_repository
from formwise_api.documents.repository import DocumentRepository
from formwise_api.privacy.engine import redact_text, scan_text, summaries
from formwise_api.privacy.models import PrivacyConsentRequest, PrivacyReportResponse
from formwise_api.privacy.repository import (
    FirestorePrivacyReportRepository,
    PrivacyReportRepository,
)
from formwise_api.privacy.storage import LocalPrivacyTextStore

router = APIRouter(tags=["privacy"])


def get_privacy_report_repository() -> PrivacyReportRepository:
    return FirestorePrivacyReportRepository(get_firestore_client())


def _response(document_id: str, report: dict[str, Any]) -> PrivacyReportResponse:
    return PrivacyReportResponse(document_id=document_id, status=str(report["status"]), policy_version=str(report["policyVersion"]), findings=report["findings"], pii_categories=report["piiCategories"], requires_consent=bool(report["requiresConsent"]), consent_decision=report.get("consentDecision"), protected_text_ready=bool(report["protectedTextReady"]), completed_at=report.get("completedAt"))


@router.post("/{document_id}/privacy/scan", response_model=PrivacyReportResponse, response_model_by_alias=True)
async def scan_privacy(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), reports: PrivacyReportRepository = Depends(get_privacy_report_repository), settings: Settings = Depends(get_settings)) -> PrivacyReportResponse:
    document = documents.get_for_owner(document_id, identity.uid)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    if document.ocr_status != "completed" or not document.ocr_text_storage_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="OCR must complete before privacy scanning.")

    findings = scan_text(LocalPrivacyTextStore(settings.privacy_result_storage_path).read_ocr(document.ocr_text_storage_key))
    finding_summaries = [item.model_dump() for item in summaries(findings)]
    categories = sorted({finding.category for finding in findings})
    has_block = any(finding.action == "BLOCK" for finding in findings)
    requires_consent = any(finding.action == "ASK_USER" for finding in findings) and not has_block
    protected_key: str | None = None
    protected_layout_key: str | None = None
    if not has_block:
        store = LocalPrivacyTextStore(settings.privacy_result_storage_path)
        protected_key = store.write_protected(document_id, redact_text(store.read_ocr(document.ocr_text_storage_key), findings))
        if document.ocr_layout_storage_key:
            protected_tokens: list[dict[str, object]] = []
            for token in store.read_layout(document.ocr_layout_storage_key):
                text = token.get("text")
                if isinstance(text, str):
                    token = {**token, "text": redact_text(text, scan_text(text))}
                protected_tokens.append(token)
            protected_layout_key = store.write_protected_layout(document_id, protected_tokens)
    now = datetime.now(UTC)
    report: dict[str, Any] = {"policyVersion": settings.privacy_policy_version, "findings": finding_summaries, "piiCategories": categories, "requiresConsent": requires_consent, "protectedTextReady": protected_key is not None, "status": "blocked" if has_block else "awaiting_consent" if requires_consent else "completed", "consentDecision": None, "completedAt": now if not requires_consent else None}
    reports.save(document_id, report)
    updated = documents.update_privacy(document_id, identity.uid, {"privacyStatus": report["status"], "privacyCompletedAt": report["completedAt"], "privacyPolicyVersion": settings.privacy_policy_version, "piiCategories": categories, "redactedTextStorageKey": protected_key, "protectedLayoutStorageKey": protected_layout_key, "consentDecision": None})
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    return _response(document_id, report)


@router.get("/{document_id}/privacy", response_model=PrivacyReportResponse, response_model_by_alias=True)
async def get_privacy_report(document_id: str, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), reports: PrivacyReportRepository = Depends(get_privacy_report_repository)) -> PrivacyReportResponse:
    if documents.get_for_owner(document_id, identity.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    report = reports.get(document_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Privacy report was not found.")
    return _response(document_id, report)


@router.post("/{document_id}/privacy/consent", response_model=PrivacyReportResponse, response_model_by_alias=True)
async def save_privacy_consent(document_id: str, payload: PrivacyConsentRequest, identity: AuthenticatedIdentity = Depends(get_authenticated_identity), documents: DocumentRepository = Depends(get_document_repository), reports: PrivacyReportRepository = Depends(get_privacy_report_repository)) -> PrivacyReportResponse:
    if documents.get_for_owner(document_id, identity.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")
    report = reports.get(document_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Privacy report was not found.")
    if report["status"] == "blocked":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This document is blocked by the privacy policy.")
    if not report["requiresConsent"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This privacy report does not require consent.")
    if report["status"] != "awaiting_consent":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A privacy decision has already been recorded.")
    now = datetime.now(UTC)
    report.update({"status": "cancelled" if payload.decision == "cancel" else "completed", "consentDecision": payload.decision, "completedAt": now})
    reports.save(document_id, report)
    documents.update_privacy(document_id, identity.uid, {"privacyStatus": report["status"], "privacyCompletedAt": now, "consentDecision": payload.decision})
    return _response(document_id, report)
