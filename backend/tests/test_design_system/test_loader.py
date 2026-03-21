"""Tests for the Design System loader — validates loading, caching, and helpers."""

import json

from backend.design_system.loader import (
    ComponentDef,
    DesignSystemData,
    load_design_system,
)


class TestComponentDef:
    def test_minimal(self) -> None:
        comp = ComponentDef(type="button")
        assert comp.type == "button"
        assert comp.variants == []
        assert comp.props == {}

    def test_with_variants_and_props(self) -> None:
        comp = ComponentDef(
            type="button",
            variants=["primary", "secondary"],
            props={"label": "string", "disabled": "boolean"},
        )
        assert len(comp.variants) == 2
        assert comp.props["label"] == "string"


class TestDesignSystemData:
    def _sample_ds(self) -> DesignSystemData:
        return DesignSystemData(
            tokens={
                "colors": {"primary": "#2563EB", "background": "#FFFFFF"},
                "spacing": {"sm": 8, "md": 16},
            },
            components=[
                ComponentDef(
                    type="button",
                    variants=["primary", "secondary"],
                    props={"label": "string"},
                ),
                ComponentDef(
                    type="card",
                    variants=["default", "outlined"],
                    props={"title": "string|null"},
                ),
                ComponentDef(type="divider", variants=[], props={}),
            ],
            rules={"constraints": {"max_components_per_screen": 50}},
        )

    def test_component_types(self) -> None:
        ds = self._sample_ds()
        types = ds.component_types()
        assert types == {"button", "card", "divider"}

    def test_variants_for_existing_type(self) -> None:
        ds = self._sample_ds()
        variants = ds.variants_for("button")
        assert variants == ["primary", "secondary"]

    def test_variants_for_unknown_type(self) -> None:
        ds = self._sample_ds()
        variants = ds.variants_for("nonexistent")
        assert variants == []

    def test_all_token_names_includes_prefixed_and_bare(self) -> None:
        ds = self._sample_ds()
        names = ds.all_token_names()
        # Bare names
        assert "primary" in names
        assert "background" in names
        assert "sm" in names
        assert "md" in names
        # Prefixed names
        assert "colors.primary" in names
        assert "spacing.sm" in names

    def test_all_token_names_skips_non_dict_values(self) -> None:
        ds = DesignSystemData(
            tokens={"version": "1.0"},  # not a dict value
        )
        names = ds.all_token_names()
        assert len(names) == 0

    def test_to_prompt_context_format(self) -> None:
        ds = self._sample_ds()
        context = ds.to_prompt_context()
        assert context.startswith("=== DESIGN SYSTEM ===")
        assert "TOKENS:" in context
        assert "COMPONENTS:" in context
        assert "RULES:" in context
        assert "primary" in context
        assert "button" in context

    def test_to_prompt_context_is_valid_json_fragments(self) -> None:
        ds = self._sample_ds()
        context = ds.to_prompt_context()
        # Extract and validate the tokens JSON fragment
        tokens_start = context.index("TOKENS:\n") + len("TOKENS:\n")
        tokens_end = context.index("\n\nCOMPONENTS:")
        tokens_json = context[tokens_start:tokens_end]
        parsed = json.loads(tokens_json)
        assert "colors" in parsed

    def test_defaults(self) -> None:
        ds = DesignSystemData()
        assert ds.tokens == {}
        assert ds.components == []
        assert ds.rules == {}
        assert ds.component_types() == set()
        assert ds.all_token_names() == set()


class TestLoadDesignSystem:
    def test_loads_real_files(self) -> None:
        # Clear lru_cache between tests
        load_design_system.cache_clear()
        ds = load_design_system()

        # Validate tokens loaded correctly
        assert "colors" in ds.tokens
        assert ds.tokens["colors"]["primary"] == "#2563EB"
        assert "spacing" in ds.tokens
        assert "typography" in ds.tokens

        # Validate components loaded
        types = ds.component_types()
        assert "button" in types
        assert "card" in types
        assert "input" in types
        assert "text" in types
        assert "navbar" in types
        assert "table" in types
        assert "avatar" in types
        assert "badge" in types
        assert "divider" in types
        assert len(types) == 9

        # Validate rules loaded
        assert ds.rules["hierarchy"]["max_nesting_depth"] == 4
        assert ds.rules["constraints"]["max_components_per_screen"] == 50

    def test_button_variants(self) -> None:
        load_design_system.cache_clear()
        ds = load_design_system()
        variants = ds.variants_for("button")
        assert variants == ["primary", "secondary", "ghost", "danger"]

    def test_text_variants(self) -> None:
        load_design_system.cache_clear()
        ds = load_design_system()
        variants = ds.variants_for("text")
        assert "heading-1" in variants
        assert "body" in variants

    def test_caching_returns_same_instance(self) -> None:
        load_design_system.cache_clear()
        ds1 = load_design_system()
        ds2 = load_design_system()
        assert ds1 is ds2

    def test_all_token_names_from_real_files(self) -> None:
        load_design_system.cache_clear()
        ds = load_design_system()
        names = ds.all_token_names()
        # Check a few known tokens
        assert "primary" in names
        assert "colors.primary" in names
        assert "md" in names
        assert "spacing.md" in names
        assert "heading-1" in names
        assert "typography.heading-1" in names

    def test_prompt_context_from_real_files(self) -> None:
        load_design_system.cache_clear()
        ds = load_design_system()
        context = ds.to_prompt_context()
        assert "=== DESIGN SYSTEM ===" in context
        assert "#2563EB" in context  # primary color token
        assert "button" in context
        assert "max_nesting_depth" in context

    def test_cache_clear_reloads(self) -> None:
        load_design_system.cache_clear()
        ds1 = load_design_system()
        load_design_system.cache_clear()
        ds2 = load_design_system()
        # After clearing cache, should get a new (but equal) instance
        assert ds1 is not ds2
        assert ds1.component_types() == ds2.component_types()
