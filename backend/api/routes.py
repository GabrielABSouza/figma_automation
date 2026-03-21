"""API route handlers for the Figma Automation Pipeline."""

import logging

from fastapi import APIRouter

from backend.api.models import (
    DesignSystemResponse,
    ErrorResponse,
    GenerateUIRequest,
    GenerateUIResponse,
    NotImplementedResponse,
    ScreenResponse,
    UIComponentResponse,
    ValidationResultResponse,
)
from backend.design_system.loader import load_design_system
from backend.orchestrator.graph import run_pipeline
from backend.orchestrator.state import UIComponent, ValidatedUI

logger = logging.getLogger(__name__)

router = APIRouter()

SCHEMA_VERSION = "1.0.0"


def _convert_component(component: UIComponent) -> UIComponentResponse:
    """Convert internal UIComponent to API response model (recursive)."""
    return UIComponentResponse(
        id=component.id,
        type=component.type,
        props=component.props,
        tokens=component.tokens,
        children=[_convert_component(c) for c in component.children],
    )


def _convert_screen(validated: ValidatedUI) -> ScreenResponse:
    """Convert internal ValidatedUI to API response model."""
    return ScreenResponse(
        screen_name=validated.screen_name,
        components=[_convert_component(c) for c in validated.components],
        tokens=validated.tokens,
        metadata=validated.metadata,
        validation=ValidationResultResponse(
            is_valid=validated.validation.is_valid,
            errors=validated.validation.errors,
            warnings=validated.validation.warnings,
        ),
    )


@router.post(
    "/generate-ui",
    response_model=GenerateUIResponse,
    responses={500: {"model": ErrorResponse}},
)
async def generate_ui(request: GenerateUIRequest) -> GenerateUIResponse:
    """Full pipeline: prompt -> structured UI JSON.

    Runs the complete pipeline (Planner -> UI Generator -> Mapper -> Validator)
    and returns the validated screens.
    """
    logger.info("POST /generate-ui — prompt: %s", request.prompt[:80])

    try:
        state = await run_pipeline(request.prompt)
    except Exception as exc:
        logger.exception("Unexpected error in pipeline execution")
        return GenerateUIResponse(
            success=False,
            errors=[f"Pipeline execution failed: {exc}"],
            metadata={"prompt": request.prompt, "schema_version": SCHEMA_VERSION},
        )

    screens = [_convert_screen(v) for v in state.validated_uis]
    has_pipeline_errors = len(state.errors) > 0
    success = not has_pipeline_errors and len(screens) > 0

    return GenerateUIResponse(
        success=success,
        screens=screens,
        errors=state.errors,
        metadata={
            "prompt": request.prompt,
            "screen_count": len(screens),
            "all_screens_valid": all(s.validation.is_valid for s in screens)
            if screens
            else False,
            "schema_version": SCHEMA_VERSION,
        },
    )


@router.post("/iterate-ui")
async def iterate_ui(
    pipeline_run_id: str, feedback: str
) -> NotImplementedResponse:
    """Partial re-run with user feedback. (Post-MVP)"""
    return NotImplementedResponse()


@router.get(
    "/design-system",
    response_model=DesignSystemResponse,
    responses={500: {"model": ErrorResponse}},
)
async def get_design_system() -> DesignSystemResponse:
    """Return the active design system (tokens, components, rules)."""
    ds = load_design_system()
    return DesignSystemResponse(
        tokens=ds.tokens,
        components=[c.model_dump() for c in ds.components],
        rules=ds.rules,
    )
