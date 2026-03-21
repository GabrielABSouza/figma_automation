"""Tests for Pydantic pipeline state models."""

from backend.orchestrator.state import (
    DesignPlan,
    InterpretedInput,
    MappedUI,
    PipelineState,
    RawUITree,
    ScreenPlan,
    Section,
    UIComponent,
    UXStructure,
    ValidatedUI,
    ValidationResult,
)


class TestInterpretedInput:
    def test_defaults(self) -> None:
        model = InterpretedInput()
        assert model.product_type == ""
        assert model.user_goals == []
        assert model.required_screens == []
        assert model.raw_input == ""

    def test_populated(self) -> None:
        model = InterpretedInput(
            product_type="SaaS",
            user_goals=["goal1"],
            required_screens=["Home"],
            raw_input="build a saas",
        )
        assert model.product_type == "SaaS"
        assert len(model.user_goals) == 1


class TestScreenPlan:
    def test_required_fields(self) -> None:
        plan = ScreenPlan(name="Dashboard", purpose="Main view")
        assert plan.name == "Dashboard"
        assert plan.priority == 0

    def test_with_priority(self) -> None:
        plan = ScreenPlan(name="Home", purpose="Landing", priority=1)
        assert plan.priority == 1


class TestDesignPlan:
    def test_defaults(self) -> None:
        plan = DesignPlan()
        assert plan.screens == []
        assert plan.navigation_flow == []

    def test_with_screens(self) -> None:
        plan = DesignPlan(
            screens=[ScreenPlan(name="A", purpose="a")],
            navigation_flow=["A"],
        )
        assert len(plan.screens) == 1


class TestSection:
    def test_recursive_children(self) -> None:
        section = Section(
            id="s1",
            content_type="hero",
            children=[Section(id="s1_1", content_type="text")],
        )
        assert section.type == "section"
        assert len(section.children) == 1
        assert section.children[0].id == "s1_1"


class TestUXStructure:
    def test_with_sections(self) -> None:
        ux = UXStructure(
            screen_name="Home",
            sections=[Section(id="s1", content_type="hero")],
        )
        assert ux.screen_name == "Home"
        assert len(ux.sections) == 1


class TestUIComponent:
    def test_minimal(self) -> None:
        comp = UIComponent(id="btn_1", type="button")
        assert comp.props == {}
        assert comp.tokens == {}
        assert comp.children == []

    def test_with_children(self) -> None:
        comp = UIComponent(
            id="section_1",
            type="section",
            children=[
                UIComponent(id="text_1", type="text", props={"content": "Hello"}),
                UIComponent(id="btn_1", type="button", props={"label": "Click"}),
            ],
        )
        assert len(comp.children) == 2

    def test_with_tokens(self) -> None:
        comp = UIComponent(
            id="card_1",
            type="card",
            tokens={"background": "surface", "spacing": "md"},
        )
        assert comp.tokens["background"] == "surface"

    def test_serialization_roundtrip(self) -> None:
        comp = UIComponent(
            id="btn_1",
            type="button",
            props={"label": "Go"},
            tokens={"color": "primary"},
        )
        json_str = comp.model_dump_json()
        restored = UIComponent.model_validate_json(json_str)
        assert restored.id == comp.id
        assert restored.props == comp.props
        assert restored.tokens == comp.tokens


class TestRawUITree:
    def test_with_layout(self) -> None:
        tree = RawUITree(
            screen_name="Dashboard",
            layout=[UIComponent(id="s1", type="section")],
        )
        assert tree.screen_name == "Dashboard"
        assert len(tree.layout) == 1


class TestMappedUI:
    def test_with_tokens(self) -> None:
        mapped = MappedUI(
            screen_name="Home",
            components=[UIComponent(id="t1", type="text")],
            tokens={"background": "surface"},
        )
        assert mapped.tokens["background"] == "surface"


class TestValidationResult:
    def test_default_is_invalid(self) -> None:
        result = ValidationResult()
        assert result.is_valid is False
        assert result.errors == []
        assert result.warnings == []

    def test_valid_result(self) -> None:
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True

    def test_with_errors(self) -> None:
        result = ValidationResult(is_valid=False, errors=["missing label"])
        assert not result.is_valid
        assert len(result.errors) == 1


class TestValidatedUI:
    def test_full_construction(self) -> None:
        validated = ValidatedUI(
            screen_name="Dashboard",
            components=[UIComponent(id="b1", type="button", props={"label": "OK"})],
            tokens={"bg": "background"},
            metadata={"component_count": 1},
            validation=ValidationResult(is_valid=True),
        )
        assert validated.screen_name == "Dashboard"
        assert validated.validation.is_valid is True
        assert validated.metadata["component_count"] == 1


class TestPipelineState:
    def test_defaults(self) -> None:
        state = PipelineState()
        assert state.raw_input == ""
        assert state.interpreted is None
        assert state.plan is None
        assert state.ux_structures == []
        assert state.raw_trees == []
        assert state.mapped_uis == []
        assert state.validated_uis == []
        assert state.errors == []

    def test_full_pipeline_state(self) -> None:
        state = PipelineState(
            raw_input="Build a dashboard",
            interpreted=InterpretedInput(product_type="SaaS"),
            plan=DesignPlan(
                screens=[ScreenPlan(name="Home", purpose="main")],
                navigation_flow=["Home"],
            ),
            raw_trees=[RawUITree(screen_name="Home", layout=[])],
            mapped_uis=[MappedUI(screen_name="Home")],
            validated_uis=[
                ValidatedUI(
                    screen_name="Home",
                    validation=ValidationResult(is_valid=True),
                )
            ],
        )
        assert state.interpreted is not None
        assert state.plan is not None
        assert len(state.validated_uis) == 1

    def test_serialization_roundtrip(self) -> None:
        state = PipelineState(
            raw_input="test",
            errors=["some error"],
        )
        json_str = state.model_dump_json()
        restored = PipelineState.model_validate_json(json_str)
        assert restored.raw_input == "test"
        assert restored.errors == ["some error"]
