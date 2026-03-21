"""E2E test — full pipeline with mocked LLM (Planner → UI Gen → Mapper → Validator).

Verifies the complete data flow through all 4 agents without real API calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.mapper import MapperOutput, map_to_design_system
from backend.agents.planner import PlannerOutput, plan
from backend.agents.ui_generator import UIGeneratorOutput, generate_ui
from backend.agents.validator import validate
from backend.orchestrator.state import PipelineState, ScreenPlan, UIComponent


def _planner_output() -> PlannerOutput:
    return PlannerOutput(
        product_type="SaaS Dashboard",
        user_goals=["View metrics", "Manage users"],
        screens=[
            ScreenPlan(name="Dashboard", purpose="Main metrics overview", priority=1),
            ScreenPlan(name="Users", purpose="User management table", priority=2),
        ],
        navigation_flow=["Dashboard", "Users"],
    )


def _ui_generator_output_dashboard() -> UIGeneratorOutput:
    return UIGeneratorOutput(
        screen_name="Dashboard",
        layout=[
            UIComponent(
                id="Dashboard_section_1",
                type="section",
                children=[
                    UIComponent(
                        id="Dashboard_text_1",
                        type="text",
                        props={"content": "Dashboard Overview"},
                    ),
                    UIComponent(
                        id="Dashboard_row_1",
                        type="row",
                        children=[
                            UIComponent(
                                id="Dashboard_card_1",
                                type="card",
                                props={"title": "Revenue"},
                                children=[
                                    UIComponent(
                                        id="Dashboard_text_2",
                                        type="text",
                                        props={"content": "$12,345"},
                                    ),
                                ],
                            ),
                            UIComponent(
                                id="Dashboard_card_2",
                                type="card",
                                props={"title": "Active Users"},
                                children=[
                                    UIComponent(
                                        id="Dashboard_text_3",
                                        type="text",
                                        props={"content": "1,234"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _ui_generator_output_users() -> UIGeneratorOutput:
    return UIGeneratorOutput(
        screen_name="Users",
        layout=[
            UIComponent(
                id="Users_section_1",
                type="section",
                children=[
                    UIComponent(
                        id="Users_text_1",
                        type="text",
                        props={"content": "User Management"},
                    ),
                    UIComponent(
                        id="Users_input_1",
                        type="input",
                        props={"label": "Search users", "placeholder": "Search..."},
                    ),
                    UIComponent(
                        id="Users_table_1",
                        type="table",
                        props={"columns": [], "rows": 10},
                    ),
                ],
            ),
        ],
    )


def _mapper_output_dashboard() -> MapperOutput:
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
                        props={"content": "Dashboard Overview", "variant": "heading-1"},
                        tokens={"color": "text-primary"},
                    ),
                    UIComponent(
                        id="Dashboard_row_1",
                        type="row",
                        children=[
                            UIComponent(
                                id="Dashboard_card_1",
                                type="card",
                                props={"title": "Revenue", "variant": "elevated"},
                                tokens={"background": "surface"},
                                children=[
                                    UIComponent(
                                        id="Dashboard_text_2",
                                        type="text",
                                        props={"content": "$12,345", "variant": "heading-2"},
                                        tokens={"color": "text-primary"},
                                    ),
                                ],
                            ),
                            UIComponent(
                                id="Dashboard_card_2",
                                type="card",
                                props={"title": "Active Users", "variant": "elevated"},
                                tokens={"background": "surface"},
                                children=[
                                    UIComponent(
                                        id="Dashboard_text_3",
                                        type="text",
                                        props={"content": "1,234", "variant": "heading-2"},
                                        tokens={"color": "text-primary"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
        tokens={"background": "background"},
    )


def _mapper_output_users() -> MapperOutput:
    return MapperOutput(
        screen_name="Users",
        components=[
            UIComponent(
                id="Users_section_1",
                type="section",
                children=[
                    UIComponent(
                        id="Users_text_1",
                        type="text",
                        props={"content": "User Management", "variant": "heading-1"},
                        tokens={"color": "text-primary"},
                    ),
                    UIComponent(
                        id="Users_input_1",
                        type="input",
                        props={
                            "label": "Search users",
                            "placeholder": "Search...",
                            "variant": "search",
                        },
                        tokens={"border": "border"},
                    ),
                    UIComponent(
                        id="Users_table_1",
                        type="table",
                        props={"columns": [], "rows": 10, "variant": "striped"},
                        tokens={"background": "surface"},
                    ),
                ],
            ),
        ],
        tokens={"background": "background"},
    )


class TestFullPipelineMock:
    """Run the complete MVP pipeline: Planner → UI Gen → Mapper → Validator."""

    async def test_full_pipeline_produces_valid_output(self) -> None:
        # --- Setup mock LLM ---
        mock_llm = AsyncMock()

        # Planner call returns PlannerOutput
        # UI Generator calls return per-screen outputs
        # Mapper calls return per-screen mapped outputs
        mock_llm.generate = AsyncMock(
            side_effect=[
                _planner_output(),
                _ui_generator_output_dashboard(),
                _ui_generator_output_users(),
                _mapper_output_dashboard(),
                _mapper_output_users(),
            ]
        )

        mock_ds = MagicMock()
        mock_ds.to_prompt_context.return_value = "=== DESIGN SYSTEM ==="

        state = PipelineState(raw_input="Build a SaaS dashboard with user management")

        # --- Step 1: Planner ---
        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = await plan(state)

        assert state.interpreted is not None
        assert state.interpreted.product_type == "SaaS Dashboard"
        assert state.plan is not None
        assert len(state.plan.screens) == 2
        assert state.plan.screens[0].name == "Dashboard"
        assert state.plan.screens[1].name == "Users"

        # --- Step 2: UI Generator ---
        with patch("backend.agents.ui_generator.get_llm", return_value=mock_llm):
            state = await generate_ui(state)

        assert len(state.raw_trees) == 2
        assert state.raw_trees[0].screen_name == "Dashboard"
        assert state.raw_trees[1].screen_name == "Users"

        # --- Step 3: Mapper ---
        with (
            patch("backend.agents.mapper.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.load_design_system", return_value=mock_ds),
        ):
            state = await map_to_design_system(state)

        assert len(state.mapped_uis) == 2
        assert state.mapped_uis[0].screen_name == "Dashboard"
        assert state.mapped_uis[1].screen_name == "Users"
        assert state.mapped_uis[0].tokens.get("background") == "background"

        # --- Step 4: Validator (real — no LLM, uses actual DS files) ---
        state = await validate(state)

        assert len(state.validated_uis) == 2
        assert len(state.errors) == 0

        # Dashboard should be valid
        dashboard_v = state.validated_uis[0]
        assert dashboard_v.screen_name == "Dashboard"
        assert dashboard_v.validation.is_valid is True
        assert len(dashboard_v.validation.errors) == 0

        # Users should be valid
        users_v = state.validated_uis[1]
        assert users_v.screen_name == "Users"
        assert users_v.validation.is_valid is True
        assert len(users_v.validation.errors) == 0

        # Metadata populated
        assert dashboard_v.metadata.get("component_count") is not None

    async def test_full_pipeline_llm_call_count(self) -> None:
        """Verify the pipeline makes exactly 5 LLM calls for 2 screens."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            side_effect=[
                _planner_output(),
                _ui_generator_output_dashboard(),
                _ui_generator_output_users(),
                _mapper_output_dashboard(),
                _mapper_output_users(),
            ]
        )

        mock_ds = MagicMock()
        mock_ds.to_prompt_context.return_value = "DS"

        state = PipelineState(raw_input="Build a SaaS dashboard")

        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = await plan(state)

        with patch("backend.agents.ui_generator.get_llm", return_value=mock_llm):
            state = await generate_ui(state)

        with (
            patch("backend.agents.mapper.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.load_design_system", return_value=mock_ds),
        ):
            state = await map_to_design_system(state)

        state = await validate(state)

        # 1 planner + 2 ui_gen + 2 mapper = 5 LLM calls
        assert mock_llm.generate.call_count == 5

    async def test_pipeline_state_serialization_roundtrip(self) -> None:
        """After full pipeline, state should serialize/deserialize correctly."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            side_effect=[
                _planner_output(),
                _ui_generator_output_dashboard(),
                _ui_generator_output_users(),
                _mapper_output_dashboard(),
                _mapper_output_users(),
            ]
        )

        mock_ds = MagicMock()
        mock_ds.to_prompt_context.return_value = "DS"

        state = PipelineState(raw_input="Build a SaaS dashboard")

        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = await plan(state)
        with patch("backend.agents.ui_generator.get_llm", return_value=mock_llm):
            state = await generate_ui(state)
        with (
            patch("backend.agents.mapper.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.load_design_system", return_value=mock_ds),
        ):
            state = await map_to_design_system(state)
        state = await validate(state)

        # Roundtrip
        json_str = state.model_dump_json()
        restored = PipelineState.model_validate_json(json_str)

        assert restored.raw_input == state.raw_input
        assert restored.interpreted is not None
        assert restored.interpreted.product_type == "SaaS Dashboard"
        assert len(restored.plan.screens) == 2
        assert len(restored.raw_trees) == 2
        assert len(restored.mapped_uis) == 2
        assert len(restored.validated_uis) == 2
        assert restored.validated_uis[0].validation.is_valid is True

    async def test_pipeline_handles_validation_failures_gracefully(self) -> None:
        """If mapper produces invalid components, validator catches them."""
        mock_llm = AsyncMock()

        # Mapper returns an invalid component type
        bad_mapper_output = MapperOutput(
            screen_name="Dashboard",
            components=[
                UIComponent(
                    id="bad_1",
                    type="widget",  # not in design system
                    props={"label": "broken"},
                ),
            ],
            tokens={},
        )

        mock_llm.generate = AsyncMock(
            side_effect=[
                _planner_output(),
                _ui_generator_output_dashboard(),
                _ui_generator_output_users(),
                bad_mapper_output,
                _mapper_output_users(),
            ]
        )

        mock_ds = MagicMock()
        mock_ds.to_prompt_context.return_value = "DS"

        state = PipelineState(raw_input="Build a SaaS dashboard")

        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = await plan(state)
        with patch("backend.agents.ui_generator.get_llm", return_value=mock_llm):
            state = await generate_ui(state)
        with (
            patch("backend.agents.mapper.get_llm", return_value=mock_llm),
            patch("backend.agents.mapper.load_design_system", return_value=mock_ds),
        ):
            state = await map_to_design_system(state)
        state = await validate(state)

        # Dashboard validation should fail (invalid "widget" type)
        assert state.validated_uis[0].validation.is_valid is False
        assert any("widget" in e for e in state.validated_uis[0].validation.errors)

        # Users should still be valid
        assert state.validated_uis[1].validation.is_valid is True
