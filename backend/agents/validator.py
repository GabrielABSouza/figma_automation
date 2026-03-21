"""Validation Agent — ensures component existence, token consistency, and rule compliance.

Pure Python validation — no LLM calls. All rules are deterministic.
"""

from backend.design_system.loader import DesignSystemData, load_design_system
from backend.orchestrator.state import (
    MappedUI,
    PipelineState,
    UIComponent,
    ValidatedUI,
    ValidationResult,
)

# Layout-only types that are structural, not in the design system
LAYOUT_TYPES = {"section", "row", "column", "stack"}


def _validate_component(
    component: UIComponent,
    ds: DesignSystemData,
    errors: list[str],
    warnings: list[str],
    depth: int = 0,
    component_count: list[int] | None = None,
) -> None:
    """Recursively validate a single component and its children."""
    if component_count is None:
        component_count = [0]
    component_count[0] += 1

    # Check nesting depth
    max_depth = ds.rules.get("hierarchy", {}).get("max_nesting_depth", 4)
    if depth > max_depth:
        errors.append(
            f"Component '{component.id}' exceeds max nesting depth of {max_depth}"
        )

    # Skip layout types — they are structural, not DS components
    if component.type not in LAYOUT_TYPES:
        valid_types = ds.component_types()
        if component.type not in valid_types:
            errors.append(
                f"Component '{component.id}' has type '{component.type}' "
                f"which does not exist in the design system. "
                f"Valid types: {sorted(valid_types)}"
            )
        else:
            # Validate variant if present in props
            variant = component.props.get("variant")
            if variant:
                valid_variants = ds.variants_for(component.type)
                if variant not in valid_variants:
                    errors.append(
                        f"Component '{component.id}' ({component.type}) has "
                        f"invalid variant '{variant}'. "
                        f"Valid variants: {valid_variants}"
                    )

            # Validate button_must_have_label
            constraints = ds.rules.get("constraints", {})
            if (
                component.type == "button"
                and constraints.get("button_must_have_label")
                and not component.props.get("label")
            ):
                errors.append(f"Button '{component.id}' must have a 'label' prop")

            # Validate input_must_have_label
            if (
                component.type == "input"
                and constraints.get("input_must_have_label")
                and not component.props.get("label")
            ):
                errors.append(f"Input '{component.id}' must have a 'label' prop")

    # Validate token references
    all_tokens = ds.all_token_names()
    for _token_key, token_value in component.tokens.items():
        if token_value not in all_tokens:
            warnings.append(
                f"Component '{component.id}' references token '{token_value}' "
                f"which may not exist in the design system"
            )

    # Recurse into children
    for child in component.children:
        _validate_component(child, ds, errors, warnings, depth + 1, component_count)


def _validate_mapped_ui(mapped_ui: MappedUI, ds: DesignSystemData) -> ValidationResult:
    """Validate a single mapped UI screen against the design system."""
    errors: list[str] = []
    warnings: list[str] = []
    component_count = [0]

    for component in mapped_ui.components:
        _validate_component(
            component, ds, errors, warnings, depth=0, component_count=component_count
        )

    # Check max_components_per_screen
    max_components = ds.rules.get("constraints", {}).get("max_components_per_screen", 50)
    if component_count[0] > max_components:
        errors.append(
            f"Screen '{mapped_ui.screen_name}' has {component_count[0]} components, "
            f"exceeding the maximum of {max_components}"
        )

    # Validate screen-level tokens
    all_tokens = ds.all_token_names()
    for _token_key, token_value in mapped_ui.tokens.items():
        if token_value not in all_tokens:
            warnings.append(
                f"Screen '{mapped_ui.screen_name}' references token "
                f"'{token_value}' which may not exist"
            )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


async def validate(state: PipelineState) -> PipelineState:
    """Validate all mapped UIs against the design system and schema constraints."""
    if not state.mapped_uis:
        state.errors.append("Validator: no mapped UIs available")
        return state

    ds = load_design_system()

    for mapped_ui in state.mapped_uis:
        result = _validate_mapped_ui(mapped_ui, ds)

        state.validated_uis.append(
            ValidatedUI(
                screen_name=mapped_ui.screen_name,
                components=mapped_ui.components,
                tokens=mapped_ui.tokens,
                metadata={"component_count": len(mapped_ui.components)},
                validation=result,
            )
        )

    return state
