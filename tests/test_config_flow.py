"""Config-flow tests, focused on update-interval coercion (issue #29).

The interval dropdown is backed by an integer-keyed ``vol.In``. The Home
Assistant frontend submits the chosen value as a string (e.g. ``"300"``), which
the bare ``vol.In`` rejected with "value must be one of ...". The schema now
coerces to ``int`` first; these tests lock that behaviour in for both the
initial setup and the options flow, and confirm validation is not weakened.
"""

from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dessmonitor.const import (
    CONF_COMPANY_KEY,
    CONF_PASSWORD,
    CONF_UPDATE_INTERVAL,
    CONF_USERNAME,
    DEFAULT_COMPANY_KEY,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

BASE_INPUT = {
    CONF_USERNAME: "user@example.com",
    CONF_PASSWORD: "hunter2",
    CONF_COMPANY_KEY: DEFAULT_COMPANY_KEY,
}


@pytest.mark.usefixtures("mock_validate_input", "mock_setup_entry")
@pytest.mark.parametrize("submitted", ["300", 300])
async def test_user_flow_coerces_interval(
    hass: HomeAssistant, submitted: str | int
) -> None:
    """A string interval from the frontend is accepted and stored as int."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**BASE_INPUT, CONF_UPDATE_INTERVAL: submitted}
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_UPDATE_INTERVAL] == 300
    assert isinstance(result2["data"][CONF_UPDATE_INTERVAL], int)


@pytest.mark.usefixtures("mock_validate_input", "mock_setup_entry")
async def test_user_flow_uses_default_interval(hass: HomeAssistant) -> None:
    """Omitting the interval falls back to the integer default."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], BASE_INPUT
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL


@pytest.mark.usefixtures("mock_validate_input", "mock_setup_entry")
async def test_user_flow_rejects_unknown_interval(hass: HomeAssistant) -> None:
    """Coercion must not weaken validation: a non-option value is rejected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(
            result["flow_id"], {**BASE_INPUT, CONF_UPDATE_INTERVAL: "999"}
        )


@pytest.mark.usefixtures("mock_setup_entry")
@pytest.mark.parametrize("submitted", ["600", 600])
async def test_options_flow_coerces_interval(
    hass: HomeAssistant, submitted: str | int
) -> None:
    """The options flow has the same int-keyed dropdown and must coerce too."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**BASE_INPUT, CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL},
        options={},
        unique_id="user@example.com",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_UPDATE_INTERVAL: submitted}
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_UPDATE_INTERVAL] == 600
    assert isinstance(result2["data"][CONF_UPDATE_INTERVAL], int)
