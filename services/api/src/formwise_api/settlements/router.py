from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.dependencies.authentication import get_authenticated_identity
from formwise_api.settlements.models import (
    Settlement,
    SettlementCreateRequest,
    SettlementResponse,
    SettlementDeduction,
)
from formwise_api.settlements.repository import (
    FirestoreSettlementRepository,
    FirestoreSettlementDeductionRepository,
)
from formwise_api.settlements.service import SettlementService
from formwise_api.settlements.extraction_service import SettlementExtractionService
from formwise_api.settlements.verification_service import SettlementVerificationService
from formwise_api.settlements.batch_processor import BatchSettlementProcessor, BatchMetrics
from formwise_api.settlements.document_extractor import DocumentSettlementExtractor
from formwise_api.settlements.processing import SettlementProcessingPipeline
from formwise_api.documents.dependencies import get_document_repository
from formwise_api.verification.models import SettlementDecision
from formwise_api.verification.repository import (
    FirestoreVerificationResultRepository,
    FirestoreSettlementDecisionRepository,
)
from formwise_api.evidence.repository import FirestoreEvidenceLinkRepository
from formwise_api.audit.repository import FirestoreFinanceAuditEventRepository

router = APIRouter(prefix="/settlements", tags=["settlements"])


class DeductionInput(BaseModel):
    """Input format for a single deduction"""
    type: str
    description: str
    amount: float
    reference_id: str | None = Field(default=None, alias="referenceId")
    reference_date: str | None = Field(default=None, alias="referenceDate")
    confidence: float = 0.95

    model_config = {"populate_by_name": True}


class ExtractRequest(BaseModel):
    """Request to extract deductions for a settlement"""
    deductions: list[DeductionInput]


class VerificationResponse(BaseModel):
    """Response containing settlement decision"""
    decision: SettlementDecision

    model_config = {"populate_by_name": True}


class BatchSettlementSpec(BaseModel):
    """Specification for a single settlement in batch"""
    source: str = "razorpay"
    settlement_date: str
    gross_amount: float
    net_amount: float
    currency: str = "INR"
    ocr_text: str = ""
    
    model_config = {"populate_by_name": True}


class BatchProcessRequest(BaseModel):
    """Request to process multiple settlements"""
    settlements: list[BatchSettlementSpec]


class BatchMetricsResponse(BaseModel):
    """Metrics from batch processing"""
    timestamp: str
    total_records: int = 0
    processed: int = 0
    successfully_extracted: int = 0
    total_settlements: int
    total_deductions: int
    approved_count: int
    flagged_count: int
    escalated_count: int
    processing_failed_count: int
    verified_deductions: int
    disputed_deductions: int
    unverifiable_deductions: int
    settlement_approval_rate: float
    deduction_verification_rate: float
    evidence_match_rate: float = 0.0
    exception_rate: float = 0.0
    extraction_success_rate: float = 0.0
    agent_investigations: int
    agent_successes: int
    agent_failures: int
    exceptions: list[dict] = []
    settlement_results: list[dict] = []
    
    model_config = {"populate_by_name": True}


from formwise_api.config import get_settings
from formwise_api.settlements.repository import (
    FirestoreSettlementRepository,
    FirestoreSettlementDeductionRepository,
    InMemorySettlementRepository,
    InMemorySettlementDeductionRepository,
)
from formwise_api.verification.repository import (
    FirestoreVerificationResultRepository,
    FirestoreSettlementDecisionRepository,
    InMemoryVerificationResultRepository,
    InMemorySettlementDecisionRepository,
)
from formwise_api.evidence.repository import (
    FirestoreEvidenceLinkRepository,
    InMemoryEvidenceLinkRepository,
)
from formwise_api.audit.repository import (
    FirestoreFinanceAuditEventRepository,
    InMemoryFinanceAuditEventRepository,
)

_demo_settlement_repo = InMemorySettlementRepository()
_demo_deduction_repo = InMemorySettlementDeductionRepository()
_demo_verification_repo = InMemoryVerificationResultRepository()
_demo_decision_repo = InMemorySettlementDecisionRepository()
_demo_evidence_repo = InMemoryEvidenceLinkRepository()
_demo_audit_repo = InMemoryFinanceAuditEventRepository()


def _get_repositories(settings=None):
    if settings is None:
        settings = get_settings()
    if settings.demo_auth_enabled:
        return (
            _demo_settlement_repo,
            _demo_deduction_repo,
            _demo_verification_repo,
            _demo_decision_repo,
            _demo_evidence_repo,
            _demo_audit_repo,
        )
    try:
        client = get_firestore_client()
        return (
            FirestoreSettlementRepository(client),
            FirestoreSettlementDeductionRepository(client),
            FirestoreVerificationResultRepository(client),
            FirestoreSettlementDecisionRepository(client),
            FirestoreEvidenceLinkRepository(client),
            FirestoreFinanceAuditEventRepository(client),
        )
    except Exception:
        return (
            _demo_settlement_repo,
            _demo_deduction_repo,
            _demo_verification_repo,
            _demo_decision_repo,
            _demo_evidence_repo,
            _demo_audit_repo,
        )


def get_settlement_service(settings=Depends(get_settings)) -> SettlementService:
    s_repo, d_repo, _, _, _, _ = _get_repositories(settings)
    return SettlementService(s_repo, d_repo)


def get_extraction_service(settings=Depends(get_settings)) -> SettlementExtractionService:
    s_repo, d_repo, _, _, _, a_repo = _get_repositories(settings)
    return SettlementExtractionService(s_repo, d_repo, a_repo)


def get_verification_service(settings=Depends(get_settings)) -> SettlementVerificationService:
    from formwise_api.ai_provider.factory import get_ai_provider
    
    s_repo, d_repo, v_repo, dec_repo, e_repo, a_repo = _get_repositories(settings)
    
    try:
        ai_provider = get_ai_provider(settings)
    except Exception:
        ai_provider = None
    
    return SettlementVerificationService(
        s_repo,
        d_repo,
        v_repo,
        dec_repo,
        a_repo,
        e_repo,
        ai_provider,
    )


def get_batch_processor(settings=Depends(get_settings)) -> BatchSettlementProcessor:
    from formwise_api.ai_provider.factory import get_ai_provider
    from formwise_api.settlements.evidence_matcher import SettlementEvidenceStore
    
    s_repo, d_repo, v_repo, dec_repo, e_repo, a_repo = _get_repositories(settings)
    
    try:
        ai_provider = get_ai_provider(settings)
    except Exception:
        ai_provider = None
    
    doc_repo = get_document_repository(settings)
    evidence_store = SettlementEvidenceStore(document_repo=doc_repo)
    
    settlement_service = SettlementService(s_repo, d_repo)
    verification_service = SettlementVerificationService(
        s_repo, d_repo, v_repo, dec_repo, a_repo, e_repo, ai_provider,
        evidence_store=evidence_store,
    )
    doc_extractor = DocumentSettlementExtractor(
        get_document_repository(settings),
        a_repo,
    )
    extraction_service = SettlementExtractionService(s_repo, d_repo, a_repo)
    
    return BatchSettlementProcessor(
        settlement_service,
        doc_extractor,
        verification_service,
        s_repo,
        extraction_service,
    )



@router.post(
    "",
    response_model=SettlementResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_settlement(
    req: SettlementCreateRequest,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    service: SettlementService = Depends(get_settlement_service),
) -> SettlementResponse:
    """Create a new settlement"""
    settlement = Settlement(
        owner_uid=identity.uid,
        source=req.source,
        settlement_date=req.settlement_date,
        gross_amount=req.gross_amount,
        net_amount=req.net_amount,
        currency=req.currency,
    )
    settlement_id = service.create_settlement(settlement)
    created = service.get_settlement(settlement_id)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create settlement")
    return SettlementResponse(**created.model_dump(by_alias=True))


@router.get(
    "/{settlement_id}",
    response_model=SettlementResponse,
    response_model_by_alias=True,
)
async def get_settlement(
    settlement_id: str,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    service: SettlementService = Depends(get_settlement_service),
) -> SettlementResponse:
    """Retrieve a settlement"""
    settlement = service.get_settlement(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    if settlement.owner_uid != identity.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    return SettlementResponse(**settlement.model_dump(by_alias=True))


@router.get(
    "",
    response_model=list[SettlementResponse],
    response_model_by_alias=True,
)
async def list_settlements(
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    service: SettlementService = Depends(get_settlement_service),
) -> list[SettlementResponse]:
    """List all settlements for current user"""
    settlements = service.list_user_settlements(identity.uid)
    return [SettlementResponse(**s.model_dump(by_alias=True)) for s in settlements]


@router.post(
    "/{settlement_id}/extract",
    response_model=SettlementResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
)
async def extract_settlement_deductions(
    settlement_id: str,
    req: ExtractRequest,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    settlement_service: SettlementService = Depends(get_settlement_service),
    extraction_service: SettlementExtractionService = Depends(get_extraction_service),
) -> SettlementResponse:
    """
    Extract deductions from a settlement.
    
    Takes deduction data and creates SettlementDeduction records.
    """
    # Verify ownership
    settlement = settlement_service.get_settlement(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    if settlement.owner_uid != identity.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Extract deductions
    try:
        deduction_dicts = [d.model_dump(by_alias=False) for d in req.deductions]
        extraction_service.extract_from_structured_data(settlement_id, deduction_dicts)
        updated = extraction_service.complete_extraction(settlement_id)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to complete extraction")
        return SettlementResponse(**updated.model_dump(by_alias=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Extraction failed: {str(e)}")


@router.post(
    "/{settlement_id}/verify",
    response_model=VerificationResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
)
async def verify_settlement(
    settlement_id: str,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    settlement_service: SettlementService = Depends(get_settlement_service),
    verification_service: SettlementVerificationService = Depends(get_verification_service),
) -> VerificationResponse:
    """
    Run verification on settlement deductions.
    
    Runs deterministic checks on all deductions and produces a settlement decision.
    """
    # Verify ownership
    settlement = settlement_service.get_settlement(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    if settlement.owner_uid != identity.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Run verification
    try:
        decision = verification_service.verify_settlement(settlement_id)
        if not decision:
            raise HTTPException(status_code=500, detail="Verification failed")
        return VerificationResponse(decision=decision)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Verification failed: {str(e)}")


@router.post(
    "/batch/process",
    response_model=BatchMetricsResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
)
async def process_batch(
    req: BatchProcessRequest,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    batch_processor: BatchSettlementProcessor = Depends(get_batch_processor),
) -> BatchMetricsResponse:
    """
    Process a batch of settlements end-to-end.
    
    For each settlement:
    1. Extract deductions from OCR text
    2. Run verification workflow
    3. Generate decision
    
    Returns batch metrics and detailed results.
    """
    try:
        specs = [s.model_dump(by_alias=False) for s in req.settlements]
        metrics, results = batch_processor.process_settlements(identity.uid, specs)
        
        return BatchMetricsResponse(**metrics.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch processing failed: {str(e)}")


@router.get(
    "/batch/demo-run",
    response_model=BatchMetricsResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
)
async def run_demo_batch(
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    batch_processor: BatchSettlementProcessor = Depends(get_batch_processor),
) -> BatchMetricsResponse:
    """
    Run demo batch with 50 synthetic benchmark settlements showing diverse outcomes.
    """
    from formwise_api.settlements.demo_data import get_benchmark_settlements
    
    try:
        specs = get_benchmark_settlements()
        metrics, results = batch_processor.process_settlements(identity.uid, specs)
        return BatchMetricsResponse(**metrics.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Demo batch failed: {str(e)}")


# ============================================================================
# REAL SETTLEMENT PROCESSING PIPELINE (NEW)
# ============================================================================


class ProcessSettlementDocumentRequest(BaseModel):
    """Request to process a settlement document"""
    document_id: str = Field(..., alias="documentId")
    ocr_text: str | None = Field(default=None, alias="ocrText")
    evidence_document_ids: list[str] | None = Field(default=None, alias="evidenceDocumentIds")
    
    model_config = {"populate_by_name": True}


class ProcessSettlementDocumentResponse(BaseModel):
    """Response from settlement document processing"""
    settlement_id: str = Field(alias="settlementId")
    status: str
    reference: str | None = None
    currency: str | None = None
    gross_amount: float = Field(alias="grossAmount")
    total_deductions: float = Field(default=0.0, alias="totalDeductions")
    net_amount: float = Field(alias="netAmount")
    deductions: list[dict]
    verification: list[dict] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    decision: dict
    audit_events: list[dict] = Field(default_factory=list, alias="auditEvents")
    document_id: str = Field(alias="documentId")
    processed_at: str = Field(alias="processedAt")
    
    model_config = {"populate_by_name": True}


def get_processing_pipeline(
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    client = Depends(get_firestore_client),
    document_repo = Depends(get_document_repository),
) -> SettlementProcessingPipeline:
    """Dependency to create processing pipeline"""
    from formwise_api.config import Settings
    from formwise_api.ai_provider.factory import get_ai_provider

    try:
        ai_provider = get_ai_provider(Settings())
    except Exception:
        ai_provider = None

    return SettlementProcessingPipeline(
        document_repo=document_repo,
        settlement_repo=FirestoreSettlementRepository(client),
        deduction_repo=FirestoreSettlementDeductionRepository(client),
        verification_repo=FirestoreVerificationResultRepository(client),
        decision_repo=FirestoreSettlementDecisionRepository(client),
        evidence_repo=FirestoreEvidenceLinkRepository(client),
        audit_repo=FirestoreFinanceAuditEventRepository(client),
        ai_provider=ai_provider,
    )


@router.post(
    "/process-document",
    response_model=ProcessSettlementDocumentResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
)
async def process_settlement_document(
    payload: ProcessSettlementDocumentRequest,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    pipeline: SettlementProcessingPipeline = Depends(get_processing_pipeline),
) -> ProcessSettlementDocumentResponse:
    """
    Process a settlement document end-to-end.
    
    Complete workflow:
    1. Load settlement document (FormWise)
    2. Extract OCR text
    3. Parse settlement structure
    4. Find/link evidence documents
    5. Run verification (deterministic + AI)
    6. Generate decision
    7. Log audit trail
    
    Returns: Settlement with decision and audit trail
    """
    try:
        result = pipeline.process_settlement_document(
            document_id=payload.document_id,
            owner_uid=identity.uid,
            ocr_text=payload.ocr_text,
            evidence_document_ids=payload.evidence_document_ids,
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return ProcessSettlementDocumentResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Settlement processing failed: {str(e)}"
        )


class SettlementDetailsResponse(BaseModel):
    """Complete settlement details"""
    settlement: dict
    deductions: list[dict]
    decision: dict
    
    model_config = {"populate_by_name": True}


@router.get(
    "/{settlement_id}/details",
    response_model=SettlementDetailsResponse,
    response_model_by_alias=True,
)
async def get_settlement_details(
    settlement_id: str,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    pipeline: SettlementProcessingPipeline = Depends(get_processing_pipeline),
) -> SettlementDetailsResponse:
    """Get complete settlement details with all verification results."""
    details = pipeline.get_settlement_details(settlement_id, identity.uid)
    if not details:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    return SettlementDetailsResponse(**details)
