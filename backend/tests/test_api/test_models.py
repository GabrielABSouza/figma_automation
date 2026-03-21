"""Tests for API request/response model validation."""

import pytest
from pydantic import ValidationError

from backend.api.models import (
    DesignSystemResponse,
    ErrorResponse,
    GenerateUIRequest,
    GenerateUIResponse,
    ScreenResponse,
    UIComponentResponse,
    ValidationResultResponse,
)


class TestGenerateUIRequest:
    def test_valid_prompt(self) -> None:
        req = GenerateUIRequest(prompt="Build a dashboard")
        assert req.prompt == "Build a dashboard"

    def test_empty_prompt_raises(self) -> None:
        with pytest.raises(ValidationError):
            GenerateUIRequest(prompt="")

    def test_missing_prompt_raises(self) -> None:
        with pytest.raises(ValidationError):
            GenerateUIRequest()  # type: ignore[call-arg]

    def test_whitespace_only_prompt_is_valid(self) -> None:
        req = GenerateUIRequest(prompt=" ")
        assert req.prompt == " "


class TestGenerateUIResponse:
    def test_success_response(self) -> None:
        resp = GenerateUIResponse(
            success=True,
            screens=[
                ScreenResponse(
                    screen_name="Home",
                    components=[UIComponentResponse(id="h1", type="text")],
                    validation=ValidationResultResponse(is_valid=True),
                )
            ],
            metadata={"prompt": "test", "screen_count": 1},
        )
        assert resp.success is True
        assert len(resp.screens) == 1

    def test_error_response(self) -> None:
        resp = GenerateUIResponse(
            success=False,
            errors=["Pipeline failed"],
            metadata={"prompt": "test"},
        )
        assert resp.success is False
        assert resp.screens == []

    def test_defaults(self) -> None:
        resp = GenerateUIResponse(success=False)
        assert resp.screens == []
        assert resp.errors == []
        assert resp.metadata == {}


class TestUIComponentResponse:
    def test_recursive_children(self) -> None:
        comp = UIComponentResponse(
            id="parent",
            type="section",
            children=[
                UIComponentResponse(
                    id="child", type="text", props={"content": "Hello"}
                )
            ],
        )
        assert len(comp.children) == 1
        assert comp.children[0].type == "text"

    def test_defaults(self) -> None:
        comp = UIComponentResponse(id="c1", type="button")
        assert comp.props == {}
        assert comp.tokens == {}
        assert comp.children == []


class TestDesignSystemResponse:
    def test_full_response(self) -> None:
        resp = DesignSystemResponse(
            tokens={"colors": {"primary": "#000"}},
            components=[{"type": "button", "variants": ["primary"]}],
            rules={"constraints": {}},
        )
        assert resp.tokens["colors"]["primary"] == "#000"
        assert len(resp.components) == 1

    def test_defaults(self) -> None:
        resp = DesignSystemResponse()
        assert resp.tokens == {}
        assert resp.components == []
        assert resp.rules == {}


class TestErrorResponse:
    def test_error_response_fields(self) -> None:
        resp = ErrorResponse(error="not_found", detail="Resource missing")
        assert resp.success is False
        assert resp.error == "not_found"
        assert resp.detail == "Resource missing"

    def test_detail_is_optional(self) -> None:
        resp = ErrorResponse(error="internal_server_error")
        assert resp.detail is None


class TestScreenResponse:
    def test_serialization_roundtrip(self) -> None:
        screen = ScreenResponse(
            screen_name="Dashboard",
            components=[
                UIComponentResponse(
                    id="d1",
                    type="card",
                    children=[UIComponentResponse(id="d2", type="text")],
                ),
            ],
            tokens={"bg": "surface"},
            metadata={"component_count": 2},
            validation=ValidationResultResponse(
                is_valid=True, warnings=["minor issue"]
            ),
        )
        data = screen.model_dump()
        restored = ScreenResponse.model_validate(data)
        assert restored.screen_name == "Dashboard"
        assert len(restored.components) == 1
        assert len(restored.components[0].children) == 1
        assert restored.validation.warnings == ["minor issue"]
