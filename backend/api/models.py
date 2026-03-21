"""Request and response models for the API layer."""

from typing import Any

from pydantic import BaseModel, Field

# ─── Request Models ───


class GenerateUIRequest(BaseModel):
    """Request body for POST /generate-ui."""

    prompt: str = Field(
        ...,
        min_length=1,
        description="Product description or intent prompt.",
        examples=["Build a SaaS dashboard for financial tracking"],
    )


# ─── Nested Response Models ───


class UIComponentResponse(BaseModel):
    """A single UI component in the response tree (recursive)."""

    id: str
    type: str
    props: dict[str, Any] = Field(default_factory=dict)
    tokens: dict[str, str] = Field(default_factory=dict)
    children: list["UIComponentResponse"] = Field(default_factory=list)


class ValidationResultResponse(BaseModel):
    """Validation status for a single screen."""

    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ScreenResponse(BaseModel):
    """A single validated screen in the API response."""

    screen_name: str
    components: list[UIComponentResponse] = Field(default_factory=list)
    tokens: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    validation: ValidationResultResponse = Field(
        default_factory=ValidationResultResponse
    )


# ─── Top-Level Response Models ───


class GenerateUIResponse(BaseModel):
    """Response body for POST /generate-ui."""

    success: bool
    screens: list[ScreenResponse] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DesignSystemResponse(BaseModel):
    """Response body for GET /design-system."""

    tokens: dict[str, Any] = Field(default_factory=dict)
    components: list[dict[str, Any]] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standardized error response for unexpected failures."""

    success: bool = False
    error: str
    detail: str | None = None


class NotImplementedResponse(BaseModel):
    """Response for endpoints not yet implemented."""

    status: str = "not_implemented"
    message: str = "This endpoint is not yet implemented."
