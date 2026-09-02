"""Mock AI provider for testing without Ollama."""

import time
from formwise_api.ai_provider.models import AIProviderRequest, AIProviderResult


class MockAIProvider:
    """Mock AI provider for testing settlement verification flow."""
    
    def __init__(self):
        pass
    
    def provider_name(self) -> str:
        return "mock"
    
    async def health_check(self) -> bool:
        return True
    
    async def generate_response(self, request: AIProviderRequest) -> AIProviderResult:
        """Generate mock response based on structured context."""
        
        started = time.perf_counter()
        
        # Extract deduction context
        context = request.structured_context
        deduction = context.get("deduction", {})
        verification_context = context.get("verification_context", {})
        
        # Mock investigation logic
        deduction_type = deduction.get("type", "")
        amount = deduction.get("amount", 0)
        confidence = deduction.get("extracted_confidence", 0)
        error_reason = verification_context.get("error", "")
        
        # Simulate investigation decision
        if "Low confidence" in error_reason and confidence < 0.5:
            # Low confidence deduction - mark as unverifiable
            decision = "unverifiable"
            reasoning = f"Extraction confidence too low ({confidence:.0%}), cannot verify without additional evidence"
            agent_confidence = 0.3
        elif "arithmetic" in error_reason.lower():
            # Arithmetic issues - mark as disputed
            decision = "disputed"
            reasoning = "Settlement arithmetic discrepancy detected during verification"
            agent_confidence = 0.8
        elif deduction_type in ("fee", "hold", "refund"):
            # Common deduction types - likely verified if amount reasonable
            if amount > 0:
                decision = "verified"
                reasoning = f"Standard {deduction_type} deduction with reasonable amount"
                agent_confidence = 0.9
            else:
                decision = "disputed"
                reasoning = f"Invalid {deduction_type} deduction amount"
                agent_confidence = 0.8
        else:
            # Other types - conservative estimate
            decision = "unverifiable"
            reasoning = "Unable to verify deduction type"
            agent_confidence = 0.4
        
        # Build response
        content = {
            "reasoning": reasoning,
            "decision": decision,
            "confidence": agent_confidence,
            "tools_used": ["verify_reference", "compare_amounts"],
            "evidence_checked": True,
        }
        
        return AIProviderResult(
            content=content,
            provider=self.provider_name(),
            model="mock-agent",
            latency_ms=round((time.perf_counter() - started) * 1000),
            token_usage=None,
        )
