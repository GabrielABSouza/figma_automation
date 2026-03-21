"""Tests for GeminiProvider — uses mocking, no real API calls."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai import errors
from pydantic import BaseModel

from backend.llm.gemini import GeminiProvider
from backend.llm.provider import LLMProviderError, LLMValidationError


class SampleOutput(BaseModel):
    name: str
    score: int


class TestGeminiProviderInit:
    def test_raises_on_empty_api_key(self) -> None:
        with pytest.raises(ValueError, match="API key is required"):
            GeminiProvider(api_key="")

    def test_creates_with_valid_key(self) -> None:
        provider = GeminiProvider(api_key="test-key")
        assert provider._model == "gemini-2.5-flash"

    def test_custom_model_config(self) -> None:
        provider = GeminiProvider(
            api_key="test-key",
            model="gemini-2.5-pro",
            temperature=0.5,
            max_output_tokens=4096,
            max_retries=3,
        )
        assert provider._model == "gemini-2.5-pro"
        assert provider._temperature == 0.5
        assert provider._max_output_tokens == 4096
        assert provider._max_retries == 3


class TestGeminiProviderGenerate:
    @pytest.fixture
    def provider(self) -> GeminiProvider:
        return GeminiProvider(api_key="test-key")

    async def test_successful_generation(self, provider: GeminiProvider) -> None:
        mock_response = MagicMock()
        mock_response.text = '{"name": "test", "score": 42}'

        with patch.object(
            provider._client.aio.models,
            "generate_content",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.generate("test prompt", SampleOutput)

        assert isinstance(result, SampleOutput)
        assert result.name == "test"
        assert result.score == 42

    async def test_with_system_prompt(self, provider: GeminiProvider) -> None:
        mock_response = MagicMock()
        mock_response.text = '{"name": "test", "score": 1}'

        with patch.object(
            provider._client.aio.models,
            "generate_content",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_gen:
            await provider.generate(
                "test prompt",
                SampleOutput,
                system_prompt="You are a test agent.",
            )

        call_kwargs = mock_gen.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        assert config.system_instruction == "You are a test agent."

    async def test_empty_response_raises(self, provider: GeminiProvider) -> None:
        mock_response = MagicMock()
        mock_response.text = ""

        with patch.object(
            provider._client.aio.models,
            "generate_content",
            new_callable=AsyncMock,
            return_value=mock_response,
        ), pytest.raises(LLMProviderError, match="empty response"):
            await provider.generate("test prompt", SampleOutput)

    async def test_none_response_text_raises(self, provider: GeminiProvider) -> None:
        mock_response = MagicMock()
        mock_response.text = None

        with patch.object(
            provider._client.aio.models,
            "generate_content",
            new_callable=AsyncMock,
            return_value=mock_response,
        ), pytest.raises(LLMProviderError, match="empty response"):
            await provider.generate("test prompt", SampleOutput)

    async def test_validation_retry_then_success(self, provider: GeminiProvider) -> None:
        bad_response = MagicMock()
        bad_response.text = '{"invalid": true}'

        good_response = MagicMock()
        good_response.text = '{"name": "fixed", "score": 99}'

        with patch.object(
            provider._client.aio.models,
            "generate_content",
            new_callable=AsyncMock,
            side_effect=[bad_response, good_response],
        ):
            result = await provider.generate("test prompt", SampleOutput)

        assert result.name == "fixed"
        assert result.score == 99

    async def test_validation_exhausted_raises(self, provider: GeminiProvider) -> None:
        bad_response = MagicMock()
        bad_response.text = '{"invalid": true}'

        with patch.object(
            provider._client.aio.models,
            "generate_content",
            new_callable=AsyncMock,
            return_value=bad_response,
        ), pytest.raises(LLMValidationError, match="Failed to get valid response"):
            await provider.generate("test prompt", SampleOutput)

    async def test_api_error_raises_after_retries(self, provider: GeminiProvider) -> None:
        api_error = errors.APIError(429, {"error": {"message": "quota exceeded"}})

        with patch.object(
            provider._client.aio.models,
            "generate_content",
            new_callable=AsyncMock,
            side_effect=api_error,
        ), pytest.raises(LLMProviderError, match="quota exceeded"):
            await provider.generate("test prompt", SampleOutput)


class TestGeminiProviderProtocolCompliance:
    def test_satisfies_llm_provider_protocol(self) -> None:
        from backend.llm.provider import LLMProvider

        provider = GeminiProvider(api_key="test-key")
        assert isinstance(provider, LLMProvider)
