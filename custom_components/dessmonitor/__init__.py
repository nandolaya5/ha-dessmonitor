"""The DessMonitor integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DessMonitorAPI, DessMonitorError
from .const import CONF_UPDATE_INTERVAL, DEFAULT_DEVADDR, DEFAULT_UPDATE_INTERVAL, DOMAIN

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

_LOGGER = logging.getLogger(__name__)


def _normalize_devcode(value: Any) -> int | None:
    """Normalize raw devcode payloads to integers when possible."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DessMonitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("Setting up DessMonitor integration for entry: %s", entry.entry_id)

    api = _create_api_client(hass, entry)
    await _authenticate_api_client(api)

    coordinator = await _create_coordinator(hass, entry, api)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.debug("Setting up platforms: %s", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("DessMonitor integration setup completed successfully")
    return True


def _create_api_client(hass: HomeAssistant, entry: ConfigEntry) -> DessMonitorAPI:
    """Create API client with storage-backed token handling."""
    username = entry.data["username"]
    pn = entry.data.get("pn", "")
    sn = entry.data.get("sn", "")
    devcode = entry.data.get("devcode", "")
    devaddr = entry.data.get("devaddr", DEFAULT_DEVADDR)
    _LOGGER.debug("Initializing API client for user: %s", username)

    store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_auth")

    return DessMonitorAPI(
        username=username,
        password=entry.data["password"],
        pn=pn,
        sn=sn,
        devcode=devcode,
        devaddr=devaddr,
        store=store,
    )


async def _authenticate_api_client(api: DessMonitorAPI) -> None:
    """Authenticate API client while honouring cached credentials."""
    try:
        if await api.load_saved_token():
            _LOGGER.info("Reused saved token for DessMonitor integration")
            return

        await _authenticate_with_token_refresh(api)
    except DessMonitorError as err:
        _LOGGER.warning(
            "DessMonitor authentication failed during setup (will retry): %s", err
        )
        raise ConfigEntryNotReady from err
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error during DessMonitor authentication: %s", err)
        _LOGGER.debug("Authentication setup error details", exc_info=True)
        raise ConfigEntryNotReady from err


async def _authenticate_with_token_refresh(api: DessMonitorAPI) -> None:
    """Perform authentication, retrying once with a fresh token if needed."""
    _LOGGER.debug("No valid cached token, performing initial authentication")
    try:
        await api.authenticate()
        _LOGGER.info("Initial authentication successful for DessMonitor integration")
        return
    except DessMonitorError:
        _LOGGER.info(
            "Cached DessMonitor token rejected during initial refresh, requesting a new token"
        )
        await api.clear_saved_token()

    _LOGGER.debug("Retrying authentication after clearing cached token")
    await api.authenticate()
    _LOGGER.info("Fresh authentication successful for DessMonitor integration")


async def _create_coordinator(
    hass: HomeAssistant, entry: ConfigEntry, api: DessMonitorAPI
) -> "DessMonitorDataUpdateCoordinator":
    """Create data coordinator and perform the initial refresh."""
    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    )
    _LOGGER.debug("Using update interval: %d seconds", update_interval)

    coordinator = DessMonitorDataUpdateCoordinator(hass, api, update_interval)
    _LOGGER.debug("Created data update coordinator, performing first refresh")

    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("First data refresh completed successfully")
    except DessMonitorError as err:
        _LOGGER.warning(
            "DessMonitor data refresh failed during setup (will retry): %s", err
        )
        raise ConfigEntryNotReady from err
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Failed to perform initial data refresh: %s", err)
        _LOGGER.debug("Initial refresh error details", exc_info=True)
        raise ConfigEntryNotReady from err

    return coordinator


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading DessMonitor integration entry: %s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        _LOGGER.debug("Coordinator removed and platforms unloaded successfully")

        if (
            coordinator is not None
            and hasattr(coordinator, "api")
            and hasattr(coordinator.api, "close")
        ):
            try:
                await coordinator.api.close()
                _LOGGER.debug("API session closed successfully")
            except Exception as err:
                _LOGGER.warning("Error closing API session: %s", err)
    else:
        _LOGGER.error("Failed to unload platforms for entry: %s", entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    _LOGGER.info("Reloading DessMonitor integration due to configuration changes")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class DessMonitorDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the DessMonitor API."""

    def __init__(
        self, hass: HomeAssistant, api: DessMonitorAPI, update_interval: int
    ) -> None:
        """Initialize."""
        self.api = api
        self.energy_flow: dict = {}
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug("Starting data update cycle")
        try:
            collectors = await self._fetch_collectors()
            data = await self._gather_all_device_data(collectors)

            try:
                energy_flow = await self.api.get_energy_flow()
                self.energy_flow = energy_flow
                _LOGGER.debug("Energy flow data received")
            except Exception as err:
                _LOGGER.warning("Failed to fetch energy flow data: %s", err)
                self.energy_flow = {}

            _LOGGER.info(
                "Data update completed successfully: %d devices total", len(data)
            )
            return data
        except DessMonitorError as err:
            if self.api._is_auth_error(str(err)):
                _LOGGER.warning("Auth error during update, clearing token and retrying")
                self.api.token = None
                await self.api.clear_saved_token()
                try:
                    collectors = await self._fetch_collectors()
                    data = await self._gather_all_device_data(collectors)
                    try:
                        energy_flow = await self.api.get_energy_flow()
                        self.energy_flow = energy_flow
                    except Exception:
                        self.energy_flow = {}
                    _LOGGER.info(
                        "Data update completed after re-auth: %d devices total", len(data)
                    )
                    return data
                except Exception as retry_err:
                    _LOGGER.error("Retry after re-auth failed: %s", retry_err)
                    raise UpdateFailed(
                        f"Error communicating with ValueClouds API: {retry_err}"
                    ) from retry_err
            _LOGGER.error(
                "Error communicating with ValueClouds API during update: %s", err
            )
            raise UpdateFailed(
                f"Error communicating with ValueClouds API: {err}"
            ) from err
        except UpdateFailed:
            raise
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                "Error communicating with ValueClouds API during update: %s", err
            )
            _LOGGER.debug("Data update error details", exc_info=True)
            raise UpdateFailed(
                f"Error communicating with ValueClouds API: {err}"
            ) from err

    async def _fetch_collectors(self) -> list[dict[str, Any]]:
        """Fetch list of collectors from the API."""
        _LOGGER.debug("Fetching collectors list")
        collectors, _projects = await self.api.get_collectors()
        _LOGGER.debug("Found %d collectors to process", len(collectors))
        return collectors

    async def _gather_all_device_data(
        self, collectors: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Collect last known data for all devices."""
        data: dict[str, Any] = {}
        errors: list[str] = []

        for index, collector in enumerate(collectors, start=1):
            collector_id = collector["pn"]
            _LOGGER.debug(
                "Processing collector %d/%d: %s",
                index,
                len(collectors),
                collector_id,
            )

            try:
                collector_devices = await self._fetch_devices_for_collector(collector)
            except DessMonitorError as err:
                _LOGGER.warning("Skipping collector %s: %s", collector_id, err)
                errors.append(f"{collector_id}: {err}")
                continue

            data.update(collector_devices)

        if not data and errors:
            raise UpdateFailed(f"All collectors failed: {'; '.join(errors)}")

        return data

    async def _fetch_devices_for_collector(
        self, collector: dict[str, Any]
    ) -> dict[str, Any]:
        """Fetch data for all devices under a collector."""
        collector_id = collector["pn"]
        devices_response = await self.api.get_collector_devices(collector_id)
        device_list = devices_response.get("dev", [])
        _LOGGER.debug("Collector %s has %d devices", collector_id, len(device_list))

        device_data: dict[str, Any] = {}
        for index, device in enumerate(device_list, start=1):
            device_sn = device["sn"]
            devcode = _normalize_devcode(device.get("devcode"))
            _LOGGER.debug(
                "Processing device %d/%d: %s (devcode=%s, devaddr=%s)",
                index,
                len(device_list),
                device_sn,
                device["devcode"],
                device["devaddr"],
            )

            try:
                last_data = await self._fetch_device_data(collector_id, device, devcode)
            except DessMonitorError as err:
                _LOGGER.warning(
                    "Skipping device %s (collector %s): %s",
                    device_sn,
                    collector_id,
                    err,
                )
                continue

            device_data[device_sn] = {
                "collector": collector,
                "device": device,
                "data": last_data,
            }

        return device_data

    async def _fetch_device_data(
        self,
        collector_id: str,
        device: dict[str, Any],
        devcode: int | None,
    ) -> list[dict[str, Any]]:
        """Fetch latest datapoints for a single device."""
        device_sn = device["sn"]

        last_data = await self.api.get_device_last_data(
            pn=collector_id,
            devcode=device["devcode"],
            devaddr=device["devaddr"],
            sn=device_sn,
        )

        _LOGGER.debug(
            "Stored data for device %s with %d data points",
            device_sn,
            len(last_data),
        )
        return last_data


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: dr.DeviceEntry
) -> dict:
    """Return diagnostics for a device entry."""
    coordinator: DessMonitorDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_sn = _resolve_device_sn(device)
    if not device_sn or device_sn not in coordinator.data:
        return {"error": "Device not found"}

    device_info = coordinator.data[device_sn]
    device_data = device_info.get("data", [])

    diagnostics = _build_base_diagnostics(device_sn, device_info, len(device_data))

    return diagnostics


def _resolve_device_sn(device: dr.DeviceEntry) -> str | None:
    """Extract DessMonitor serial number from device identifiers."""
    for domain, identifier in device.identifiers:
        if domain == DOMAIN:
            return identifier
    return None


def _build_base_diagnostics(
    device_sn: str, device_info: dict[str, Any], datapoint_count: int
) -> dict[str, Any]:
    """Return the base diagnostics structure for a device."""
    device_meta = device_info.get("device", {})
    collector_meta = device_info.get("collector", {})

    return {
        "device_info": {
            "serial_number": device_sn,
            "alias": device_meta.get("alias", "Unknown"),
            "firmware_version": collector_meta.get("fireware", "Unknown"),
            "collector_pn": collector_meta.get("pn", "Unknown"),
            "device_code": device_meta.get("devcode"),
            "device_address": device_meta.get("devaddr"),
        },
        "raw_data_points": datapoint_count,
    }
