"""HTML Generator Agent — generates production-quality HTML for each screen.

Replaces the old UI Generator + Mapper pipeline. The LLM has full creative
freedom to design beautiful interfaces using HTML with inline styles.

The generated HTML is converted to Figma nodes by a deterministic converter,
so the HTML MUST use only supported CSS properties (listed in the system prompt).
"""

import logging

from pydantic import BaseModel, Field

from backend.design_system.components import get_component_catalog_for_prompt
from backend.design_system.icons import get_icon_reference_for_prompt
from backend.design_system.loader import load_design_system
from backend.llm.factory import get_llm
from backend.orchestrator.state import PipelineState, ScreenHTML

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a world-class UI/UX designer who creates stunning, production-quality \
web interfaces indistinguishable from Linear, Vercel, Stripe, and Notion.

Your HTML will be converted to Figma nodes by a deterministic converter. \
You MUST use ONLY the CSS properties listed below. Any unsupported property \
will be SILENTLY IGNORED, causing broken layouts.

## Design Philosophy (shadcn/ui + Radix)

Your designs follow the shadcn/ui component system exactly:
- Clean, minimal aesthetics with generous whitespace
- Subtle depth via shadows (never borders on cards unless intentional)
- Consistent 4/8px spacing grid
- Inter font family, precise type scale
- Lucide icons for ALL iconography (NEVER use emoji)
- Muted color palette with intentional accent colors
- Every element feels purposeful and considered

## Supported CSS Properties (ONLY use these)

### Layout
- `display: flex` (REQUIRED on every container element)
- `flex-direction: row | column` (REQUIRED with display:flex)
- `gap: Npx` (spacing between children)
- `align-items: center | flex-start | flex-end | stretch`
- `justify-content: center | flex-start | flex-end | space-between`
- `flex: 1` or `flex-grow: 1` (fill available space)

### Size
- `width: Npx` or `width: 100%`
- `height: Npx`
- `min-width: Npx` / `min-height: Npx`

### Spacing
- `padding: Npx` or `padding: Npx Npx Npx Npx`
- `padding-top`, `padding-right`, `padding-bottom`, `padding-left`

### Visual
- `background-color: #hex | rgba(r,g,b,a)`
- `border: Npx solid #hex`
- `border-bottom: Npx solid #hex` (and other sides)
- `border-radius: Npx | 50% | 9999px`
- `box-shadow: offsetX offsetY blur rgba(r,g,b,a)`
- `opacity: 0-1`
- `overflow: hidden`

### Typography (text elements ONLY: p, h1-h6, span, label, small, a, strong, em)
- `font-size: Npx`
- `font-weight: 400 | 500 | 600 | 700`
- `color: #hex | rgba()`
- `line-height: Npx`
- `letter-spacing: Npx | 0.05em`
- `text-align: left | center | right`
- `text-transform: uppercase | lowercase | capitalize`

## FORBIDDEN CSS (will be SILENTLY IGNORED)

margin, position, top/right/bottom/left, transform, transition, animation, \
grid, float, calc(), z-index, cursor, white-space, outline, \
background: linear-gradient(), display: grid, var(), media queries.

## Icons — Lucide (MANDATORY)

Use `data-icon` attribute on a `<div>` to render Lucide vector icons. \
NEVER use emoji. NEVER use text symbols as icons. ALWAYS use data-icon.

```html
<div data-icon='home' style='width: 18px; height: 18px; color: #64748B'></div>
```

Common sizes: 14px (inline/small), 16px (buttons), 18px (nav items), \
20px (section icons), 24px (large/standalone), 28-48px (empty states).

{icon_reference}

## Critical Layout Rules

1. NEVER use margin — use `gap` on parent.
2. EVERY container MUST have `display: flex; flex-direction: column` or `row`.
3. Equal-width siblings: parent `flex-direction: row; gap: 24px`, each child `flex: 1`.
4. Root div: `width: 1440px; height: 900px; display: flex; flex-direction: row` (for sidebar layouts).
5. Sidebar: `width: 260px; height: 900px` (FIXED, never flex:1). Main content: `flex: 1`.
6. Text elements MUST NOT have `display: flex`.
7. `<input>` elements get auto-styled — use `placeholder` attribute.
8. Use single quotes for ALL HTML attribute values.
9. All sizes in px. No em, rem, vh, vw, %.
10. NO JavaScript, NO <style> tags, NO SVG elements, NO <img> tags.
11. Buttons: use `align-items: flex-start` on button's parent column to prevent stretching.
12. Breadcrumbs: keep text short, never use `flex: 1` on breadcrumb text spans.

{component_catalog}

## CROSS-SCREEN CONSISTENCY (CRITICAL)

The sidebar and top navigation bar MUST be IDENTICAL across ALL screens. \
This means the EXACT same sidebar items, icons, labels, sections, and user profile \
must appear on every screen. The ONLY difference is which item has the active \
(highlighted) state.

Sidebar requirements:
- MUST include ALL navigation items on EVERY screen (do NOT omit items)
- Group items with section labels (e.g., "OVERVIEW", "ACCOUNT")
- Active item: `background-color: #2563EB` with white text/icon
- Inactive items: muted text/icon color (#94A3B8)
- Bottom: user profile with avatar, name, email, and logout icon

Top bar requirements:
- Breadcrumb navigation (current location)
- Search bar and action buttons (consistent across all screens)

## Content Density

Fill the entire 900px viewport height with content. NO large empty areas. \
If the main content doesn't naturally fill the space:
- Add MORE data rows (tables: 8-12 rows, lists: 6-8 items)
- Add more sections (summary stats, charts, recent activity)
- Use `flex: 1` on the content scroll area to fill remaining space

Minimum content requirements:
- Tables: at least 7 rows of data
- Lists: at least 5 items
- Dashboards: at least 3 metric cards + 2 content sections
- Charts/graphs: use chart placeholder with realistic legend entries (5+)

## Quality Standard

Your output MUST be indistinguishable from a real SaaS product designed by \
a top-tier team. Use realistic data (names, dollar amounts, dates, statuses). \
Every pixel matters. White cards on light gray backgrounds. Subtle shadows. \
Proper visual hierarchy. Icons for EVERY navigational element and metric.

CRITICAL: Every container element MUST have display:flex with flex-direction. \
Omitting this WILL break the layout completely.\
"""


class ScreenHTMLItem(BaseModel):
    """HTML output for a single screen."""

    screen_name: str
    html: str


class HTMLGeneratorOutput(BaseModel):
    """Output from the HTML generator — HTML for all screens."""

    screens: list[ScreenHTMLItem] = Field(min_length=1, max_length=6)


def _build_user_prompt(state: PipelineState) -> str:
    """Build the user prompt from pipeline state."""
    plan = state.plan
    if not plan:
        raise ValueError("Pipeline state has no design plan")

    screen_descriptions = []
    for screen in plan.screens:
        screen_descriptions.append(
            f"- **{screen.name}** (priority {screen.priority}): {screen.purpose}"
        )

    interpreted = state.interpreted
    product_context = ""
    if interpreted:
        product_context = (
            f"Product type: {interpreted.product_type}\n"
            f"User goals: {', '.join(interpreted.user_goals)}\n"
        )

    screens_text = "\n".join(screen_descriptions)
    nav_flow = ", ".join(plan.navigation_flow) if plan.navigation_flow else "N/A"

    # Inject design system tokens for visual consistency
    ds = load_design_system()
    tokens = ds.tokens
    colors = tokens.get("colors", {})
    spacing = tokens.get("spacing", {})
    typography = tokens.get("typography", {})

    color_lines = [f"  - {k}: {v}" for k, v in colors.items()]
    spacing_lines = [f"  - {k}: {v}px" for k, v in spacing.items()]
    typo_lines = [
        f"  - {k}: {v.get('fontSize', '')}px / weight {v.get('fontWeight', '')}"
        for k, v in typography.items()
        if isinstance(v, dict)
    ]

    design_tokens = (
        "## Design Tokens (use these exact values for consistency)\n\n"
        "Colors:\n" + "\n".join(color_lines) + "\n\n"
        "Spacing:\n" + "\n".join(spacing_lines) + "\n\n"
        "Typography:\n" + "\n".join(typo_lines) + "\n"
    )

    return (
        f"Design a complete, production-quality UI for this product.\n\n"
        f"PRODUCT DESCRIPTION:\n{state.raw_input}\n\n"
        f"{product_context}"
        f"SCREENS TO DESIGN:\n{screens_text}\n\n"
        f"NAVIGATION FLOW: {nav_flow}\n\n"
        f"{design_tokens}\n"
        f"## Instructions\n\n"
        f"For EACH screen listed above, generate a complete HTML layout with inline styles.\n"
        f"Each screen MUST be a self-contained `<div>` with `width: 1440px`.\n\n"
        f"CRITICAL REMINDERS:\n"
        f"- Use `gap` for spacing between siblings. NEVER use `margin`.\n"
        f"- Every container MUST have `display: flex` with explicit `flex-direction`.\n"
        f"- Cards in a row MUST each have `flex: 1` so they fill equal widths.\n"
        f"- Use `width: 100%` for elements that should fill parent width.\n"
        f"- Use Lucide icons via data-icon for ALL iconography. NEVER use emoji.\n"
        f"- Every nav item MUST have an icon. Every metric card MUST have an icon.\n"
        f"- Include realistic placeholder data — real names, dollar amounts, dates.\n"
        f"- The design MUST be cohesive across all screens "
        f"(same color palette, typography, spacing).\n"
        f"- COMPOSE screens from the Component Library patterns in the system prompt.\n"
        f"- Root div: width: 1440px; height: 900px. Fill the ENTIRE viewport.\n"
        f"- SIDEBAR MUST BE IDENTICAL across all screens (same items, same order, "
        f"same icons). Only the active/highlighted item changes per screen.\n"
        f"- Tables: at least 7 rows. Lists: at least 5 items. Fill the space!\n\n"
        f"Return a JSON object with a 'screens' array, where each item has:\n"
        f"  - 'screen_name': the screen name (PascalCase)\n"
        f"  - 'html': the complete HTML string for that screen\n"
    )


def _build_system_prompt() -> str:
    """Build the full system prompt with injected component catalog and icons."""
    icon_ref = get_icon_reference_for_prompt()
    catalog = get_component_catalog_for_prompt()

    return SYSTEM_PROMPT.format(
        icon_reference=icon_ref,
        component_catalog=catalog,
    )


async def generate_html(state: PipelineState) -> PipelineState:
    """Generate beautiful HTML for all screens defined in the plan."""
    llm = get_llm()

    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(state)
    logger.debug("HTML generator system prompt (%d chars)", len(system_prompt))
    logger.debug("HTML generator user prompt (%d chars):\n%s", len(user_prompt), user_prompt)

    result = await llm.generate(
        prompt=user_prompt,
        output_schema=HTMLGeneratorOutput,
        system_prompt=system_prompt,
    )

    state.screen_htmls = [
        ScreenHTML(screen_name=s.screen_name, html=s.html) for s in result.screens
    ]

    for sh in state.screen_htmls:
        logger.info(
            "HTML generated: screen='%s', length=%d chars",
            sh.screen_name,
            len(sh.html),
        )

    return state
