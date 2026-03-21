from typing import Any

from pydantic import BaseModel, Field


class InterpretedInput(BaseModel):
    product_type: str = ""
    user_goals: list[str] = Field(default_factory=list)
    required_screens: list[str] = Field(default_factory=list)
    raw_input: str = ""


class ScreenPlan(BaseModel):
    name: str
    purpose: str
    priority: int = 0


class DesignPlan(BaseModel):
    screens: list[ScreenPlan] = Field(default_factory=list)
    navigation_flow: list[str] = Field(default_factory=list)


class Section(BaseModel):
    id: str
    type: str = "section"
    content_type: str = ""
    children: list["Section"] = Field(default_factory=list)


class UXStructure(BaseModel):
    screen_name: str
    sections: list[Section] = Field(default_factory=list)


class UIComponent(BaseModel):
    id: str
    type: str
    props: dict[str, Any] = Field(default_factory=dict)
    tokens: dict[str, str] = Field(default_factory=dict)
    children: list["UIComponent"] = Field(default_factory=list)


class RawUITree(BaseModel):
    screen_name: str
    layout: list[UIComponent] = Field(default_factory=list)


class MappedUI(BaseModel):
    screen_name: str
    components: list[UIComponent] = Field(default_factory=list)
    tokens: dict[str, str] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ValidatedUI(BaseModel):
    screen_name: str
    components: list[UIComponent] = Field(default_factory=list)
    tokens: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    validation: ValidationResult = Field(default_factory=ValidationResult)


class PipelineState(BaseModel):
    """Full state passed through the LangGraph pipeline."""

    raw_input: str = ""
    interpreted: InterpretedInput | None = None
    plan: DesignPlan | None = None
    ux_structures: list[UXStructure] = Field(default_factory=list)
    raw_trees: list[RawUITree] = Field(default_factory=list)
    mapped_uis: list[MappedUI] = Field(default_factory=list)
    validated_uis: list[ValidatedUI] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
