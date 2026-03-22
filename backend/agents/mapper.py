"""Design System Mapper Agent — maps abstract UI to real design system components."""

from pydantic import BaseModel, Field

from backend.design_system.loader import load_design_system
from backend.llm.factory import get_llm
from backend.orchestrator.state import MappedUI, PipelineState, UIComponent

SYSTEM_PROMPT = """\
You are a design system specialist who maps abstract UI structures to a concrete
design system.

Your task is to take a raw UI component tree and transform it into a fully-mapped
UI that uses ONLY components, variants, and tokens from the provided design system.

Rules:
1. Every leaf component's "type" MUST match a component type in the design system.
2. Layout types (section, row, column, stack) are NOT design system components —
   they are structural and must be preserved as-is with type unchanged.
3. For each design system component, assign a valid "variant" from the component's
   variant list in the props field (e.g., props: {"variant": "primary"}).
4. Props must match the component definition. Use appropriate values.
5. Apply design tokens in the "tokens" field using bare token names from the token
   system. Example: {"background": "surface", "color": "text-primary", "spacing": "md"}.
6. Preserve the component hierarchy and all IDs from the input.
7. Do NOT invent components or tokens not in the design system.
8. Every button MUST have a "label" prop with meaningful text.
9. Every input MUST have a "label" prop with descriptive text.
10. Apply spacing tokens consistently: sections use "md" or "lg" spacing,
    rows use "md" spacing, cards use "md" padding.
11. Apply "surface" background to cards by default. Do NOT apply background to sections.
12. Apply shadows: cards get "sm" shadow, elevated cards get "md" shadow.
13. Every text component MUST have a "color" token: headings use "text-primary",
    body text uses "text-primary" or "text-secondary", captions use "text-muted".
14. Preserve "title" props on sections — do NOT remove existing props.
15. Apply borderRadius "md" to cards and buttons, "sm" to inputs, "full" to avatars.

Output ONLY valid JSON matching the provided schema.\
"""


class MapperOutput(BaseModel):
    """LLM output for a single mapped screen."""

    screen_name: str
    components: list[UIComponent] = Field(min_length=1)
    tokens: dict[str, str] = Field(default_factory=dict)


def _build_user_prompt(raw_tree_json: str, ds_context: str) -> str:
    return (
        f"Map the following raw UI tree to the design system.\n\n"
        f"{ds_context}\n\n"
        f"RAW UI TREE:\n{raw_tree_json}\n\n"
        f"Transform each component to use valid design system types, variants, "
        f"props, and tokens. Preserve layout structure (section/row/column/stack). "
        f"Also assign screen-level tokens (e.g., background, default spacing)."
    )


async def map_to_design_system(state: PipelineState) -> PipelineState:
    """Map abstract UI trees to real design system components."""
    if not state.raw_trees:
        state.errors.append("Mapper: no raw UI trees available")
        return state

    llm = get_llm()
    ds = load_design_system()
    ds_context = ds.to_prompt_context()

    for raw_tree in state.raw_trees:
        raw_tree_json = raw_tree.model_dump_json(indent=2)

        result = await llm.generate(
            prompt=_build_user_prompt(raw_tree_json, ds_context),
            output_schema=MapperOutput,
            system_prompt=SYSTEM_PROMPT,
        )

        state.mapped_uis.append(
            MappedUI(
                screen_name=result.screen_name,
                components=result.components,
                tokens=result.tokens,
            )
        )

    return state
