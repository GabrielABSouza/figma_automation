from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMProvider(Protocol):
    """Abstract LLM provider interface — swap Gemini/Claude/GPT without changing agent code."""

    async def generate(
        self,
        prompt: str,
        output_schema: type[T],
        *,
        system_prompt: str | None = None,
    ) -> T:
        """Generate structured output from a prompt.

        Args:
            prompt: The user/task prompt to send to the LLM.
            output_schema: A Pydantic model class. The LLM response will be
                validated and returned as an instance of this model.
            system_prompt: Optional system-level instructions that guide
                the LLM's behavior (e.g., agent role definition).

        Returns:
            An instance of output_schema populated from the LLM response.

        Raises:
            LLMProviderError: If the LLM call fails after all retries.
            LLMValidationError: If the response cannot be parsed into output_schema.
        """
        ...


class LLMProviderError(Exception):
    """Raised when the LLM API call fails after all retry attempts."""

    def __init__(self, message: str, *, provider: str, status_code: int | None = None) -> None:
        self.provider = provider
        self.status_code = status_code
        super().__init__(message)


class LLMValidationError(Exception):
    """Raised when the LLM response cannot be parsed into the expected schema."""

    def __init__(self, message: str, *, raw_response: str, schema_name: str) -> None:
        self.raw_response = raw_response
        self.schema_name = schema_name
        super().__init__(message)
