"""Input Interpreter Agent — parses user input and extracts product intent."""

from backend.orchestrator.state import InterpretedInput, PipelineState


async def interpret(state: PipelineState) -> PipelineState:
    """Parse raw input and extract product type, goals, and required screens."""
    # TODO: implement with LLM call
    state.interpreted = InterpretedInput(raw_input=state.raw_input)
    return state
