"""Tests for the Design Planner agent — uses mocked LLM, no real API calls."""

from unittest.mock import AsyncMock, patch

from backend.agents.planner import PlannerOutput, plan
from backend.orchestrator.state import PipelineState, ScreenPlan


class TestPlanAgent:
    def _mock_output(self) -> PlannerOutput:
        return PlannerOutput(
            product_type="SaaS dashboard",
            user_goals=["View metrics", "Manage users"],
            screens=[
                ScreenPlan(name="Dashboard", purpose="Main overview", priority=1),
                ScreenPlan(name="Users", purpose="User management", priority=2),
            ],
            navigation_flow=["Dashboard", "Users"],
        )

    async def test_populates_interpreted_input(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=self._mock_output())

        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = PipelineState(raw_input="Build a SaaS dashboard")
            result = await plan(state)

        assert result.interpreted is not None
        assert result.interpreted.product_type == "SaaS dashboard"
        assert len(result.interpreted.user_goals) == 2
        assert result.interpreted.raw_input == "Build a SaaS dashboard"
        assert result.interpreted.required_screens == ["Dashboard", "Users"]

    async def test_populates_design_plan(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=self._mock_output())

        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = PipelineState(raw_input="Build a SaaS dashboard")
            result = await plan(state)

        assert result.plan is not None
        assert len(result.plan.screens) == 2
        assert result.plan.screens[0].name == "Dashboard"
        assert result.plan.screens[0].priority == 1
        assert result.plan.navigation_flow == ["Dashboard", "Users"]

    async def test_calls_llm_with_system_prompt(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=self._mock_output())

        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = PipelineState(raw_input="Build a SaaS dashboard")
            await plan(state)

        mock_llm.generate.assert_called_once()
        call_kwargs = mock_llm.generate.call_args
        assert call_kwargs.kwargs["system_prompt"] is not None
        assert "product designer" in call_kwargs.kwargs["system_prompt"].lower()
        assert call_kwargs.kwargs["output_schema"] is PlannerOutput
