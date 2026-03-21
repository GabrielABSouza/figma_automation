"""Shared pytest configuration and fixtures."""

from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env from project root so GEMINI_API_KEY is available during test collection
_project_root = Path(__file__).resolve().parents[2]
load_dotenv(_project_root / ".env")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip tests marked with `real_api` unless `-m real_api` is explicitly passed."""
    if config.getoption("-m") == "real_api":
        return

    skip_real = pytest.mark.skip(reason="pass -m real_api to run real API tests")
    for item in items:
        if "real_api" in item.keywords:
            item.add_marker(skip_real)
