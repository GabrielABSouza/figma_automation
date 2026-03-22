"""LangGraph pipeline definition — wires all agents into a StateGraph.

MVP pipeline: Planner → UI Generator → Mapper → Validator
Each node is wrapped with retry logic. Conditional edges halt the pipeline
on error to avoid cascading failures.
"""

import json
import logging
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents import generate_ui, map_to_design_system, plan, validate
from backend.agents.html_generator import generate_html
from backend.converters.html_to_figma import convert_html_to_figma_tree
from backend.orchestrator.state import FigmaTreeScreen, PipelineState

logger = logging.getLogger(__name__)

DEBUG_DIR = Path(__file__).resolve().parent.parent.parent / "debug"

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
                result = await agent_fn(state)
                logger.info("Node '%s' completed successfully", name)
                return result
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


# ─── Design Pipeline (v2): Planner → HTML Generator → Converter ───


def _log_tree_summary(node: dict, indent: int = 0, max_depth: int = 3) -> list[str]:
    """Build a human-readable summary of the Figma tree structure."""
    if indent > max_depth:
        n = len(node.get("children", []))
        return [f"{'  ' * indent}... ({n} children)"] if n else []

    prefix = "  " * indent
    t = node.get("type", "?")
    parts = [t]
    if node.get("name"):
        parts.append(f'"{node["name"]}"')
    if node.get("characters"):
        parts.append(f'"{node["characters"][:25]}"')
    if node.get("layoutMode"):
        parts.append(node["layoutMode"])
    if node.get("layoutGrow"):
        parts.append(f"grow={node['layoutGrow']}")
    if node.get("layoutAlign"):
        parts.append(f"align={node['layoutAlign']}")
    if node.get("textAutoResize"):
        parts.append(f"TAR={node['textAutoResize']}")
    if node.get("width"):
        parts.append(f"w={node['width']}")
    if node.get("height"):
        parts.append(f"h={node['height']}")
    if node.get("primaryAxisSizingMode"):
        parts.append(f"primary={node['primaryAxisSizingMode']}")
    if node.get("counterAxisSizingMode"):
        parts.append(f"counter={node['counterAxisSizingMode']}")

    lines = [f"{prefix}{' '.join(parts)}"]
    for child in node.get("children", []):
        lines.extend(_log_tree_summary(child, indent + 1, max_depth))
    return lines


async def _convert_html_to_figma(state: PipelineState) -> PipelineState:
    """Convert generated HTML screens to Figma node trees (no LLM needed)."""
    DEBUG_DIR.mkdir(exist_ok=True)

    for screen_html in state.screen_htmls:
        logger.info(
            "Converting screen '%s' (HTML length: %d)",
            screen_html.screen_name,
            len(screen_html.html),
        )

        # Save raw HTML for debugging
        html_file = DEBUG_DIR / f"html_{screen_html.screen_name}.html"
        html_file.write_text(screen_html.html)

        tree = convert_html_to_figma_tree(screen_html.html, screen_html.screen_name)

        # Save JSON tree for debugging
        tree_file = DEBUG_DIR / f"tree_{screen_html.screen_name}.json"
        tree_file.write_text(json.dumps(tree, indent=2))

        # Log tree structure summary
        summary = "\n".join(_log_tree_summary(tree))
        logger.info("Tree structure for '%s':\n%s", screen_html.screen_name, summary)

        state.figma_trees.append(
            FigmaTreeScreen(screen_name=screen_html.screen_name, tree=tree)
        )
    return state


def build_design_graph(max_retries: int = DEFAULT_MAX_RETRIES) -> StateGraph:
    """Construct the LangGraph StateGraph for the design pipeline (v2).

    Pipeline: START → plan → generate_html → convert_to_figma → END
    """
    graph = StateGraph(PipelineState)

    graph.add_node("plan", _wrap_with_retry("plan", plan, max_retries))
    graph.add_node(
        "generate_html", _wrap_with_retry("generate_html", generate_html, max_retries)
    )
    graph.add_node(
        "convert_to_figma",
        _wrap_with_retry("convert_to_figma", _convert_html_to_figma, max_retries),
    )

    graph.add_edge(START, "plan")
    graph.add_conditional_edges(
        "plan", _should_continue, {"continue": "generate_html", "stop": END}
    )
    graph.add_conditional_edges(
        "generate_html", _should_continue, {"continue": "convert_to_figma", "stop": END}
    )
    graph.add_edge("convert_to_figma", END)

    return graph


design_pipeline = build_design_graph().compile()


async def run_design_pipeline(raw_input: str) -> PipelineState:
    """Execute the design pipeline (v2) from raw user input to Figma trees.

    Args:
        raw_input: The user's product description / prompt.

    Returns:
        PipelineState with figma_trees populated.
    """
    logger.info("Design pipeline started: %.80s...", raw_input)
    initial_state = PipelineState(raw_input=raw_input)
    result = await design_pipeline.ainvoke(initial_state)
    state = PipelineState.model_validate(result)
    logger.info(
        "Design pipeline finished: %d screens, %d errors",
        len(state.figma_trees),
        len(state.errors),
    )
    return state
