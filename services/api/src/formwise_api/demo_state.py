"""Process-lifetime singletons for demo (Firestore-less) mode.

Every in-memory repository used when `demo_auth_enabled` is on (or when
Firestore is unreachable and a route falls back to demo mode) MUST be
obtained through the `get_demo_*` factories in this module, and nowhere
else. Each factory is wrapped in `functools.lru_cache(maxsize=None)` with
no arguments, which guarantees exactly one instance is ever constructed
for the lifetime of the Python process, no matter how many times or from
how many call sites (router dependency, direct function call, another
module's import) the factory is invoked.

This replaces the previous pattern of scattering
`_demo_x_repo = SomeInMemoryRepository()` module-level globals across
`documents/dependencies.py`, `settlements/router.py`, and `ocr/router.py`.
That pattern is *usually* fine (module-level globals are only initialized
once), but it is fragile: if a module ever ends up imported under two
different paths (e.g. `formwise_api.documents.dependencies` vs. a
different sys.path entry resolving to the same file), Python treats them
as two separate modules with two separate globals, silently splitting
state and causing exactly the "upload succeeds, but a later GET sees
nothing" symptom. Centralizing all demo singletons in this one module,
behind `lru_cache`, removes that whole class of bug: `lru_cache` keys are
per-function-object, so even if this module were somehow imported twice
under different names, importers that share the *same* imported module
object see the same cache.

Nothing here fakes data. These are the same in-memory repository classes
that already existed - only their lifecycle changed. The real Firestore
path is untouched.
"""

from functools import lru_cache

from formwise_api.audit.repository import InMemoryFinanceAuditEventRepository
from formwise_api.documents.repository import InMemoryDocumentRepository
from formwise_api.evidence.repository import InMemoryEvidenceLinkRepository
from formwise_api.ocr.jobs import InMemoryOcrJobRepository
from formwise_api.settlements.repository import (
    InMemorySettlementDeductionRepository,
    InMemorySettlementRepository,
)
from formwise_api.verification.repository import (
    InMemorySettlementDecisionRepository,
    InMemoryVerificationResultRepository,
)


@lru_cache(maxsize=None)
def get_demo_document_repository() -> InMemoryDocumentRepository:
    return InMemoryDocumentRepository()


@lru_cache(maxsize=None)
def get_demo_settlement_repository() -> InMemorySettlementRepository:
    return InMemorySettlementRepository()


@lru_cache(maxsize=None)
def get_demo_settlement_deduction_repository() -> InMemorySettlementDeductionRepository:
    return InMemorySettlementDeductionRepository()


@lru_cache(maxsize=None)
def get_demo_verification_result_repository() -> InMemoryVerificationResultRepository:
    return InMemoryVerificationResultRepository()


@lru_cache(maxsize=None)
def get_demo_settlement_decision_repository() -> InMemorySettlementDecisionRepository:
    return InMemorySettlementDecisionRepository()


@lru_cache(maxsize=None)
def get_demo_evidence_link_repository() -> InMemoryEvidenceLinkRepository:
    return InMemoryEvidenceLinkRepository()


@lru_cache(maxsize=None)
def get_demo_finance_audit_event_repository() -> InMemoryFinanceAuditEventRepository:
    return InMemoryFinanceAuditEventRepository()


@lru_cache(maxsize=None)
def get_demo_ocr_job_repository(local_storage_path: str, ocr_result_storage_path: str) -> InMemoryOcrJobRepository:
    """Single OCR job repository for the process lifetime.

    Bound to the same shared `get_demo_document_repository()` instance so
    that OCR status/results written by this repository are visible to
    every other route reading documents in demo mode. `local_storage_path`
    / `ocr_result_storage_path` are part of the cache key only so that a
    settings change (e.g. in tests) can produce a distinct instance;
    in a running process these values are constant, so this still
    resolves to a single shared instance in practice.
    """
    return InMemoryOcrJobRepository(
        document_repo=get_demo_document_repository(),
        local_storage_path=local_storage_path,
        ocr_result_storage_path=ocr_result_storage_path,
    )
