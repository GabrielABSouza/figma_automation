import json
import logging
from typing import Any, TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from backend.llm.provider import LLMProviderError, LLMValidationError

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


def _has_ref(schema: Any) -> bool:
    """Check if a JSON schema contains $ref (recursive or cross-referenced types)."""
    if isinstance(schema, dict):
        if "$ref" in schema:
            return True
        return any(_has_ref(v) for v in schema.values())
    if isinstance(schema, list):
        return any(_has_ref(item) for item in schema)
    return False


def _strip_additional_properties(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively strip 'additionalProperties' from a JSON schema.

    The Gemini API (non-VertexAI) does not support additionalProperties.
    Pydantic v2 emits it for dict[str, Any] fields, so we clean it here.
    """
    schema.pop("additionalProperties", None)

    for prop in schema.get("properties", {}).values():
        if isinstance(prop, dict):
            _strip_additional_properties(prop)

    if "items" in schema and isinstance(schema["items"], dict):
        _strip_additional_properties(schema["items"])

    for key in ("allOf", "anyOf", "oneOf"):
        if key in schema:
            for sub in schema[key]:
                if isinstance(sub, dict):
                    _strip_additional_properties(sub)

    for ref_def in schema.get("$defs", {}).values():
        if isinstance(ref_def, dict):
            _strip_additional_properties(ref_def)

    return schema


class GeminiProvider:
    """Google Gemini LLM provider implementing the LLMProvider protocol.

    Uses the google-genai SDK async client with native structured JSON output.
    The SDK handles HTTP-level retries (429/5xx) automatically. This class adds
    application-level retry when JSON passes HTTP but fails Pydantic validation.

    For schemas with recursive $ref (e.g., UIComponent with children), the SDK
    cannot handle response_schema natively, so the schema is injected into the
    prompt text instead and only response_mime_type="application/json" is used.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.1,
        max_output_tokens: int = 8192,
        max_retries: int = 2,
    ) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required")
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._max_retries = max_retries

    async def generate(
        self,
        prompt: str,
        output_schema: type[T],
        *,
        system_prompt: str | None = None,
    ) -> T:
        """Generate structured output from Gemini."""
        json_schema = output_schema.model_json_schema()
        uses_ref = _has_ref(json_schema)

        if uses_ref:
            # Recursive schemas can't be passed to response_schema (SDK hits
            # infinite recursion). Instead, inject the schema into the prompt
            # and rely on response_mime_type to enforce JSON output.
            schema_text = json.dumps(json_schema, indent=2)
            schema_suffix = (
                f"\n\nYou MUST output valid JSON matching this exact schema:\n"
                f"```json\n{schema_text}\n```"
            )
            prompt = prompt + schema_suffix
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=self._temperature,
                max_output_tokens=self._max_output_tokens,
            )
        else:
            clean_schema = _strip_additional_properties(json_schema)
            config = types.GenerateContentConfig(
                response_schema=clean_schema,
                response_mime_type="application/json",
                temperature=self._temperature,
                max_output_tokens=self._max_output_tokens,
            )

        if system_prompt:
            config.system_instruction = system_prompt

        current_prompt = prompt
        last_error: Exception | None = None
        raw_text = ""

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=current_prompt,
                    config=config,
                )

                raw_text = response.text or ""
                if not raw_text:
                    raise LLMProviderError(
                        f"Gemini returned empty response on attempt {attempt}",
                        provider="gemini",
                    )

                return output_schema.model_validate_json(raw_text)

            except ValidationError as exc:
                logger.warning(
                    "Gemini response failed schema validation (attempt %d/%d): %s",
                    attempt,
                    self._max_retries,
                    exc.error_count(),
                )
                last_error = exc
                # Augment prompt with validation feedback for next attempt
                current_prompt = (
                    f"{prompt}\n\n"
                    f"[VALIDATION ERROR — your previous response had these issues, "
                    f"please fix them:\n{exc}]"
                )

            except errors.APIError as exc:
                logger.error(
                    "Gemini API error (attempt %d/%d): %s %s",
                    attempt,
                    self._max_retries,
                    exc.code,
                    exc.message,
                )
                last_error = exc
                if attempt == self._max_retries:
                    raise LLMProviderError(
                        f"Gemini API error after {self._max_retries} attempts: {exc.message}",
                        provider="gemini",
                        status_code=exc.code,
                    ) from exc

        # Exhausted retries due to validation errors
        raise LLMValidationError(
            f"Failed to get valid response after {self._max_retries} attempts",
            raw_response=raw_text,
            schema_name=output_schema.__name__,
        ) from last_error
