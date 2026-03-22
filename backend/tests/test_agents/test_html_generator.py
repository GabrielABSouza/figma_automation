"""Tests for the HTML Generator agent.

Level 1: Verifies that the LLM generates structurally sound, high-quality HTML.

- Mock tests: validate prompt construction and output schema handling.
- Real API tests: send actual prompts to Gemini and verify the HTML output
  for structural integrity, proper inline styles, and realistic content.
  Run with: pytest -m real_api
"""

import os
import re
from html.parser import HTMLParser
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.html_generator import (
    HTMLGeneratorOutput,
    ScreenHTMLItem,
    _build_user_prompt,
    generate_html,
)
from backend.llm.factory import reset_llm
from backend.orchestrator.state import (
    DesignPlan,
    InterpretedInput,
    PipelineState,
    ScreenPlan,
)

# ─── Helpers ───


def _make_state(
    prompt: str = "Build a SaaS dashboard",
    screens: list[ScreenPlan] | None = None,
) -> PipelineState:
    """Create a PipelineState with plan for testing."""
    if screens is None:
        screens = [
            ScreenPlan(name="Dashboard", purpose="Main metrics overview", priority=1),
            ScreenPlan(name="Settings", purpose="App configuration", priority=2),
        ]
    return PipelineState(
        raw_input=prompt,
        interpreted=InterpretedInput(
            product_type="dashboard",
            user_goals=["View metrics", "Manage settings"],
        ),
        plan=DesignPlan(
            screens=screens,
            navigation_flow=[s.name for s in screens],
        ),
    )


class HTMLStructureValidator(HTMLParser):
    """Validates basic HTML structure — balanced tags, no forbidden elements."""

    FORBIDDEN_TAGS = {"script", "style", "link", "img", "svg", "iframe"}
    VOID_TAGS = {
        "br", "hr", "input", "meta", "area", "base",
        "col", "embed", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__()
        self.errors: list[str] = []
        self.tag_stack: list[str] = []
        self.element_count = 0
        self.text_content: list[str] = []
        self.has_inline_styles = False
        self.has_class_names = False
        self.style_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.element_count += 1

        if tag in self.FORBIDDEN_TAGS:
            self.errors.append(f"Forbidden tag: <{tag}>")

        attr_dict = dict(attrs)
        if "class" in attr_dict:
            self.has_class_names = True
        if "style" in attr_dict:
            self.has_inline_styles = True
            self.style_count += 1

        if tag not in self.VOID_TAGS:
            self.tag_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.VOID_TAGS:
            return
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        else:
            self.errors.append(f"Mismatched closing tag: </{tag}>")

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.text_content.append(text)


def validate_html(html: str) -> HTMLStructureValidator:
    """Parse HTML and return the validator with results."""
    v = HTMLStructureValidator()
    v.feed(html)
    return v


# ─── Mock Tests (no API calls) ───


class TestBuildUserPrompt:
    def test_includes_product_description(self):
        state = _make_state("Build a financial tracker")
        prompt = _build_user_prompt(state)
        assert "financial tracker" in prompt.lower()

    def test_includes_screen_names(self):
        state = _make_state()
        prompt = _build_user_prompt(state)
        assert "Dashboard" in prompt
        assert "Settings" in prompt

    def test_includes_navigation_flow(self):
        state = _make_state()
        prompt = _build_user_prompt(state)
        assert "Dashboard" in prompt
        assert "Settings" in prompt

    def test_raises_without_plan(self):
        state = PipelineState(raw_input="test")
        with pytest.raises(ValueError, match="no design plan"):
            _build_user_prompt(state)


class TestGenerateHTMLMock:
    def _mock_html_output(self) -> HTMLGeneratorOutput:
        return HTMLGeneratorOutput(
            screens=[
                ScreenHTMLItem(
                    screen_name="Dashboard",
                    html="<div style='display: flex; flex-direction: column; width: 1440px'>"
                    "<h1 style='font-size: 32px; font-weight: 700'>Dashboard</h1>"
                    "</div>",
                ),
                ScreenHTMLItem(
                    screen_name="Settings",
                    html="<div style='display: flex; flex-direction: column; width: 1440px'>"
                    "<h1 style='font-size: 32px; font-weight: 700'>Settings</h1>"
                    "</div>",
                ),
            ]
        )

    async def test_generates_html_for_all_screens(self):
        state = _make_state()
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=self._mock_html_output())

        with patch("backend.agents.html_generator.get_llm", return_value=mock_llm):
            result = await generate_html(state)

        assert len(result.screen_htmls) == 2
        assert result.screen_htmls[0].screen_name == "Dashboard"
        assert result.screen_htmls[1].screen_name == "Settings"

    async def test_html_contains_content(self):
        state = _make_state()
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=self._mock_html_output())

        with patch("backend.agents.html_generator.get_llm", return_value=mock_llm):
            result = await generate_html(state)

        for screen_html in result.screen_htmls:
            assert "<div" in screen_html.html
            assert "style=" in screen_html.html

    async def test_llm_called_once(self):
        state = _make_state()
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=self._mock_html_output())

        with patch("backend.agents.html_generator.get_llm", return_value=mock_llm):
            await generate_html(state)

        # HTML generator makes a single LLM call for all screens
        assert mock_llm.generate.call_count == 1

    async def test_errors_on_missing_plan(self):
        state = PipelineState(raw_input="test")
        mock_llm = AsyncMock()

        with (
            patch("backend.agents.html_generator.get_llm", return_value=mock_llm),
            pytest.raises(ValueError, match="no design plan"),
        ):
            await generate_html(state)


# ─── Real API Tests (require GEMINI_API_KEY) ───

pytestmark_real = pytest.mark.real_api
_has_api_key = bool(os.environ.get("GEMINI_API_KEY"))


@pytest.mark.real_api
@pytest.mark.skipif(not _has_api_key, reason="GEMINI_API_KEY not set")
class TestHTMLGeneratorRealAPI:
    """Send real prompts to Gemini and verify HTML quality.

    Run with: pytest backend/tests/test_agents/test_html_generator.py -m real_api -v
    """

    @pytest.fixture(autouse=True)
    def _reset_llm(self):
        reset_llm()

    async def test_generates_valid_html_for_dashboard(self):
        """LLM should produce well-structured HTML with inline styles."""
        state = _make_state(
            "Build a SaaS financial dashboard with revenue metrics, "
            "user analytics, and a recent transactions table",
            screens=[
                ScreenPlan(name="Dashboard", purpose="Financial metrics overview", priority=1),
            ],
        )

        result = await generate_html(state)

        assert len(result.screen_htmls) >= 1
        html = result.screen_htmls[0].html

        # Structural integrity
        v = validate_html(html)
        assert v.element_count >= 5, f"Too few elements ({v.element_count})"
        assert len(v.errors) == 0, f"HTML errors: {v.errors}"

        # Has inline styles (not class-based)
        assert v.has_inline_styles, "No inline styles found"
        assert v.style_count >= 3, f"Too few styled elements ({v.style_count})"

        # Contains realistic text content
        assert len(v.text_content) >= 3, "Too little text content"

        # Has a root div with width
        assert "1440" in html, "Root should have 1440px width"

        # Uses flexbox
        assert "display: flex" in html or "display:flex" in html, "Should use flexbox"

    async def test_generates_multiple_screens(self):
        """LLM should produce HTML for each requested screen."""
        state = _make_state(
            "Build an e-commerce admin panel",
            screens=[
                ScreenPlan(name="Dashboard", purpose="Sales overview", priority=1),
                ScreenPlan(name="Products", purpose="Product listing", priority=2),
            ],
        )

        result = await generate_html(state)

        assert len(result.screen_htmls) >= 2
        screen_names = [s.screen_name for s in result.screen_htmls]
        assert "Dashboard" in screen_names
        assert "Products" in screen_names

        # Each screen should have substantial HTML
        for screen_html in result.screen_htmls:
            v = validate_html(screen_html.html)
            assert v.element_count >= 5, (
                f"{screen_html.screen_name}: too few elements ({v.element_count})"
            )
            assert v.has_inline_styles, f"{screen_html.screen_name}: no inline styles"

    async def test_html_has_proper_styling(self):
        """Verify the HTML uses proper CSS properties for a polished design."""
        state = _make_state(
            "Build a project management tool dashboard",
            screens=[
                ScreenPlan(name="Dashboard", purpose="Project overview", priority=1),
            ],
        )

        result = await generate_html(state)
        html = result.screen_htmls[0].html

        # Should have proper CSS patterns
        # Background colors
        assert re.search(r"background-color:\s*#[0-9a-fA-F]{3,6}", html), (
            "Should have hex background colors"
        )

        # Font sizes
        assert re.search(r"font-size:\s*\d+px", html), "Should have font sizes in px"

        # Padding
        assert re.search(r"padding:\s*\d+px", html), "Should have padding values"

        # Border radius (for cards/buttons)
        assert re.search(r"border-radius:\s*\d+px", html), "Should have border-radius"

    async def test_no_forbidden_elements(self):
        """HTML should not contain script, style tags, SVG, or img elements."""
        state = _make_state(
            "Build a user management dashboard",
            screens=[
                ScreenPlan(name="Users", purpose="User management", priority=1),
            ],
        )

        result = await generate_html(state)
        html = result.screen_htmls[0].html

        v = validate_html(html)
        assert len(v.errors) == 0, f"Forbidden elements found: {v.errors}"

        # Double-check with regex
        assert "<script" not in html.lower(), "Should not contain <script>"
        assert "<style>" not in html.lower(), "Should not contain <style> tags"
        assert "<svg" not in html.lower(), "Should not contain <svg>"

    async def test_html_has_realistic_data(self):
        """HTML should contain realistic placeholder data, not lorem ipsum."""
        state = _make_state(
            "Build a financial tracking SaaS dashboard with revenue, expenses, and profit metrics",
            screens=[
                ScreenPlan(name="Dashboard", purpose="Financial overview with KPIs", priority=1),
            ],
        )

        result = await generate_html(state)
        v = validate_html(result.screen_htmls[0].html)
        all_text = " ".join(v.text_content).lower()

        # Should have actual content — numbers, dollar signs, or meaningful words
        has_numbers = bool(re.search(r"\d+", all_text))
        has_dollar = "$" in all_text or "revenue" in all_text or "profit" in all_text
        assert has_numbers or has_dollar, (
            f"Expected realistic data in text content, got: {all_text[:200]}"
        )
