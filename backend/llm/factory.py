from backend.config import settings
from backend.llm.gemini import GeminiProvider
from backend.llm.provider import LLMProvider

_provider: LLMProvider | None = None


def create_llm_provider() -> LLMProvider:
    """Create a new LLM provider instance from settings."""
    return GeminiProvider(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        temperature=settings.gemini_temperature,
        max_output_tokens=settings.gemini_max_output_tokens,
        max_retries=settings.gemini_max_retries,
    )


def get_llm() -> LLMProvider:
    """Return the singleton LLM provider, creating it on first call.

    Agents call this at invocation time. Tests patch this function
    to inject a mock provider.
    """
    global _provider  # noqa: PLW0603
    if _provider is None:
        _provider = create_llm_provider()
    return _provider


def reset_llm() -> None:
    """Reset the cached provider (used in tests)."""
    global _provider  # noqa: PLW0603
    _provider = None
