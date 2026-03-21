"""Tests for FastAPI API endpoints — stub endpoints return not_implemented."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.fixture
def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestGenerateUI:
    async def test_returns_not_implemented(self, client: AsyncClient) -> None:
        response = await client.post(
            "/generate-ui", params={"prompt": "Build a dashboard"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "not_implemented"

    async def test_missing_prompt_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/generate-ui")
        assert response.status_code == 422


class TestIterateUI:
    async def test_returns_not_implemented(self, client: AsyncClient) -> None:
        response = await client.post(
            "/iterate-ui",
            params={"pipeline_run_id": "abc123", "feedback": "make it blue"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "not_implemented"


class TestGetDesignSystem:
    async def test_returns_not_implemented(self, client: AsyncClient) -> None:
        response = await client.get("/design-system")
        assert response.status_code == 200
        assert response.json()["status"] == "not_implemented"


class TestAppMeta:
    async def test_openapi_schema_available(self, client: AsyncClient) -> None:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Figma Automation Pipeline"
        assert schema["info"]["version"] == "0.1.0"
