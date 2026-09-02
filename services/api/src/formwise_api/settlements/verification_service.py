"""Settlement verification orchestration service."""

from typing import Optional
from formwise_api.settlements.models import Settlement
from formwise_api.settlements.repository import (
    SettlementRepository,
    SettlementDeductionRepository,
)
from formwise_api.settlements.deterministic_verifier import DeterministicVerifier
from formwise_api.settlements.evidence_matcher import EvidenceMatcher
from formwise_api.settlements.finance_agent import SettlementFinanceAgent
from formwise_api.verification.models import SettlementDecision
from formwise_api.verification.repository import (
    VerificationResultRepository,
    SettlementDecisionRepository,
)
from formwise_api.evidence.repository import EvidenceLinkRepository
from formwise_api.audit.finance_audit_events import FinanceAuditEvent
from formwise_api.audit.repository import FinanceAuditEventRepository
from formwise_api.ai_provider.interfaces import AIProvider


class SettlementVerificationService:
    """Orchestrates settlement verification workflow.
    
    Workflow:
    1. Run deterministic verification on each deduction
    2. If confident (verified) → mark as verified
    3. If ambiguous/failed → run AI agent investigation
    4. AI agent uses tools to investigate
    5. Aggregate results into settlement decision
    """

    def __init__(
        self,
        settlement_repo: SettlementRepository,
        deduction_repo: SettlementDeductionRepository,
        verification_repo: VerificationResultRepository,
        decision_repo: SettlementDecisionRepository,
        audit_repo: FinanceAuditEventRepository,
        evidence_link_repo: Optional[EvidenceLinkRepository] = None,
        ai_provider: Optional[AIProvider] = None,
    ):
        self._settlement_repo = settlement_repo
        self._deduction_repo = deduction_repo
        self._verification_repo = verification_repo
        self._decision_repo = decision_repo
        self._audit_repo = audit_repo
        self._verifier = DeterministicVerifier()
        self._evidence_matcher = EvidenceMatcher(evidence_link_repo) if evidence_link_repo else None
        self._agent = SettlementFinanceAgent(ai_provider, audit_repo) if ai_provider else None

    def verify_settlement(self, settlement_id: str) -> SettlementDecision | None:
        """
        Run full verification workflow on a settlement.
        
        1. Load settlement and deductions
        2. Run deterministic checks on each deduction
        3. Aggregate results into settlement decision
        4. Persist decision
        
        Returns SettlementDecision if successful, None if settlement not found.
        """
        # Load settlement and deductions
        settlement = self._settlement_repo.get(settlement_id)
        if not settlement:
            return None
        
        deductions = self._deduction_repo.list_for_settlement(settlement_id)
        
        # Run deterministic verification on settlement level
        settlement_issue = self._verifier.verify_settlement(settlement, deductions)
        if settlement_issue:
            # Settlement has structural issues
            self._verification_repo.create(settlement_issue)
            decision = SettlementDecision(
                settlement_id=settlement_id,
                final_decision="flag",
                reason=f"Settlement structure issue: {settlement_issue.reason}",
                verification_summary={
                    "total_deductions": len(deductions),
                    "issue": settlement_issue.reason,
                },
                confidence=0.0,
                requires_human_review=True,
            )
            decision_id = self._decision_repo.create(decision)
            self._settlement_repo.update(settlement_id, {"status": "flagged"})
            return self._decision_repo.get(decision_id)
        
        # Verify each deduction
        verification_results = []
        verified_count = 0
        disputed_count = 0
        unverifiable_count = 0
        
        for deduction in deductions:
            # Step 1: Run deterministic verification
            result = self._verifier.verify_deduction(deduction, settlement)
            
            # Step 2: If deterministic check passes, accept result
            if result.status == "verified":
                result.id = self._verification_repo.create(result)
                verification_results.append(result)
                verified_count += 1
                continue
            
            # Step 3: For ambiguous/failed cases, try evidence matching
            if self._evidence_matcher:
                evidence_result, evidence_link = self._evidence_matcher.match_deduction_to_evidence(
                    deduction, settlement
                )
                if evidence_result.status == "verified":
                    evidence_result.id = self._verification_repo.create(evidence_result)
                    verification_results.append(evidence_result)
                    verified_count += 1
                    continue
                # If evidence matching also doesn't resolve, will try agent next
                result = evidence_result
            
            # Step 4: If still ambiguous and agent available, run AI investigation
            if result.status in ("unverifiable", "disputed") and self._agent:
                try:
                    # Determine why deterministic check failed
                    verification_context = {
                        "error": result.reason,
                        "status": result.status,
                        "deterministic_checks": result.deterministic_checks or {},
                    }
                    
                    # Run async agent investigation
                    import asyncio
                    agent_result = asyncio.run(
                        self._agent.investigate_deduction(deduction, settlement, verification_context)
                    )
                    result = agent_result
                except Exception as e:
                    # If agent fails, keep deterministic result
                    self._audit_repo.create(
                        FinanceAuditEvent(
                            settlement_id=settlement.id,
                            action="agent_investigation",
                            resource_type="deduction",
                            resource_id=deduction.id,
                            details={"error": str(e)},
                            outcome="error",
                        )
                    )
            
            # Persist result
            result.id = self._verification_repo.create(result)
            verification_results.append(result)
            
            if result.status == "verified":
                verified_count += 1
            elif result.status == "disputed":
                disputed_count += 1
            else:
                unverifiable_count += 1
        
        # Make settlement-level decision based on verification results
        total = len(deductions)
        verification_rate = verified_count / total if total > 0 else 0.0
        
        if verified_count == total:
            # All verified - approve
            final_decision = "approve"
            confidence = 0.95
            reason = f"All {total} deductions passed verification"
        elif disputed_count > 0:
            # Has disputes - flag
            final_decision = "flag"
            confidence = 0.6
            reason = f"{disputed_count} deductions have discrepancies requiring review"
        elif unverifiable_count > 0 and unverifiable_count / total > 0.3:
            # Too many unverifiable - escalate
            final_decision = "escalate"
            confidence = 0.4
            reason = f"{unverifiable_count} deductions cannot be verified ({unverifiable_count/total:.0%})"
        else:
            # Some unverifiable but not critical - flag
            final_decision = "flag"
            confidence = 0.7
            reason = f"{unverifiable_count} deductions have insufficient evidence"
        
        # Create decision record
        decision = SettlementDecision(
            settlement_id=settlement_id,
            final_decision=final_decision,
            reason=reason,
            verification_summary={
                "total": total,
                "verified": verified_count,
                "disputed": disputed_count,
                "unverifiable": unverifiable_count,
                "verification_rate": verification_rate,
            },
            gaps_identified=[
                f"{r.id}: {r.reason}"
                for r in verification_results
                if r.status != "verified"
            ],
            confidence=confidence,
            requires_human_review=final_decision in ("flag", "escalate"),
        )
        
        decision_id = self._decision_repo.create(decision)
        
        # Update settlement status based on decision
        # Map decision to status (decision uses "escalate", status uses "escalated")
        status_map = {
            "approve": "verified",
            "flag": "flagged",
            "escalate": "escalated",
        }
        new_status = status_map.get(final_decision, "flagged")
        self._settlement_repo.update(settlement_id, {"status": new_status})
        
        # Log decision event
        self._audit_repo.create(
            FinanceAuditEvent(
                settlement_id=settlement_id,
                action="decision_made",
                resource_type="settlement",
                resource_id=settlement_id,
                details={
                    "decision": final_decision,
                    "verification_rate": verification_rate,
                    "verified": verified_count,
                    "disputed": disputed_count,
                    "unverifiable": unverifiable_count,
                },
                confidence=confidence,
                outcome=final_decision,
            )
        )
        
        return self._decision_repo.get(decision_id)
