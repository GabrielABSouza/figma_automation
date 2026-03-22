"""Design Planner Agent — defines list of screens and navigation flow.

In MVP, also handles intent extraction (substituting the Interpreter agent).
"""

import logging

from pydantic import BaseModel, Field

from backend.llm.factory import get_llm
from backend.orchestrator.state import (
    DesignPlan,
    InterpretedInput,
    PipelineState,
    ScreenPlan,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior product designer and information architect.

Your task is to analyze a product description and produce a structured design plan.

You MUST:
1. Identify the product type (e.g., "SaaS dashboard", "e-commerce", "landing page").
2. Extract 2-5 concrete user goals from the description.
3. Define 2-6 screens needed to fulfill those goals.
4. Assign each screen a clear purpose and priority (1 = highest priority).
5. Define the navigation flow as an ordered list of screen names.

Constraints:
- Keep screen count between 2 and 6 for MVP scope.
- Screen names must be concise PascalCase (e.g., "Dashboard", "UserProfile", "Settings").
- Every screen must have a unique name.
- Navigation flow must include all screen names.
- Priority 1 is the main/landing screen.

Output ONLY valid JSON matching the provided schema.\
"""


class PlannerOutput(BaseModel):
    """Combined output: interpretation + plan in a single LLM call."""

    product_type: str
    user_goals: list[str] = Field(min_length=1, max_length=5)
    screens: list[ScreenPlan] = Field(min_length=2, max_length=6)
    navigation_flow: list[str] = Field(min_length=2, max_length=6)


def _build_user_prompt(raw_input: str) -> str:
    return (
        f"Analyze the following product description and create a design plan.\n\n"
        f"PRODUCT DESCRIPTION:\n{raw_input}\n\n"
        f"Produce a JSON object with: product_type, user_goals, screens "
        f"(each with name, purpose, priority), and navigation_flow."
    )


async def plan(state: PipelineState) -> PipelineState:
    """Generate a design plan with screens and navigation from raw input."""
    llm = get_llm()

    user_prompt = _build_user_prompt(state.raw_input)
    logger.debug("Planner prompt:\n%s", user_prompt)

    result = await llm.generate(
        prompt=user_prompt,
        output_schema=PlannerOutput,
        system_prompt=SYSTEM_PROMPT,
    )

    logger.info(
        "Planner result: product_type=%s, screens=%s, nav=%s",
        result.product_type,
        [s.name for s in result.screens],
        result.navigation_flow,
    )

    # Populate interpreted input (MVP substitute for the Interpreter agent)
    state.interpreted = InterpretedInput(
        product_type=result.product_type,
        user_goals=result.user_goals,
        required_screens=[s.name for s in result.screens],
        raw_input=state.raw_input,
    )

    state.plan = DesignPlan(
        screens=result.screens,
        navigation_flow=result.navigation_flow,
    )

    return state
