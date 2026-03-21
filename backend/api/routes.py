from fastapi import APIRouter

router = APIRouter()


@router.post("/generate-ui")
async def generate_ui(prompt: str) -> dict:
    """Full pipeline: prompt → structured UI JSON."""
    # TODO: wire to orchestrator
    return {"status": "not_implemented"}


@router.post("/iterate-ui")
async def iterate_ui(pipeline_run_id: str, feedback: str) -> dict:
    """Partial re-run with user feedback."""
    # TODO: wire to orchestrator with partial execution
    return {"status": "not_implemented"}


@router.get("/design-system")
async def get_design_system() -> dict:
    """Return active design system (tokens, components, rules)."""
    # TODO: load from design_system/
    return {"status": "not_implemented"}
