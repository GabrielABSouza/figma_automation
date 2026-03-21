"""Screen Decomposer Agent — breaks screens into atomic sections (post-MVP)."""

from backend.orchestrator.state import PipelineState


async def decompose(state: PipelineState) -> PipelineState:
    """Decompose each planned screen into atomic sections and content types."""
    # TODO: implement with LLM call (post-MVP)
    return state
