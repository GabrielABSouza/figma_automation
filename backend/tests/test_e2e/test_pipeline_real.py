"""E2E test — full pipeline with REAL Gemini API calls.

Requires a valid GEMINI_API_KEY in .env. Run with:
    pytest backend/tests/test_e2e/test_pipeline_real.py -v -m real_api

These tests are SLOW and cost real API credits. They are skipped by default.
"""

import os

import pytest

from backend.agents.mapper import map_to_design_system
from backend.agents.planner import plan
from backend.agents.ui_generator import generate_ui
from backend.agents.validator import validate
from backend.llm.factory import reset_llm
from backend.orchestrator.state import PipelineState

# Skip all tests in this module unless GEMINI_API_KEY is set and marker is used
pytestmark = pytest.mark.real_api

_has_api_key = bool(os.environ.get("GEMINI_API_KEY"))


@pytest.fixture(autouse=True)
def _reset_llm_singleton() -> None:
    """Reset the LLM singleton before each test so it picks up fresh config."""
    reset_llm()


@pytest.mark.skipif(not _has_api_key, reason="GEMINI_API_KEY not set")
class TestRealPipeline:
    """Full pipeline tests using the real Gemini API."""

    async def test_planner_with_real_api(self) -> None:
        """Planner produces a valid design plan from a real prompt."""
        state = PipelineState(
            raw_input="Build a simple task management app with a dashboard and settings page"
        )

        state = await plan(state)

        assert state.interpreted is not None
        assert state.interpreted.product_type != ""
        assert len(state.interpreted.user_goals) >= 1
        assert state.plan is not None
        assert 2 <= len(state.plan.screens) <= 6
        assert len(state.plan.navigation_flow) >= 2

        # All screen names should be unique
        screen_names = [s.name for s in state.plan.screens]
        assert len(screen_names) == len(set(screen_names))

    async def test_planner_then_ui_generator(self) -> None:
        """Planner → UI Generator produces valid raw trees."""
        state = PipelineState(raw_input="Build a blog with a home page and post editor")

        state = await plan(state)
        assert state.plan is not None

        state = await generate_ui(state)

        assert len(state.raw_trees) == len(state.plan.screens)
        for tree in state.raw_trees:
            assert tree.screen_name != ""
            assert len(tree.layout) >= 1

    async def test_full_pipeline_real(self) -> None:
        """Complete pipeline: Planner → UI Gen → Mapper → Validator.

        This is the ultimate integration test. The output may not always pass
        validation (LLM outputs vary), but the pipeline should not crash.
        """
        state = PipelineState(
            raw_input=(
                "Build a simple landing page for a SaaS product. "
                "It should have a hero section, features section, and a pricing section."
            )
        )

        # Step 1: Plan
        state = await plan(state)
        assert state.plan is not None
        assert len(state.errors) == 0

        # Step 2: Generate UI
        state = await generate_ui(state)
        assert len(state.raw_trees) > 0
        assert len(state.errors) == 0

        # Step 3: Map to DS
        state = await map_to_design_system(state)
        assert len(state.mapped_uis) > 0
        assert len(state.errors) == 0

        # Step 4: Validate
        state = await validate(state)
        assert len(state.validated_uis) > 0

        # Log results for debugging (visible with -v flag)
        for v_ui in state.validated_uis:
            print(f"\n--- {v_ui.screen_name} ---")
            print(f"  Valid: {v_ui.validation.is_valid}")
            print(f"  Errors: {v_ui.validation.errors}")
            print(f"  Warnings: {v_ui.validation.warnings}")
            print(f"  Components: {v_ui.metadata.get('component_count', '?')}")

        # The pipeline completed without crashing — that's the key assertion.
        # Validation may or may not pass depending on LLM output quality.
        assert len(state.validated_uis) == len(state.mapped_uis)
