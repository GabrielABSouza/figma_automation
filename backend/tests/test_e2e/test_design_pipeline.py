"""E2E tests for the design pipeline (v2): Planner → HTML Generator → Converter.

- Mock tests: full pipeline with mocked LLM, verifying data flow.
- Real API tests: full pipeline with real Gemini API, verifying end-to-end quality.
  Run with: pytest -m real_api
"""

import os
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.agents.html_generator import HTMLGeneratorOutput, ScreenHTMLItem, generate_html
from backend.agents.planner import PlannerOutput, plan
from backend.converters.html_to_figma import convert_html_to_figma_tree
from backend.llm.factory import reset_llm
from backend.main import app
from backend.orchestrator.graph import _convert_html_to_figma
from backend.orchestrator.state import PipelineState, ScreenHTML, ScreenPlan

# ─── Fixtures ───

DASHBOARD_HTML = """\
<div style='display: flex; flex-direction: column; width: 1440px; \
background-color: #F8FAFC; padding: 48px; gap: 32px'>
    <div style='display: flex; flex-direction: row; align-items: center; \
justify-content: space-between; padding: 16px 32px; \
background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; border-radius: 12px'>
        <span style='font-size: 20px; font-weight: 700; color: #0F172A'>FinTrack</span>
        <div style='display: flex; flex-direction: row; gap: 24px'>
            <span style='font-size: 16px; color: #2563EB; font-weight: 500'>Dashboard</span>
            <span style='font-size: 16px; color: #475569'>Settings</span>
        </div>
    </div>
    <h1 style='font-size: 32px; font-weight: 700; color: #0F172A'>Dashboard</h1>
    <div style='display: flex; flex-direction: row; gap: 24px'>
        <div style='flex: 1; background-color: #FFFFFF; border-radius: 12px; \
padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); \
display: flex; flex-direction: column; gap: 8px'>
            <p style='font-size: 14px; color: #64748B'>Total Revenue</p>
            <p style='font-size: 32px; font-weight: 700; color: #0F172A'>$45,231</p>
            <p style='font-size: 12px; color: #16A34A'>+12.5% from last month</p>
        </div>
        <div style='flex: 1; background-color: #FFFFFF; border-radius: 12px; \
padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); \
display: flex; flex-direction: column; gap: 8px'>
            <p style='font-size: 14px; color: #64748B'>Active Users</p>
            <p style='font-size: 32px; font-weight: 700; color: #0F172A'>2,345</p>
            <p style='font-size: 12px; color: #16A34A'>+8.2% from last month</p>
        </div>
    </div>
</div>"""

SETTINGS_HTML = """\
<div style='display: flex; flex-direction: column; width: 1440px; \
background-color: #F8FAFC; padding: 48px; gap: 32px'>
    <h1 style='font-size: 32px; font-weight: 700; color: #0F172A'>Settings</h1>
    <div style='background-color: #FFFFFF; border-radius: 12px; padding: 24px; \
box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; flex-direction: column; gap: 16px'>
        <h2 style='font-size: 20px; font-weight: 600; color: #0F172A'>Profile</h2>
        <div style='display: flex; flex-direction: column; gap: 4px'>
            <span style='font-size: 14px; font-weight: 500; color: #475569'>Name</span>
            <input style='padding: 12px; border: 1px solid #E2E8F0; border-radius: 8px' \
placeholder='John Doe' />
        </div>
        <button style='background-color: #2563EB; color: #FFFFFF; padding: 10px 20px; \
border-radius: 8px; font-weight: 600; font-size: 14px; border: none'>Save Changes</button>
    </div>
</div>"""


def _planner_output() -> PlannerOutput:
    return PlannerOutput(
        product_type="SaaS Dashboard",
        user_goals=["View financial metrics", "Manage settings"],
        screens=[
            ScreenPlan(name="Dashboard", purpose="Financial metrics overview", priority=1),
            ScreenPlan(name="Settings", purpose="App configuration", priority=2),
        ],
        navigation_flow=["Dashboard", "Settings"],
    )


def _html_generator_output() -> HTMLGeneratorOutput:
    return HTMLGeneratorOutput(
        screens=[
            ScreenHTMLItem(screen_name="Dashboard", html=DASHBOARD_HTML),
            ScreenHTMLItem(screen_name="Settings", html=SETTINGS_HTML),
        ]
    )


def _validate_figma_tree(tree: dict[str, Any], screen_name: str) -> list[str]:
    """Validate a Figma tree has essential properties. Returns list of issues."""
    issues: list[str] = []

    if tree.get("type") != "FRAME":
        issues.append(f"{screen_name}: root is not FRAME")
    if tree.get("name") != screen_name:
        issues.append(f"{screen_name}: root name mismatch ({tree.get('name')})")
    if "layoutMode" not in tree:
        issues.append(f"{screen_name}: missing layoutMode")
    if tree.get("width", 0) < 1000:
        issues.append(f"{screen_name}: width too small ({tree.get('width')})")

    children = tree.get("children", [])
    if len(children) == 0:
        issues.append(f"{screen_name}: no children")

    # Count node types
    text_count = 0
    frame_count = 0

    def _count_nodes(node: dict[str, Any]) -> None:
        nonlocal text_count, frame_count
        if node.get("type") == "TEXT":
            text_count += 1
        elif node.get("type") == "FRAME":
            frame_count += 1
        for child in node.get("children", []):
            _count_nodes(child)

    _count_nodes(tree)

    if text_count < 2:
        issues.append(f"{screen_name}: too few TEXT nodes ({text_count})")
    if frame_count < 2:
        issues.append(f"{screen_name}: too few FRAME nodes ({frame_count})")

    return issues


# ─── Mock E2E Tests ───


class TestDesignPipelineMock:
    """Full design pipeline with mocked LLM: Planner → HTML Gen → Converter."""

    async def test_full_pipeline_produces_figma_trees(self):
        """Pipeline should produce valid Figma trees for all screens."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            side_effect=[_planner_output(), _html_generator_output()]
        )

        state = PipelineState(raw_input="Build a SaaS dashboard for financial tracking")

        # Step 1: Plan
        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = await plan(state)

        assert state.plan is not None
        assert len(state.plan.screens) == 2

        # Step 2: Generate HTML
        with patch("backend.agents.html_generator.get_llm", return_value=mock_llm):
            state = await generate_html(state)

        assert len(state.screen_htmls) == 2

        # Step 3: Convert to Figma (no LLM needed)
        state = await _convert_html_to_figma(state)

        assert len(state.figma_trees) == 2
        assert state.figma_trees[0].screen_name == "Dashboard"
        assert state.figma_trees[1].screen_name == "Settings"

        # Validate tree quality
        for ft in state.figma_trees:
            issues = _validate_figma_tree(ft.tree, ft.screen_name)
            assert issues == [], f"Tree issues: {issues}"

    async def test_pipeline_llm_call_count(self):
        """Design pipeline should make exactly 2 LLM calls (planner + HTML gen)."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            side_effect=[_planner_output(), _html_generator_output()]
        )

        state = PipelineState(raw_input="Build a dashboard")

        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = await plan(state)
        with patch("backend.agents.html_generator.get_llm", return_value=mock_llm):
            state = await generate_html(state)
        state = await _convert_html_to_figma(state)

        # 1 planner + 1 html_gen = 2 LLM calls (vs 5 in v1 pipeline)
        assert mock_llm.generate.call_count == 2

    async def test_dashboard_tree_has_cards_and_text(self):
        """Dashboard tree should contain metric cards with text content."""
        tree = convert_html_to_figma_tree(DASHBOARD_HTML, "Dashboard")

        issues = _validate_figma_tree(tree, "Dashboard")
        assert issues == [], f"Tree issues: {issues}"

        # Collect all text content
        texts: list[str] = []

        def _collect_text(node: dict[str, Any]) -> None:
            if node.get("type") == "TEXT":
                texts.append(node.get("characters", ""))
            for child in node.get("children", []):
                _collect_text(child)

        _collect_text(tree)

        # Should contain dashboard content
        all_text = " ".join(texts).lower()
        assert "dashboard" in all_text
        assert "$45,231" in " ".join(texts)  # exact dollar amount
        assert "2,345" in " ".join(texts)  # user count

    async def test_settings_tree_has_form_elements(self):
        """Settings tree should contain form elements (input, button)."""
        tree = convert_html_to_figma_tree(SETTINGS_HTML, "Settings")

        issues = _validate_figma_tree(tree, "Settings")
        assert issues == [], f"Tree issues: {issues}"

        # Collect all node types and text
        node_types: list[str] = []
        texts: list[str] = []

        def _collect(node: dict[str, Any]) -> None:
            node_types.append(node.get("type", ""))
            if node.get("type") == "TEXT":
                texts.append(node.get("characters", ""))
            for child in node.get("children", []):
                _collect(child)

        _collect(tree)

        all_text = " ".join(texts).lower()
        assert "settings" in all_text
        assert "save changes" in all_text or "save" in all_text

    async def test_tree_has_proper_layout(self):
        """Trees should use proper auto-layout (VERTICAL/HORIZONTAL)."""
        tree = convert_html_to_figma_tree(DASHBOARD_HTML, "Dashboard")

        # Root is vertical
        assert tree["layoutMode"] == "VERTICAL"
        assert tree["width"] == 1440

        # Find a horizontal row (card row)
        def _find_horizontal(node: dict[str, Any]) -> bool:
            if node.get("layoutMode") == "HORIZONTAL":
                return True
            return any(_find_horizontal(child) for child in node.get("children", []))

        assert _find_horizontal(tree), "Should have at least one HORIZONTAL layout"

    async def test_tree_has_visual_styling(self):
        """Trees should have fills, shadows, borders — not plain wireframes."""
        tree = convert_html_to_figma_tree(DASHBOARD_HTML, "Dashboard")

        has_fills = False
        has_effects = False
        has_corner_radius = False

        def _check_styling(node: dict[str, Any]) -> None:
            nonlocal has_fills, has_effects, has_corner_radius
            if node.get("fills"):
                has_fills = True
            if node.get("effects"):
                has_effects = True
            if node.get("cornerRadius"):
                has_corner_radius = True
            for child in node.get("children", []):
                _check_styling(child)

        _check_styling(tree)

        assert has_fills, "Should have background fills"
        assert has_effects, "Should have shadow effects"
        assert has_corner_radius, "Should have corner radius"

    async def test_state_serialization_roundtrip(self):
        """State with figma_trees should serialize/deserialize correctly."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            side_effect=[_planner_output(), _html_generator_output()]
        )

        state = PipelineState(raw_input="Build a dashboard")

        with patch("backend.agents.planner.get_llm", return_value=mock_llm):
            state = await plan(state)
        with patch("backend.agents.html_generator.get_llm", return_value=mock_llm):
            state = await generate_html(state)
        state = await _convert_html_to_figma(state)

        # Roundtrip
        json_str = state.model_dump_json()
        restored = PipelineState.model_validate_json(json_str)

        assert restored.raw_input == state.raw_input
        assert len(restored.figma_trees) == 2
        assert restored.figma_trees[0].screen_name == "Dashboard"
        assert restored.figma_trees[0].tree["type"] == "FRAME"

    async def test_converter_handles_empty_html_gracefully(self):
        """If HTML gen returns empty HTML, converter produces minimal frame."""
        state = PipelineState(raw_input="test")
        state.screen_htmls = [ScreenHTML(screen_name="Empty", html="")]

        state = await _convert_html_to_figma(state)

        assert len(state.figma_trees) == 1
        tree = state.figma_trees[0].tree
        assert tree["type"] == "FRAME"
        assert tree["name"] == "Empty"
        assert tree["width"] == 1440 or tree.get("width", 0) > 0


# ─── Mock API Endpoint Tests ───


class TestDesignEndpointMock:
    """Test the /generate-design API endpoint with mocked pipeline."""

    async def test_endpoint_returns_screens(self):
        """POST /generate-design should return Figma tree screens."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            side_effect=[_planner_output(), _html_generator_output()]
        )

        with (
            patch("backend.agents.planner.get_llm", return_value=mock_llm),
            patch("backend.agents.html_generator.get_llm", return_value=mock_llm),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/generate-design",
                    json={"prompt": "Build a SaaS dashboard"},
                    timeout=30.0,
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["screens"]) == 2
        assert data["errors"] == []

        # Each screen should have a tree
        for screen in data["screens"]:
            assert "screen_name" in screen
            assert "tree" in screen
            tree = screen["tree"]
            assert tree["type"] == "FRAME"
            assert len(tree.get("children", [])) > 0

    async def test_endpoint_handles_pipeline_error(self):
        """If pipeline fails, endpoint returns success=false with errors."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

        with (
            patch("backend.agents.planner.get_llm", return_value=mock_llm),
            patch("backend.agents.html_generator.get_llm", return_value=mock_llm),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/generate-design",
                    json={"prompt": "Build a dashboard"},
                    timeout=30.0,
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0


# ─── Real API E2E Tests ───

_has_api_key = bool(os.environ.get("GEMINI_API_KEY"))


@pytest.mark.real_api
@pytest.mark.skipif(not _has_api_key, reason="GEMINI_API_KEY not set")
class TestDesignPipelineRealAPI:
    """Full design pipeline with real Gemini API.

    Run with: pytest backend/tests/test_e2e/test_design_pipeline.py -m real_api -v
    """

    @pytest.fixture(autouse=True)
    def _reset_llm(self):
        reset_llm()

    async def test_full_design_pipeline_real(self):
        """Complete pipeline: prompt → plan → HTML → Figma trees.

        Verifies the full pipeline produces renderable Figma node trees.
        """
        state = PipelineState(
            raw_input=(
                "Build a SaaS financial dashboard with: "
                "1. Dashboard page showing revenue, expenses, and user metrics "
                "2. Settings page with profile form and notification preferences"
            )
        )

        # Step 1: Plan
        state = await plan(state)
        assert state.plan is not None
        assert len(state.plan.screens) >= 2
        print(f"\nPlanner output: {len(state.plan.screens)} screens")

        # Step 2: Generate HTML
        state = await generate_html(state)
        assert len(state.screen_htmls) >= 2
        for sh in state.screen_htmls:
            print(f"  {sh.screen_name}: {len(sh.html)} chars of HTML")
            assert len(sh.html) > 100, f"{sh.screen_name}: HTML too short"

        # Step 3: Convert to Figma
        state = await _convert_html_to_figma(state)
        assert len(state.figma_trees) >= 2

        for ft in state.figma_trees:
            issues = _validate_figma_tree(ft.tree, ft.screen_name)
            print(f"  {ft.screen_name}: {len(issues)} issues")
            for issue in issues:
                print(f"    - {issue}")
            # Allow minor issues but no critical ones
            critical = [i for i in issues if "no children" in i or "root is not FRAME" in i]
            assert critical == [], f"Critical issues in {ft.screen_name}: {critical}"

    async def test_generate_design_endpoint_real(self):
        """POST /generate-design with real Gemini API."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generate-design",
                json={
                    "prompt": (
                        "Build a simple task management app with "
                        "a dashboard and a settings page"
                    )
                },
                timeout=120.0,
            )

        assert response.status_code == 200
        data = response.json()

        print(f"\nsuccess: {data['success']}")
        print(f"errors: {data['errors']}")
        print(f"screen_count: {data['metadata'].get('screen_count')}")

        assert data["success"] is True
        assert len(data["screens"]) >= 1
        assert data["errors"] == []

        for screen in data["screens"]:
            print(f"\n--- {screen['screen_name']} ---")
            tree = screen["tree"]
            assert tree["type"] == "FRAME"
            children_count = len(tree.get("children", []))
            print(f"  Children: {children_count}")
            assert children_count > 0, f"{screen['screen_name']}: empty tree"
