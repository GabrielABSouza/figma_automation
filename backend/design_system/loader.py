"""Design system loader — reads and caches tokens, components, and rules."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_DS_DIR = Path(__file__).parent


class ComponentDef(BaseModel):
    """A single component definition from components.json."""

    type: str
    variants: list[str] = Field(default_factory=list)
    props: dict[str, Any] = Field(default_factory=dict)


class DesignSystemData(BaseModel):
    """Complete design system data, loaded and cached from JSON files."""

    tokens: dict[str, Any] = Field(default_factory=dict)
    components: list[ComponentDef] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)

    def component_types(self) -> set[str]:
        """Return set of valid component type names."""
        return {c.type for c in self.components}

    def variants_for(self, component_type: str) -> list[str]:
        """Return valid variants for a component type, or empty list."""
        for c in self.components:
            if c.type == component_type:
                return c.variants
        return []

    def all_token_names(self) -> set[str]:
        """Return all token names across all categories (both prefixed and bare)."""
        names: set[str] = set()
        for category, values in self.tokens.items():
            if isinstance(values, dict):
                for key in values:
                    names.add(f"{category}.{key}")
                    names.add(key)
        return names

    def to_prompt_context(self) -> str:
        """Serialize the entire DS into a prompt-friendly string."""
        return (
            "=== DESIGN SYSTEM ===\n\n"
            f"TOKENS:\n{json.dumps(self.tokens, indent=2)}\n\n"
            f"COMPONENTS:\n"
            f"{json.dumps([c.model_dump() for c in self.components], indent=2)}\n\n"
            f"RULES:\n{json.dumps(self.rules, indent=2)}\n"
        )


@lru_cache(maxsize=1)
def load_design_system() -> DesignSystemData:
    """Load and cache the design system from JSON files."""
    tokens = json.loads((_DS_DIR / "tokens.json").read_text())
    raw_components = json.loads((_DS_DIR / "components.json").read_text())
    rules = json.loads((_DS_DIR / "rules.json").read_text())

    components = [ComponentDef(**c) for c in raw_components["components"]]

    return DesignSystemData(tokens=tokens, components=components, rules=rules)
