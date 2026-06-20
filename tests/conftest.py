"""Shared fixtures for the DessMonitor test suite."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None, None, None]:
    """Enable loading of the custom integration in every test.

    ``enable_custom_integrations`` is provided by
    pytest-homeassistant-custom-component; without it Home Assistant refuses to
    load components under ``custom_components/``.
    """
    yield


@pytest.fixture
def mock_validate_input() -> Generator[None, None, None]:
    """Make config-flow validation succeed without any network access.

    The flow authenticates and then lists collectors; both are patched so the
    flow reaches entry creation deterministically. The HTTP session is stubbed
    too, so no real aiohttp/aiodns resolver thread is spawned (which would
    otherwise trip Home Assistant's lingering-thread cleanup check).
    """
    with (
        patch(
            "custom_components.dessmonitor.config_flow.async_get_clientsession",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.dessmonitor.config_flow.DessMonitorAPI.authenticate",
            return_value=True,
        ),
        patch(
            "custom_components.dessmonitor.config_flow.DessMonitorAPI.get_collectors",
            return_value=([{"pn": "PN-TEST"}], []),
        ),
    ):
        yield


@pytest.fixture
def mock_setup_entry() -> Generator[None, None, None]:
    """Stop the entry from being fully set up after the flow creates it.

    Keeps config-flow tests focused on the flow itself rather than coordinator
    start-up and live API polling.
    """
    with patch(
        "custom_components.dessmonitor.async_setup_entry",
        return_value=True,
    ):
        yield
