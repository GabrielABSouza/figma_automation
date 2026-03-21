"""Tests for the Validation Agent — tests against real design system files."""

from backend.agents.validator import validate
from backend.orchestrator.state import MappedUI, PipelineState, UIComponent


class TestValidatorAgent:
    def _valid_mapped_ui(self) -> MappedUI:
        return MappedUI(
            screen_name="Dashboard",
            components=[
                UIComponent(
                    id="d_section_1",
                    type="section",
                    children=[
                        UIComponent(
                            id="d_button_1",
                            type="button",
                            props={"label": "Click me", "size": "md"},
                            tokens={"background": "primary"},
                        ),
                        UIComponent(
                            id="d_text_1",
                            type="text",
                            props={"content": "Hello World"},
                            tokens={"color": "text-primary"},
                        ),
                    ],
                ),
            ],
            tokens={"background": "background"},
        )

    def _invalid_component_type(self) -> MappedUI:
        return MappedUI(
            screen_name="Broken",
            components=[
                UIComponent(
                    id="b_widget_1",
                    type="widget",  # does not exist in DS
                    props={},
                ),
            ],
        )

    def _missing_label(self) -> MappedUI:
        return MappedUI(
            screen_name="NoLabel",
            components=[
                UIComponent(
                    id="nl_button_1",
                    type="button",
                    props={"size": "md"},  # missing label
                ),
                UIComponent(
                    id="nl_input_1",
                    type="input",
                    props={"placeholder": "type here"},  # missing label
                ),
            ],
        )

    async def test_valid_ui_passes(self) -> None:
        state = PipelineState(mapped_uis=[self._valid_mapped_ui()])
        result = await validate(state)

        assert len(result.validated_uis) == 1
        assert result.validated_uis[0].validation.is_valid is True
        assert len(result.validated_uis[0].validation.errors) == 0

    async def test_invalid_component_type_fails(self) -> None:
        state = PipelineState(mapped_uis=[self._invalid_component_type()])
        result = await validate(state)

        validation = result.validated_uis[0].validation
        assert validation.is_valid is False
        assert any("widget" in e for e in validation.errors)

    async def test_missing_label_fails(self) -> None:
        state = PipelineState(mapped_uis=[self._missing_label()])
        result = await validate(state)

        validation = result.validated_uis[0].validation
        assert validation.is_valid is False
        assert any("Button" in e and "label" in e for e in validation.errors)
        assert any("Input" in e and "label" in e for e in validation.errors)

    async def test_invalid_variant_fails(self) -> None:
        state = PipelineState(
            mapped_uis=[
                MappedUI(
                    screen_name="BadVariant",
                    components=[
                        UIComponent(
                            id="bv_button_1",
                            type="button",
                            props={"label": "OK", "variant": "nonexistent"},
                        ),
                    ],
                )
            ]
        )
        result = await validate(state)

        validation = result.validated_uis[0].validation
        assert validation.is_valid is False
        assert any("variant" in e.lower() for e in validation.errors)

    async def test_nesting_depth_exceeds_limit(self) -> None:
        # Build a tree with depth 5 (exceeds max of 4)
        deep: UIComponent = UIComponent(
            id="leaf", type="text", props={"content": "x"}
        )
        for i in range(5):
            deep = UIComponent(id=f"level_{i}", type="section", children=[deep])

        state = PipelineState(
            mapped_uis=[MappedUI(screen_name="Deep", components=[deep])]
        )
        result = await validate(state)

        validation = result.validated_uis[0].validation
        assert any("nesting depth" in e for e in validation.errors)

    async def test_layout_types_skip_ds_validation(self) -> None:
        """Layout types (section, row, column, stack) should not be checked against DS."""
        state = PipelineState(
            mapped_uis=[
                MappedUI(
                    screen_name="LayoutOnly",
                    components=[
                        UIComponent(
                            id="lo_section_1",
                            type="section",
                            children=[
                                UIComponent(id="lo_row_1", type="row"),
                                UIComponent(id="lo_col_1", type="column"),
                                UIComponent(id="lo_stack_1", type="stack"),
                            ],
                        ),
                    ],
                )
            ]
        )
        result = await validate(state)

        validation = result.validated_uis[0].validation
        assert validation.is_valid is True

    async def test_empty_mapped_uis_adds_error(self) -> None:
        state = PipelineState()
        result = await validate(state)

        assert len(result.errors) > 0
        assert "no mapped UIs" in result.errors[0]

    async def test_unknown_token_produces_warning(self) -> None:
        state = PipelineState(
            mapped_uis=[
                MappedUI(
                    screen_name="TokenWarn",
                    components=[
                        UIComponent(
                            id="tw_text_1",
                            type="text",
                            props={"content": "hi"},
                            tokens={"color": "nonexistent-token-xyz"},
                        ),
                    ],
                )
            ]
        )
        result = await validate(state)

        validation = result.validated_uis[0].validation
        # Unknown token is a warning, not an error
        assert validation.is_valid is True
        assert any("nonexistent-token-xyz" in w for w in validation.warnings)
