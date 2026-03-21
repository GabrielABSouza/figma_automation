"""LangGraph pipeline definition — wires all agents into a StateGraph.

MVP pipeline: Planner → UI Generator → Mapper → Validator
Each node is wrapped with retry logic. Conditional edges halt the pipeline
on error to avoid cascading failures.
"""

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents import generate_ui, map_to_design_system, plan, validate
from backend.orchestrator.state import PipelineState

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 2


def _wrap_with_retry(
    name: str,
    agent_fn: Callable[[PipelineState], Coroutine[Any, Any, PipelineState]],
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Callable[[PipelineState], Coroutine[Any, Any, PipelineState]]:
    """Wrap an agent function with retry logic.

    On exception, retries up to max_retries times. After exhausting retries,
    captures the error in state.errors and returns the state without raising.
    """

    async def wrapper(state: PipelineState) -> PipelineState:
        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                return await agent_fn(state)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Node '%s' failed (attempt %d/%d): %s",
                    name,
                    attempt,
                    max_retries,
                    exc,
                )
        error_msg = f"Node '{name}' failed after {max_retries} retries: {last_error}"
        logger.error(error_msg)
        state.errors.append(error_msg)
        return state

    wrapper.__name__ = f"{name}_with_retry"
    return wrapper


def _should_continue(state: PipelineState) -> str:
    """Route to END if errors exist, otherwise continue to next node."""
    if state.errors:
        return "stop"
    return "continue"


def build_graph(max_retries: int = DEFAULT_MAX_RETRIES) -> StateGraph:
    """Construct the LangGraph StateGraph for the MVP pipeline.

    Pipeline: START → plan → generate_ui → map_to_design_system → validate → END
    """
    graph = StateGraph(PipelineState)

    graph.add_node("plan", _wrap_with_retry("plan", plan, max_retries))
    graph.add_node("generate_ui", _wrap_with_retry("generate_ui", generate_ui, max_retries))
    graph.add_node(
        "map_to_design_system",
        _wrap_with_retry("map_to_design_system", map_to_design_system, max_retries),
    )
    graph.add_node("validate", _wrap_with_retry("validate", validate, max_retries))

    graph.add_edge(START, "plan")
    graph.add_conditional_edges(
        "plan", _should_continue, {"continue": "generate_ui", "stop": END}
    )
    graph.add_conditional_edges(
        "generate_ui", _should_continue, {"continue": "map_to_design_system", "stop": END}
    )
    graph.add_conditional_edges(
        "map_to_design_system", _should_continue, {"continue": "validate", "stop": END}
    )
    graph.add_edge("validate", END)

    return graph


pipeline = build_graph().compile()


async def run_pipeline(raw_input: str) -> PipelineState:
    """Execute the full pipeline from raw user input to validated UI.

    Args:
        raw_input: The user's product description / prompt.

    Returns:
        PipelineState with all fields populated up to the point of success
        (or with errors if a node failed).
    """
    initial_state = PipelineState(raw_input=raw_input)
    result = await pipeline.ainvoke(initial_state)
    return PipelineState.model_validate(result)
