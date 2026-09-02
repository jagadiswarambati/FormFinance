"""AI Finance Verification Agent for investigating ambiguous settlement deductions."""

import json
import uuid
from datetime import date
from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.verification.models import VerificationResult
from formwise_api.evidence.models import EvidenceLink
from formwise_api.audit.finance_audit_events import FinanceAuditEvent
from formwise_api.audit.repository import FinanceAuditEventRepository
from formwise_api.ai_provider.models import AIProviderRequest, AIProviderResult
from formwise_api.ai_provider.interfaces import AIProvider


class SettlementFinanceAgent:
    """AI agent for investigating ambiguous settlement deductions."""
    
    def __init__(self, ai_provider: AIProvider, audit_repo: FinanceAuditEventRepository):
        self._ai_provider = ai_provider
        self._audit_repo = audit_repo
        self._correlation_id = str(uuid.uuid4())
    
    async def investigate_deduction(
        self,
        deduction: SettlementDeduction,
        settlement: Settlement,
        verification_context: dict,
    ) -> VerificationResult:
        """
        Investigate an ambiguous deduction using AI.
        
        Args:
            deduction: The deduction to investigate
            settlement: The parent settlement
            verification_context: Context from failed deterministic checks
                                 (e.g., {"error": "Low confidence", "confidence": 0.45})
        
        Returns:
            Enhanced VerificationResult with agent findings
        """
        # Log investigation start
        self._audit_repo.create(
            FinanceAuditEvent(
                settlement_id=settlement.id,
                action="agent_investigation",
                resource_type="deduction",
                resource_id=deduction.id,
                details={
                    "investigation_reason": verification_context.get("error", "Unknown"),
                    "deduction_type": deduction.type,
                    "amount": deduction.amount,
                },
            )
        )
        
        # Build agent request
        request = self._build_investigation_request(
            deduction, settlement, verification_context
        )
        
        # Call AI provider
        try:
            result: AIProviderResult = await self._ai_provider.generate_response(request)
        except Exception as e:
            # If AI fails, mark as unverifiable
            return VerificationResult(
                deduction_id=deduction.id,
                settlement_id=settlement.id,
                status="unverifiable",
                reason=f"Agent investigation failed: {str(e)}",
                agent_investigation={
                    "error": str(e),
                    "investigation_attempted": True,
                },
            )
        
        # Parse agent response
        agent_response = result.content
        
        # Log investigation result
        self._audit_repo.create(
            FinanceAuditEvent(
                settlement_id=settlement.id,
                action="agent_investigation",
                resource_type="deduction",
                resource_id=deduction.id,
                details={
                    "agent_reasoning": agent_response.get("reasoning", ""),
                    "agent_decision": agent_response.get("decision", ""),
                    "agent_confidence": agent_response.get("confidence", 0),
                },
                confidence=float(agent_response.get("confidence", 0)),
                outcome=agent_response.get("decision", "unverifiable"),
            )
        )
        
        # Extract decision from agent
        agent_decision = agent_response.get("decision", "unverifiable")
        agent_confidence = float(agent_response.get("confidence", 0))
        reasoning = agent_response.get("reasoning", "Agent investigation inconclusive")
        
        # Map agent decision to verification status
        if agent_decision == "verified":
            status = "verified"
            reason = f"Agent verified: {reasoning}"
        elif agent_decision == "disputed":
            status = "disputed"
            reason = f"Agent identified discrepancy: {reasoning}"
        else:  # unverifiable or unknown
            status = "unverifiable"
            reason = f"Agent could not confirm: {reasoning}"
        
        return VerificationResult(
            deduction_id=deduction.id,
            settlement_id=settlement.id,
            status=status,
            reason=reason,
            agent_investigation={
                "reasoning": reasoning,
                "decision": agent_decision,
                "confidence": agent_confidence,
                "tools_used": agent_response.get("tools_used", []),
                "evidence_checked": agent_response.get("evidence_checked", False),
            },
        )
    
    def _build_investigation_request(
        self,
        deduction: SettlementDeduction,
        settlement: Settlement,
        verification_context: dict,
    ) -> AIProviderRequest:
        """Build an AIProviderRequest for agent investigation."""
        
        structured_context = {
            "settlement": {
                "id": settlement.id,
                "source": settlement.source,
                "settlement_date": settlement.settlement_date.isoformat(),
                "gross_amount": settlement.gross_amount,
                "net_amount": settlement.net_amount,
            },
            "deduction": {
                "id": deduction.id,
                "type": deduction.type,
                "description": deduction.description,
                "amount": deduction.amount,
                "reference_id": deduction.reference_id,
                "reference_date": deduction.reference_date.isoformat() if deduction.reference_date else None,
                "extracted_confidence": deduction.extracted_with_confidence,
            },
            "verification_context": verification_context,
        }
        
        system_instruction = """You are a financial verification agent specializing in settlement deduction analysis.
Your task is to investigate ambiguous or problematic settlement deductions.

You have access to these tools:
1. compare_amounts: Compare expected vs actual amounts
2. verify_reference: Verify reference IDs and dates
3. check_deduction_type: Validate deduction type classification
4. search_evidence: Search for supporting evidence

For each investigation:
1. Analyze the deduction details
2. Use available tools to cross-check
3. Provide clear reasoning
4. Make a final decision: verified, disputed, or unverifiable
5. Provide confidence 0.0-1.0

Return a JSON object with:
{
    "reasoning": "your reasoning",
    "decision": "verified|disputed|unverifiable",
    "confidence": 0.0-1.0,
    "tools_used": ["tool1", "tool2"],
    "evidence_checked": true/false
}"""
        
        user_message = self._build_user_message(deduction, settlement, verification_context)
        
        return AIProviderRequest(
            system_instruction=system_instruction,
            structured_context=structured_context,
            history=[],
            user_message=user_message,
            response_schema={
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string"},
                    "decision": {"type": "string", "enum": ["verified", "disputed", "unverifiable"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "tools_used": {"type": "array", "items": {"type": "string"}},
                    "evidence_checked": {"type": "boolean"},
                },
                "required": ["reasoning", "decision", "confidence"],
            },
            locale="en",
            task_type="settlement_deduction_verification",
            correlation_id=self._correlation_id,
        )
    
    def _build_user_message(
        self,
        deduction: SettlementDeduction,
        settlement: Settlement,
        verification_context: dict,
    ) -> str:
        """Build user message for agent."""
        
        message = f"""Please investigate this settlement deduction:

Deduction Type: {deduction.type}
Description: {deduction.description}
Amount: {deduction.amount}
Reference ID: {deduction.reference_id or 'None'}
Reference Date: {deduction.reference_date or 'None'}
Extraction Confidence: {deduction.extracted_with_confidence:.0%}

Verification Issue: {verification_context.get('error', 'Unknown')}

Settlement Context:
- Source: {settlement.source}
- Settlement Date: {settlement.settlement_date}
- Gross Amount: {settlement.gross_amount}
- Net Amount: {settlement.net_amount}

Please use the available tools to:
1. Compare amounts (deduction vs settlement)
2. Verify reference information
3. Check deduction type validity
4. Search for any supporting evidence

Based on your investigation, determine if this deduction is:
- VERIFIED: Legitimate deduction with supporting evidence
- DISPUTED: Evidence of discrepancy or fraud
- UNVERIFIABLE: Insufficient information to confirm

Provide your reasoning and confidence level."""
        
        return message
