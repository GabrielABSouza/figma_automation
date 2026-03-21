"""Tests for the API layer — endpoints, error handling, and integration."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.orchestrator.state import (
    DesignPlan,
    InterpretedInput,
    MappedUI,
    PipelineState,
    RawUITree,
    ScreenPlan,
    UIComponent,
    ValidatedUI,
    ValidationResult,
)


@pytest.fixture
def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ─── State Builders ───


def _successful_state(prompt: str = "Build a dashboard") -> PipelineState:
    return PipelineState(
        raw_input=prompt,
        interpreted=InterpretedInput(
            product_type="SaaS",
            user_goals=["View metrics"],
            required_screens=["Dashboard"],
            raw_input=prompt,
        ),
        plan=DesignPlan(
            screens=[ScreenPlan(name="Dashboard", purpose="Main view", priority=1)],
            navigation_flow=["Dashboard"],
        ),
        raw_trees=[
            RawUITree(
                screen_name="Dashboard",
                layout=[
                    UIComponent(id="d_text_1", type="text", props={"content": "Hello"})
                ],
            )
        ],
        mapped_uis=[
            MappedUI(
                screen_name="Dashboard",
                components=[
                    UIComponent(
                        id="d_text_1",
                        type="text",
                        props={"content": "Hello", "variant": "heading-1"},
                        tokens={"color": "text-primary"},
                    )
                ],
                tokens={"background": "background"},
            )
        ],
        validated_uis=[
            ValidatedUI(
                screen_name="Dashboard",
                components=[
                    UIComponent(
                        id="d_text_1",
                        type="text",
                        props={"content": "Hello", "variant": "heading-1"},
                        tokens={"color": "text-primary"},
                    )
                ],
                tokens={"background": "background"},
                metadata={"component_count": 1},
                validation=ValidationResult(is_valid=True),
            )
        ],
    )


def _failed_state(prompt: str = "Build something") -> PipelineState:
    return PipelineState(
        raw_input=prompt,
        errors=["Node 'plan' failed after 2 retries: LLM service unavailable"],
    )


def _partial_state(prompt: str = "Build a dashboard") -> PipelineState:
    return PipelineState(
        raw_input=prompt,
        validated_uis=[
            ValidatedUI(
                screen_name="Dashboard",
                components=[UIComponent(id="bad_1", type="widget")],
                metadata={"component_count": 1},
                validation=ValidationResult(
                    is_valid=False,
                    errors=["Unknown component type 'widget'"],
                ),
            )
        ],
    )


# ─── POST /generate-ui — Happy Path ───


class TestGenerateUIHappyPath:
    async def test_returns_200_with_screens(self, client: AsyncClient) -> None:
        with patch(
            "backend.api.routes.run_pipeline",
            new_callable=AsyncMock,
            return_value=_successful_state(),
        ):
            response = await client.post(
                "/generate-ui", json={"prompt": "Build a dashboard"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["screens"]) == 1
        assert data["screens"][0]["screen_name"] == "Dashboard"
        assert data["errors"] == []

    async def test_response_contains_metadata(self, client: AsyncClient) -> None:
        with patch(
            "backend.api.routes.run_pipeline",
            new_callable=AsyncMock,
            return_value=_successful_state("Build a fintech app"),
        ):
            response = await client.post(
                "/generate-ui", json={"prompt": "Build a fintech app"}
            )

        data = response.json()
        assert data["metadata"]["prompt"] == "Build a fintech app"
        assert data["metadata"]["screen_count"] == 1
        assert data["metadata"]["schema_version"] == "1.0.0"
        assert data["metadata"]["all_screens_valid"] is True

    async def test_screen_contains_components_tokens_validation(
        self, client: AsyncClient
    ) -> None:
        with patch(
            "backend.api.routes.run_pipeline",
            new_callable=AsyncMock,
            return_value=_successful_state(),
        ):
            response = await client.post(
                "/generate-ui", json={"prompt": "Build a dashboard"}
            )

        screen = response.json()["screens"][0]
        assert len(screen["components"]) == 1
        assert screen["components"][0]["type"] == "text"
        assert screen["components"][0]["tokens"]["color"] == "text-primary"
        assert screen["tokens"]["background"] == "background"
        assert screen["validation"]["is_valid"] is True
        assert screen["metadata"]["component_count"] == 1

    async def test_pipeline_called_with_prompt(self, client: AsyncClient) -> None:
        mock_run = AsyncMock(return_value=_successful_state())
        with patch("backend.api.routes.run_pipeline", mock_run):
            await client.post(
                "/generate-ui", json={"prompt": "Build a SaaS dashboard"}
            )

        mock_run.assert_called_once_with("Build a SaaS dashboard")


# ─── POST /generate-ui — Pipeline Errors ───


class TestGenerateUIWithPipelineErrors:
    async def test_pipeline_error_returns_200_with_success_false(
        self, client: AsyncClient
    ) -> None:
        with patch(
            "backend.api.routes.run_pipeline",
            new_callable=AsyncMock,
            return_value=_failed_state(),
        ):
            response = await client.post(
                "/generate-ui", json={"prompt": "Build something"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0
        assert data["screens"] == []
        assert "plan" in data["errors"][0]

    async def test_partial_result_with_invalid_screens(
        self, client: AsyncClient
    ) -> None:
        with patch(
            "backend.api.routes.run_pipeline",
            new_callable=AsyncMock,
            return_value=_partial_state(),
        ):
            response = await client.post(
                "/generate-ui", json={"prompt": "Build a dashboard"}
            )

        data = response.json()
        assert data["success"] is True
        assert len(data["screens"]) == 1
        assert data["screens"][0]["validation"]["is_valid"] is False
        assert "widget" in data["screens"][0]["validation"]["errors"][0]

    async def test_unexpected_exception_returns_structured_error(
        self, client: AsyncClient
    ) -> None:
        with patch(
            "backend.api.routes.run_pipeline",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected crash"),
        ):
            response = await client.post(
                "/generate-ui", json={"prompt": "Build something"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert any("Unexpected crash" in e for e in data["errors"])


# ─── POST /generate-ui — Validation ───


class TestGenerateUIValidation:
    async def test_missing_prompt_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/generate-ui", json={})
        assert response.status_code == 422

    async def test_empty_prompt_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/generate-ui", json={"prompt": ""})
        assert response.status_code == 422

    async def test_no_body_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/generate-ui")
        assert response.status_code == 422

    async def test_prompt_as_query_param_no_longer_works(
        self, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/generate-ui", params={"prompt": "Build a dashboard"}
        )
        assert response.status_code == 422


# ─── GET /design-system ───


class TestGetDesignSystem:
    async def test_returns_200_with_tokens(self, client: AsyncClient) -> None:
        response = await client.get("/design-system")
        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert "components" in data
        assert "rules" in data

    async def test_tokens_contain_colors(self, client: AsyncClient) -> None:
        response = await client.get("/design-system")
        data = response.json()
        assert "colors" in data["tokens"]
        assert data["tokens"]["colors"]["primary"] == "#2563EB"

    async def test_components_list_has_expected_types(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/design-system")
        data = response.json()
        component_types = {c["type"] for c in data["components"]}
        assert "button" in component_types
        assert "card" in component_types
        assert "input" in component_types
        assert "text" in component_types
        assert len(data["components"]) == 9

    async def test_rules_contain_constraints(self, client: AsyncClient) -> None:
        response = await client.get("/design-system")
        data = response.json()
        assert data["rules"]["constraints"]["max_components_per_screen"] == 50
        assert data["rules"]["hierarchy"]["max_nesting_depth"] == 4

    async def test_components_include_variants(self, client: AsyncClient) -> None:
        response = await client.get("/design-system")
        data = response.json()
        button = next(c for c in data["components"] if c["type"] == "button")
        assert button["variants"] == ["primary", "secondary", "ghost", "danger"]


# ─── POST /iterate-ui ───


class TestIterateUI:
    async def test_still_returns_not_implemented(self, client: AsyncClient) -> None:
        response = await client.post(
            "/iterate-ui",
            params={"pipeline_run_id": "abc123", "feedback": "make it blue"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_implemented"


# ─── Error Handling ───


class TestErrorHandling:
    async def test_global_exception_handler_returns_json(self) -> None:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        error_client = AsyncClient(transport=transport, base_url="http://test")

        with patch(
            "backend.api.routes.load_design_system",
            side_effect=FileNotFoundError("tokens.json missing"),
        ):
            response = await error_client.get("/design-system")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "internal_server_error"
        assert "tokens.json" in data["detail"]

    async def test_404_on_unknown_route(self, client: AsyncClient) -> None:
        response = await client.get("/nonexistent")
        assert response.status_code == 404


# ─── App Meta ───


class TestAppMeta:
    async def test_openapi_schema_available(self, client: AsyncClient) -> None:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Figma Automation Pipeline"
        assert schema["info"]["version"] == "0.1.0"

    async def test_openapi_includes_endpoints(self, client: AsyncClient) -> None:
        response = await client.get("/openapi.json")
        paths = response.json()["paths"]
        assert "/generate-ui" in paths
        assert "/design-system" in paths
        assert "/iterate-ui" in paths
