"""Tests for the Design System Mapper agent — uses mocked LLM, no real API calls."""

from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.mapper import MapperOutput, map_to_design_system
from backend.orchestrator.state import PipelineState, RawUITree, UIComponent


class TestMapperAgent:
    def _state_with_raw_trees(self) -> PipelineState:
        return PipelineState(
            raw_input="test",
            raw_trees=[
                RawUITree(
                    screen_name="Dashboard",
                    layout=[
                        UIComponent(
                            id="Dashboard_section_1",
                            type="section",
                            children=[
                                UIComponent(
                                    id="Dashboard_text_1",
                                    type="text",
                                    props={"content": "Hello"},
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def _mock_mapper_output(self) -> MapperOutput:
        return MapperOutput(
            screen_name="Dashboard",
            components=[
                UIComponent(
                    id="Dashboard_section_1",
                    type="section",
                    children=[
                        UIComponent(
                            id="Dashboard_text_1",
                            type="text",
                            props={"content": "Hello", "variant": "heading-1"},
                            tokens={"color": "text-primary"},
                        ),
                    ],
                ),
            ],
            tokens={"background": "background"},
        )

    async def test_maps_raw_trees_to_design_system(self) -> None:
        state = self._state_with_raw_trees()
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=self._mock_mapper_output())
        mock_ds = MagicMock()
        mock_ds.to_prompt_context.return_value = "DS_CONTEXT"

        with (
            patch("backend.agents.mapper.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.load_design_system", return_value=mock_ds),
        ):
            result = await map_to_design_system(state)

        assert len(result.mapped_uis) == 1
        assert result.mapped_uis[0].screen_name == "Dashboard"
        assert result.mapped_uis[0].tokens == {"background": "background"}

    async def test_injects_design_system_in_prompt(self) -> None:
        state = self._state_with_raw_trees()
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=self._mock_mapper_output())
        mock_ds = MagicMock()
        mock_ds.to_prompt_context.return_value = "=== DESIGN SYSTEM ==="

        with (
            patch("backend.agents.mapper.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.load_design_system", return_value=mock_ds),
        ):
            await map_to_design_system(state)

        call_args = mock_llm.generate.call_args
        prompt = call_args.kwargs.get("prompt") or call_args.args[0]
        assert "DESIGN SYSTEM" in prompt

    async def test_errors_on_missing_raw_trees(self) -> None:
        state = PipelineState(raw_input="test")

        with patch("backend.agents.mapper.get_llm"):
            result = await map_to_design_system(state)

        assert len(result.errors) > 0
        assert "no raw UI trees" in result.errors[0]
