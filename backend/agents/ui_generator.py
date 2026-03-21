"""UI Generator Agent — generates raw UI tree per screen (layout-first, not styled)."""

from pydantic import BaseModel, Field

from backend.llm.factory import get_llm
from backend.orchestrator.state import PipelineState, RawUITree, UIComponent

SYSTEM_PROMPT = """\
You are a senior UI architect who creates structured UI layouts.

Your task is to generate a raw UI component tree for a single screen based on its
purpose and the overall product context.

Rules:
1. Use ONLY these component types:
   - Layout types: section, row, column, stack
   - Leaf types: text, button, input, card, navbar, table, avatar, badge, divider
2. Every component MUST have a unique id using the format: "{screen}_{type}_{n}"
   (e.g., "Dashboard_card_1", "UserProfile_input_2").
3. Layout components (section, row, column, stack) contain children.
   Leaf components (text, button, input, etc.) should NOT have children.
4. Build a reasonable hierarchy: screen -> sections -> rows/columns -> leaf components.
5. Maximum nesting depth: 4 levels.
6. Maximum 50 components per screen.
7. Do NOT apply styling or design tokens — the "tokens" field must be empty ({})
   for all components. Styling is applied in the next pipeline stage.
8. Props should contain semantic content appropriate for the screen's purpose:
   - text: {"content": "actual text"}
   - button: {"label": "action text"}
   - input: {"label": "field name", "placeholder": "hint"}
9. Generate a realistic, functional UI — not just placeholder elements.

Output ONLY valid JSON matching the provided schema.\
"""


class UIGeneratorOutput(BaseModel):
    """LLM output schema for a single screen's UI tree."""

    screen_name: str
    layout: list[UIComponent] = Field(min_length=1, max_length=50)


def _build_user_prompt(
    screen_name: str,
    screen_purpose: str,
    product_type: str,
    all_screens: list[str],
    navigation_flow: list[str],
) -> str:
    return (
        f"Generate a UI component tree for the following screen.\n\n"
        f"PRODUCT TYPE: {product_type}\n"
        f"ALL SCREENS: {', '.join(all_screens)}\n"
        f"NAVIGATION FLOW: {' -> '.join(navigation_flow)}\n\n"
        f"TARGET SCREEN: {screen_name}\n"
        f"PURPOSE: {screen_purpose}\n\n"
        f"Create a hierarchical layout with sections, rows/columns, and leaf "
        f"components appropriate for this screen's purpose. Use semantic prop values."
    )


async def generate_ui(state: PipelineState) -> PipelineState:
    """Generate raw UI trees from the design plan — one tree per screen."""
    if not state.plan or not state.plan.screens:
        state.errors.append("UI Generator: no design plan available")
        return state

    llm = get_llm()
    product_type = state.interpreted.product_type if state.interpreted else "application"
    all_screen_names = [s.name for s in state.plan.screens]

    for screen in state.plan.screens:
        result = await llm.generate(
            prompt=_build_user_prompt(
                screen_name=screen.name,
                screen_purpose=screen.purpose,
                product_type=product_type,
                all_screens=all_screen_names,
                navigation_flow=state.plan.navigation_flow,
            ),
            output_schema=UIGeneratorOutput,
            system_prompt=SYSTEM_PROMPT,
        )

        state.raw_trees.append(
            RawUITree(
                screen_name=result.screen_name,
                layout=result.layout,
            )
        )

    return state
