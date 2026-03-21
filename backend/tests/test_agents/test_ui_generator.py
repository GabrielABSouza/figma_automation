"""Tests for the UI Generator agent — uses mocked LLM, no real API calls."""

from unittest.mock import AsyncMock, patch

from backend.agents.ui_generator import UIGeneratorOutput, generate_ui
from backend.orchestrator.state import (
    DesignPlan,
    InterpretedInput,
    PipelineState,
    ScreenPlan,
    UIComponent,
)


class TestGenerateUIAgent:
    def _state_with_plan(self) -> PipelineState:
        return PipelineState(
            raw_input="Build a dashboard",
            interpreted=InterpretedInput(product_type="dashboard"),
            plan=DesignPlan(
                screens=[
                    ScreenPlan(name="Dashboard", purpose="Main view", priority=1),
                    ScreenPlan(name="Settings", purpose="App settings", priority=2),
                ],
                navigation_flow=["Dashboard", "Settings"],
            ),
        )

    def _mock_output(self, screen_name: str) -> UIGeneratorOutput:
        return UIGeneratorOutput(
            screen_name=screen_name,
            layout=[
                UIComponent(
                    id=f"{screen_name}_section_1",
                    type="section",
                    children=[
                        UIComponent(
                            id=f"{screen_name}_text_1",
                            type="text",
                            props={"content": f"{screen_name} Title"},
                        ),
                    ],
                ),
            ],
        )

    async def test_generates_one_tree_per_screen(self) -> None:
        state = self._state_with_plan()
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            side_effect=[
                self._mock_output("Dashboard"),
                self._mock_output("Settings"),
            ]
        )

        with patch("backend.agents.ui_generator.get_llm", return_value=mock_llm):
            result = await generate_ui(state)

        assert len(result.raw_trees) == 2
        assert result.raw_trees[0].screen_name == "Dashboard"
        assert result.raw_trees[1].screen_name == "Settings"

    async def test_tree_contains_layout_components(self) -> None:
        state = self._state_with_plan()
        state.plan.screens = [state.plan.screens[0]]  # just Dashboard
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=self._mock_output("Dashboard"))

        with patch("backend.agents.ui_generator.get_llm", return_value=mock_llm):
            result = await generate_ui(state)

        tree = result.raw_trees[0]
        assert len(tree.layout) >= 1
        assert tree.layout[0].type == "section"
        assert len(tree.layout[0].children) >= 1

    async def test_errors_on_missing_plan(self) -> None:
        state = PipelineState(raw_input="test")

        with patch("backend.agents.ui_generator.get_llm"):
            result = await generate_ui(state)

        assert len(result.errors) > 0
        assert "no design plan" in result.errors[0]

    async def test_errors_on_empty_screens(self) -> None:
        state = PipelineState(
            raw_input="test",
            plan=DesignPlan(screens=[], navigation_flow=[]),
        )

        with patch("backend.agents.ui_generator.get_llm"):
            result = await generate_ui(state)

        assert len(result.errors) > 0
