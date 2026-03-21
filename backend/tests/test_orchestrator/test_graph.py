"""Tests for the LangGraph orchestration — graph structure, retry, and pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.mapper import MapperOutput
from backend.agents.planner import PlannerOutput
from backend.agents.ui_generator import UIGeneratorOutput
from backend.orchestrator.graph import (
    _should_continue,
    _wrap_with_retry,
    build_graph,
    run_pipeline,
)
from backend.orchestrator.state import PipelineState, ScreenPlan, UIComponent

# --- Fixtures ---


def _planner_output() -> PlannerOutput:
    return PlannerOutput(
        product_type="SaaS",
        user_goals=["View data"],
        screens=[
            ScreenPlan(name="Home", purpose="Main view", priority=1),
            ScreenPlan(name="Settings", purpose="User settings", priority=2),
        ],
        navigation_flow=["Home", "Settings"],
    )


def _ui_gen_output() -> UIGeneratorOutput:
    return UIGeneratorOutput(
        screen_name="Home",
        layout=[
            UIComponent(
                id="Home_section_1",
                type="section",
                children=[
                    UIComponent(
                        id="Home_text_1", type="text", props={"content": "Hello"}
                    ),
                ],
            ),
        ],
    )


def _mapper_output() -> MapperOutput:
    return MapperOutput(
        screen_name="Home",
        components=[
            UIComponent(
                id="Home_section_1",
                type="section",
                children=[
                    UIComponent(
                        id="Home_text_1",
                        type="text",
                        props={"content": "Hello", "variant": "heading-1"},
                        tokens={"color": "text-primary"},
                    ),
                ],
            ),
        ],
        tokens={"background": "background"},
    )


# --- Graph Structure ---


class TestGraphStructure:
    def test_graph_has_all_nodes(self) -> None:
        graph = build_graph()
        node_names = set(graph.nodes)
        assert "plan" in node_names
        assert "generate_ui" in node_names
        assert "map_to_design_system" in node_names
        assert "validate" in node_names

    def test_graph_compiles(self) -> None:
        compiled = build_graph().compile()
        assert hasattr(compiled, "ainvoke")

    def test_module_level_pipeline_exists(self) -> None:
        from backend.orchestrator.graph import pipeline

        assert hasattr(pipeline, "ainvoke")


# --- Conditional Edges ---


class TestShouldContinue:
    def test_returns_stop_with_errors(self) -> None:
        state = PipelineState(errors=["something broke"])
        assert _should_continue(state) == "stop"

    def test_returns_continue_without_errors(self) -> None:
        state = PipelineState()
        assert _should_continue(state) == "continue"


# --- Retry Wrapper ---


class TestRetryWrapper:
    async def test_succeeds_first_attempt(self) -> None:
        mock_agent = AsyncMock(return_value=PipelineState(raw_input="ok"))
        wrapped = _wrap_with_retry("test", mock_agent, max_retries=2)
        state = PipelineState(raw_input="test")
        result = await wrapped(state)
        assert mock_agent.call_count == 1
        assert result.errors == []

    async def test_retries_then_succeeds(self) -> None:
        mock_agent = AsyncMock(
            side_effect=[ValueError("fail"), PipelineState(raw_input="ok")]
        )
        wrapped = _wrap_with_retry("test", mock_agent, max_retries=2)
        state = PipelineState(raw_input="test")
        result = await wrapped(state)
        assert mock_agent.call_count == 2
        assert result.errors == []

    async def test_captures_error_after_max_retries(self) -> None:
        mock_agent = AsyncMock(side_effect=ValueError("persistent"))
        wrapped = _wrap_with_retry("test", mock_agent, max_retries=2)
        state = PipelineState(raw_input="test")
        result = await wrapped(state)
        assert mock_agent.call_count == 2
        assert len(result.errors) == 1
        assert "persistent" in result.errors[0]

    async def test_does_not_raise_after_exhaustion(self) -> None:
        mock_agent = AsyncMock(side_effect=RuntimeError("boom"))
        wrapped = _wrap_with_retry("test", mock_agent, max_retries=2)
        state = PipelineState(raw_input="test")
        result = await wrapped(state)
        assert isinstance(result, PipelineState)
        assert len(result.errors) == 1


# --- Full Pipeline via run_pipeline ---


class TestRunPipeline:
    async def test_happy_path(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            side_effect=[
                _planner_output(),
                _ui_gen_output(),
                _ui_gen_output(),
                _mapper_output(),
                _mapper_output(),
            ]
        )
        mock_ds = MagicMock()
        mock_ds.to_prompt_context.return_value = "DS"

        with (
            patch("backend.agents.planner.get_llm", return_value=mock_llm),
            patch("backend.agents.ui_generator.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.load_design_system", return_value=mock_ds),
        ):
            result = await run_pipeline("Build a SaaS dashboard")

        assert isinstance(result, PipelineState)
        assert result.errors == []
        assert result.interpreted is not None
        assert result.plan is not None
        assert len(result.raw_trees) == 2
        assert len(result.mapped_uis) == 2
        assert len(result.validated_uis) == 2

    async def test_planner_failure_halts_pipeline(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(side_effect=RuntimeError("LLM down"))

        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            result = await run_pipeline("Build something")

        assert len(result.errors) >= 1
        assert "plan" in result.errors[0]
        assert result.interpreted is None
        assert result.raw_trees == []
        assert result.mapped_uis == []
        assert result.validated_uis == []

    async def test_returns_pydantic_model(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            side_effect=[
                _planner_output(),
                _ui_gen_output(),
                _ui_gen_output(),
                _mapper_output(),
                _mapper_output(),
            ]
        )
        mock_ds = MagicMock()
        mock_ds.to_prompt_context.return_value = "DS"

        with (
            patch("backend.agents.planner.get_llm", return_value=mock_llm),
            patch("backend.agents.ui_generator.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.load_design_system", return_value=mock_ds),
        ):
            result = await run_pipeline("test")

        assert isinstance(result, PipelineState)
