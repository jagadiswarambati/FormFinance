from formwise_api.ai_provider.interfaces import AIProvider
from formwise_api.ai_provider.ollama import OllamaProvider
from formwise_api.config import Settings


def get_ai_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider != "ollama":
        raise RuntimeError("The selected AI provider is disabled.")
    return OllamaProvider(settings.ollama_base_url, settings.ollama_model, settings.ollama_temperature, settings.ollama_context_length, settings.ollama_max_tokens, settings.ollama_timeout_seconds)
