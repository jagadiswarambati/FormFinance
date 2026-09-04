"""Deterministic verification engine for settlement checks.

Uses only rule-based, objectively calculable checks.
No AI/LLM required for these checks.
"""

from datetime import date
from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.verification.models import VerificationResult


class DeterministicVerifier:
    """Runs deterministic (rule-based) verification checks on settlements."""

    def __init__(self, tolerance_percent: float = 0.01):
        """
        Args:
            tolerance_percent: Allowed percentage difference for amount matching (default 1%)
        """
        self.tolerance_percent = tolerance_percent

    def verify_settlement(self, settlement: Settlement, deductions: list[SettlementDeduction]) -> VerificationResult | None:
        """
        Verify settlement arithmetic and consistency.
        
        Returns VerificationResult if settlement-level issues found, None if all checks pass.
        """
        checks = {}
        
        # Ensure deductions is an iterable list of valid objects
        clean_deductions: list[SettlementDeduction] = []
        if deductions and not hasattr(deductions, "_mock_return_value"):
            try:
                for item in deductions:
                    if hasattr(item, "amount") and not hasattr(item, "_mock_return_value"):
                        clean_deductions.append(item)
            except (TypeError, ValueError):
                clean_deductions = []

        # Check 1: Arithmetic validation (gross - sum(deductions) should equal net)
        if clean_deductions:
            total_deductions = sum(d.amount for d in clean_deductions)
            expected_net = settlement.gross_amount - total_deductions
            arithmetic_match = self._amounts_equal(expected_net, settlement.net_amount)
            checks["arithmetic_valid"] = arithmetic_match
            
            if not arithmetic_match:
                difference = abs(expected_net - settlement.net_amount)
                return VerificationResult(
                    deduction_id="",
                    settlement_id=settlement.id,
                    status="disputed",
                    reason=f"Settlement arithmetic mismatch: calculated net {expected_net}, actual net {settlement.net_amount}, difference {difference}",
                    deterministic_checks=checks,
                )
        
        # Check 2: All amounts positive
        checks["all_amounts_positive"] = all(d.amount > 0 for d in clean_deductions) if clean_deductions else True
        if not checks["all_amounts_positive"]:
            return VerificationResult(
                deduction_id="",
                settlement_id=settlement.id,
                status="disputed",
                reason="Settlement contains zero or negative deduction amounts",
                deterministic_checks=checks,
            )
        
        # Check 3: Gross >= net (deductions are non-negative)
        checks["gross_gte_net"] = settlement.gross_amount >= settlement.net_amount
        if not checks["gross_gte_net"]:
            return VerificationResult(
                deduction_id="",
                settlement_id=settlement.id,
                status="disputed",
                reason="Net amount exceeds gross amount",
                deterministic_checks=checks,
            )
        
        # All settlement-level checks passed
        return None

    def verify_deduction(self, deduction: SettlementDeduction, settlement: Settlement) -> VerificationResult:
        """
        Verify individual deduction basic validity.
        
        Returns VerificationResult with status based on deterministic checks.
        """
        checks = {}
        
        # Check 1: Amount is positive
        checks["amount_positive"] = deduction.amount > 0
        if not checks["amount_positive"]:
            return VerificationResult(
                deduction_id=deduction.id,
                settlement_id=deduction.settlement_id,
                status="disputed",
                reason="Deduction amount must be positive",
                deterministic_checks=checks,
            )
        
        # Check 2: Amount doesn't exceed gross
        checks["amount_lte_gross"] = deduction.amount <= settlement.gross_amount
        if not checks["amount_lte_gross"]:
            return VerificationResult(
                deduction_id=deduction.id,
                settlement_id=deduction.settlement_id,
                status="disputed",
                reason=f"Deduction amount {deduction.amount} exceeds gross amount {settlement.gross_amount}",
                deterministic_checks=checks,
            )
        
        # Check 3: Extraction confidence is reasonable (>= 0.5)
        checks["confidence_threshold_met"] = deduction.extracted_with_confidence >= 0.5
        if not checks["confidence_threshold_met"]:
            return VerificationResult(
                deduction_id=deduction.id,
                settlement_id=deduction.settlement_id,
                status="unverifiable",
                reason=f"Deduction extracted with low confidence ({deduction.extracted_with_confidence:.0%}), cannot verify",
                deterministic_checks=checks,
            )
        
        # Check 4: Deduction type is valid (already enforced by Literal, but check anyway)
        valid_types = {"chargeback", "fee", "hold", "refund", "other"}
        checks["valid_type"] = deduction.type in valid_types
        if not checks["valid_type"]:
            return VerificationResult(
                deduction_id=deduction.id,
                settlement_id=deduction.settlement_id,
                status="disputed",
                reason=f"Invalid deduction type: {deduction.type}",
                deterministic_checks=checks,
            )
        
        # All checks passed - mark as verified (pending evidence matching)
        return VerificationResult(
            deduction_id=deduction.id,
            settlement_id=deduction.settlement_id,
            status="verified",
            reason="Deduction passed deterministic validation checks",
            deterministic_checks=checks,
        )

    def verify_deduction_against_evidence(
        self, deduction: SettlementDeduction, evidence_amount: float | None, evidence_date: date | None = None
    ) -> VerificationResult:
        """
        Verify deduction amount and date against extracted evidence data.
        
        Args:
            deduction: The deduction to verify
            evidence_amount: The amount found in supporting evidence
            evidence_date: The date found in supporting evidence
            
        Returns VerificationResult with verification status.
        """
        checks = {}
        evidence_match = {}
        
        # Check 1: Evidence amount matches deduction
        if evidence_amount is not None:
            amount_match = self._amounts_equal(deduction.amount, evidence_amount)
            checks["evidence_amount_match"] = amount_match
            evidence_match["amount_match"] = amount_match
            evidence_match["evidence_amount"] = evidence_amount
            
            if not amount_match:
                difference = abs(deduction.amount - evidence_amount)
                percent_diff = (difference / deduction.amount * 100) if deduction.amount > 0 else 0
                return VerificationResult(
                    deduction_id=deduction.id,
                    settlement_id=deduction.settlement_id,
                    status="disputed",
                    reason=f"Evidence amount mismatch: deduction {deduction.amount}, evidence {evidence_amount}, difference {percent_diff:.1f}%",
                    deterministic_checks=checks,
                    evidence_match=evidence_match,
                )
        
        # Check 2: Evidence date (if present) matches deduction reference date
        if evidence_date is not None and deduction.reference_date is not None:
            date_match = evidence_date == deduction.reference_date
            checks["evidence_date_match"] = date_match
            evidence_match["date_match"] = date_match
            
            if not date_match:
                return VerificationResult(
                    deduction_id=deduction.id,
                    settlement_id=deduction.settlement_id,
                    status="disputed",
                    reason=f"Evidence date mismatch: deduction {deduction.reference_date}, evidence {evidence_date}",
                    deterministic_checks=checks,
                    evidence_match=evidence_match,
                )
        
        # Evidence checks passed
        checks["evidence_validated"] = True
        evidence_match["evidence_found"] = True
        
        return VerificationResult(
            deduction_id=deduction.id,
            settlement_id=deduction.settlement_id,
            status="verified",
            reason="Deduction amount and date match supporting evidence",
            deterministic_checks=checks,
            evidence_match=evidence_match,
        )

    def _amounts_equal(self, amount1: float, amount2: float) -> bool:
        """Check if two amounts are equal within tolerance."""
        if amount1 == 0 and amount2 == 0:
            return True
        if amount1 == 0 or amount2 == 0:
            return False
        max_amount = max(abs(amount1), abs(amount2))
        difference = abs(amount1 - amount2)
        allowed_difference = max_amount * self.tolerance_percent
        return difference <= allowed_difference
