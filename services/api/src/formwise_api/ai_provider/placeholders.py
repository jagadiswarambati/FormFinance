from formwise_api.ai_provider.models import AIProviderRequest, AIProviderResult


class DisabledProvider:
    def __init__(self, name: str) -> None:
        self._name = name

    def provider_name(self) -> str:
        return self._name

    async def health_check(self) -> bool:
        return False

    async def generate_response(self, request: AIProviderRequest) -> AIProviderResult:
        raise RuntimeError(f"{self._name} is disabled by the frozen V1 architecture.")
