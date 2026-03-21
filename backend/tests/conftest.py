"""Shared pytest configuration and fixtures."""

import pytest


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
