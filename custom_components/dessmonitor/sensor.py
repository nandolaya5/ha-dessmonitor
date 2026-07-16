"""Platform for ValueClouds (DessMonitor) sensor integration."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DessMonitorDataUpdateCoordinator
from .const import (
    DIAGNOSTIC_SENSOR_TITLES,
    DOMAIN,
    ENERGY_FLOW_SENSORS,
    ENUM_SENSOR_TITLES,
    SENSOR_TYPES,
    SYSTEM_SENSORS,
    UNITS,
)
from .utils import create_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ValueClouds sensors based on a config entry."""
    _LOGGER.debug(
        "Setting up ValueClouds sensors for config entry: %s", config_entry.entry_id
    )
    coordinator: DessMonitorDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities = []

    if not coordinator.data:
        _LOGGER.debug("No coordinator data available; skipping sensor setup")
        return

    if not isinstance(coordinator.data, dict):
        _LOGGER.warning(
            "Unexpected coordinator data type %s; skipping sensor setup",
            type(coordinator.data),
        )
        return

    coordinator_data = cast(dict[str, dict[str, Any]], coordinator.data)
    _LOGGER.debug("Processing sensor data for %d devices", len(coordinator_data))

    for device_sn, raw_device_info in coordinator_data.items():
        device_info = cast(dict[str, Any], raw_device_info)
        device_data = device_info.get("data", [])
        device_meta = device_info.get("device", {})
        collector_meta = device_info.get("collector", {})

        _LOGGER.debug(
            "Processing device %s with %d data points", device_sn, len(device_data)
        )

        seen_sensors = set()
        supported_sensors = 0
        duplicate_sensors = 0

        for data_point in device_data:
            field_id = data_point.get("id") or data_point.get("title")
            if not field_id:
                continue

            sensor_config = SENSOR_TYPES.get(field_id)
            if not sensor_config:
                sensor_config = SYSTEM_SENSORS.get(field_id)

            if not sensor_config:
                continue

            sensor_key = f"{device_sn}_{field_id}"
            if sensor_key in seen_sensors:
                duplicate_sensors += 1
                continue

            seen_sensors.add(sensor_key)
            entities.append(
                ValueCloudsSensor(
                    coordinator=coordinator,
                    device_sn=device_sn,
                    device_meta=device_meta,
                    collector_meta=collector_meta,
                    field_id=field_id,
                    sensor_config=sensor_config,
                    data_point=data_point,
                )
            )
            supported_sensors += 1

        _LOGGER.info(
            "Device %s: created %d sensors, skipped %d duplicates",
            device_sn,
            supported_sensors,
            duplicate_sensors,
        )

    for sensor_id, config in ENERGY_FLOW_SENSORS.items():
        entities.append(
            EnergyFlowSensor(
                coordinator=coordinator,
                device_sn=device_sn,
                device_meta=device_meta,
                collector_meta=collector_meta,
                sensor_id=sensor_id,
                config=config,
            )
        )
        _LOGGER.debug("Created energy flow sensor: %s", config["name"])

    _LOGGER.info("Adding %d total sensors to Home Assistant", len(entities))
    async_add_entities(entities, True)


class ValueCloudsSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ValueClouds sensor."""

    def __init__(
        self,
        coordinator: DessMonitorDataUpdateCoordinator,
        device_sn: str,
        device_meta: dict[str, Any],
        collector_meta: dict[str, Any],
        field_id: str,
        sensor_config: dict[str, Any],
        data_point: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._device_sn = device_sn
        self._device_meta = device_meta
        self._collector_meta = collector_meta
        self._field_id = field_id
        self._sensor_config = sensor_config
        self._data_point = data_point

        device_alias = device_meta.get("alias", "Inverter")
        sensor_name = sensor_config.get("name", field_id)
        self._attr_name = f"{device_alias} {sensor_name}"
        self._attr_unique_id = f"{device_sn}_{field_id}"

        self._apply_unit_metadata(sensor_config.get("unit", ""))
        self._apply_sensor_traits(sensor_config)

        self._attr_device_info = create_device_info(
            device_sn, device_meta, collector_meta
        )

        _LOGGER.debug(
            "Initialized sensor: name='%s', unique_id='%s', field_id='%s'",
            self._attr_name,
            self._attr_unique_id,
            field_id,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self._attr_device_info

    def _apply_unit_metadata(self, unit: str) -> None:
        """Configure unit/device class metadata with sensible defaults."""
        native_unit, device_class, precision = self._unit_metadata_from_unit(unit)
        self._attr_native_unit_of_measurement = native_unit

        if device_class is not None:
            self._attr_device_class = device_class

        if precision is not None:
            self._attr_suggested_display_precision = precision

    @staticmethod
    def _unit_metadata_from_unit(
        unit: str,
    ) -> tuple[
        str
        | UnitOfPower
        | UnitOfEnergy
        | UnitOfElectricPotential
        | UnitOfElectricCurrent
        | UnitOfFrequency
        | UnitOfTemperature,
        SensorDeviceClass | None,
        int | None,
    ]:
        """Return (native_unit, device_class, precision) for a given unit string."""
        if unit == UNITS["POWER"]:
            return UnitOfPower.WATT, SensorDeviceClass.POWER, None
        if unit == UNITS["POWER_KW"]:
            return UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, None
        if unit == UNITS["ENERGY"]:
            return UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, None
        if unit == UNITS["VOLTAGE"]:
            return UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, 1
        if unit == UNITS["CURRENT"]:
            return UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, 1
        if unit in {UNITS["FREQUENCY"], "HZ"}:
            return UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, None
        if unit == UNITS["TEMPERATURE"]:
            return UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, None
        if unit == UNITS["PERCENTAGE"]:
            return UNITS["PERCENTAGE"], None, None
        if unit == UNITS["APPARENT_POWER"]:
            device_class = getattr(SensorDeviceClass, "APPARENT_POWER", None)
            return unit, device_class, None

        return unit, None, None

    def _apply_sensor_traits(self, sensor_config: dict[str, Any]) -> None:
        """Apply additional metadata such as state class and icons."""
        if self._field_id in ENUM_SENSOR_TITLES:
            self._attr_device_class = SensorDeviceClass.ENUM
            if self._field_id == "status":
                self._attr_options = ["OffGrid", "OnGrid", "Hybrid"]

        state_class = sensor_config.get("state_class")
        if state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING

        icon = sensor_config.get("icon")
        if icon:
            self._attr_icon = str(icon)

        if self._field_id in DIAGNOSTIC_SENSOR_TITLES:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str | float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        device_info = self.coordinator.data.get(self._device_sn)
        if not device_info:
            return None

        device_data = device_info.get("data", [])

        for data_point in device_data:
            point_id = data_point.get("id") or data_point.get("title")
            if point_id == self._field_id:
                value = data_point.get("val")
                return self._coerce_native_value(value)

        return None

    def _coerce_native_value(self, value: Any) -> str | float | None:
        """Coerce API value into Home Assistant native value format."""
        if self._field_id in ENUM_SENSOR_TITLES:
            if value is not None and value != "":
                return str(value)
            return "Unknown"

        return self._coerce_numeric_value(value)

    def _coerce_numeric_value(self, value: Any) -> float | str | None:
        """Attempt to coerce sensor value into a float when possible."""
        if value in (None, ""):
            return value

        if isinstance(value, str):
            stripped_value = value.strip()

            placeholder_values = {"-", "--", "—"}
            if stripped_value in placeholder_values or stripped_value.lower() in {
                "n/a",
                "na",
                "null",
                "none",
            }:
                return None

            value = stripped_value if stripped_value else value

        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class EnergyFlowSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ValueClouds Energy Flow sensor."""

    def __init__(
        self,
        coordinator: DessMonitorDataUpdateCoordinator,
        device_sn: str,
        device_meta: dict[str, Any],
        collector_meta: dict[str, Any],
        sensor_id: str,
        config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._device_meta = device_meta
        self._collector_meta = collector_meta
        self._sensor_id = sensor_id
        self._config = config

        self._attr_name = f"{device_meta.get('alias', 'Inverter')} {config['name']}"
        self._attr_unique_id = f"{DOMAIN}_{device_sn}_{sensor_id}"
        self._attr_icon = config.get("icon")
        self._attr_native_unit_of_measurement = config.get("unit", "")
        self._attr_state_class = (
            SensorStateClass.MEASUREMENT
            if config.get("state_class") == "measurement"
            else None
        )

        device_class = config.get("device_class")
        if device_class:
            self._attr_device_class = getattr(
                SensorDeviceClass, device_class.upper(), None
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return create_device_info(
            self._device_sn, self._device_meta, self._collector_meta
        )

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement from coordinator's energy flow data."""
        energy_flow = getattr(self.coordinator, 'energy_flow', {})
        if not energy_flow:
            return self._config.get("unit", "")

        section = self._config["section"]
        key = self._config["key"]
        section_data = energy_flow.get(section, [])

        for item in section_data:
            if item.get("par") == key:
                return item.get("unit", self._config.get("unit", ""))

        return self._config.get("unit", "")

    @property
    def native_value(self) -> float | None:
        """Return the sensor value from coordinator's energy flow data."""
        energy_flow = getattr(self.coordinator, 'energy_flow', {})
        if not energy_flow:
            return None

        section = self._config["section"]
        key = self._config["key"]
        section_data = energy_flow.get(section, [])

        for item in section_data:
            if item.get("par") == key:
                try:
                    return float(item.get("val", 0))
                except (ValueError, TypeError):
                    return None

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        energy_flow = getattr(self.coordinator, 'energy_flow', {})
        section = self._config["section"]
        key = self._config["key"]
        section_data = energy_flow.get(section, [])

        for item in section_data:
            if item.get("par") == key:
                return {
                    "source": "energy_flow",
                    "section": section,
                    "raw_value": item.get("val"),
                    "unit": item.get("unit"),
                }

        return {"source": "energy_flow", "section": section}
