"""Tests for the LLM provider factory."""

from unittest.mock import patch

from backend.llm.factory import create_llm_provider
from backend.llm.gemini import GeminiProvider


class TestCreateLLMProvider:
    def test_creates_gemini_provider(self) -> None:
        with patch("backend.llm.factory.settings") as mock_settings:
            mock_settings.gemini_api_key = "test-key"
            mock_settings.gemini_model = "gemini-2.5-flash"
            mock_settings.gemini_temperature = 0.1
            mock_settings.gemini_max_output_tokens = 8192
            mock_settings.gemini_max_retries = 2

            provider = create_llm_provider()

        assert isinstance(provider, GeminiProvider)
        assert provider._model == "gemini-2.5-flash"
        assert provider._temperature == 0.1
        assert provider._max_output_tokens == 8192
        assert provider._max_retries == 2

    def test_uses_custom_settings(self) -> None:
        with patch("backend.llm.factory.settings") as mock_settings:
            mock_settings.gemini_api_key = "custom-key"
            mock_settings.gemini_model = "gemini-2.5-pro"
            mock_settings.gemini_temperature = 0.7
            mock_settings.gemini_max_output_tokens = 4096
            mock_settings.gemini_max_retries = 3

            provider = create_llm_provider()

        assert provider._model == "gemini-2.5-pro"
        assert provider._temperature == 0.7
        assert provider._max_output_tokens == 4096
        assert provider._max_retries == 3
