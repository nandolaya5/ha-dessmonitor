"""Constants for the ValueClouds (formerly DessMonitor) integration."""

from typing import Final

DOMAIN: Final = "dessmonitor"
VERSION: Final = "2.4.0"

CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_PN: Final = "pn"
CONF_SN: Final = "sn"
CONF_DEVCODE: Final = "devcode"
CONF_DEVADDR: Final = "devaddr"
CONF_UPDATE_INTERVAL: Final = "update_interval"

DEFAULT_UPDATE_INTERVAL: Final = 5
DEFAULT_DEVADDR: Final = "4"
MIN_UPDATE_INTERVAL: Final = 5
MAX_UPDATE_INTERVAL: Final = 3600

UPDATE_INTERVAL_OPTIONS: Final = {
    5: "5 seconds (Real-time)",
    10: "10 seconds (Fast)",
    30: "30 seconds (Quick)",
    60: "1 minute (Standard)",
    300: "5 minutes (Normal)",
    600: "10 minutes (Reduced API usage)",
    1800: "30 minutes (Low usage)",
    3600: "1 hour (Minimal usage)",
}

API_BASE_URL: Final = "https://api.valueclouds.com/"
LOGIN_ENDPOINT: Final = "ppr/web/login/login"
DEVICE_ONE_DATA_ENDPOINT: Final = "ppe/api/auth/web/queryDeviceOneDataxxx"
HEADER_PROJECT: Final = "IOT"
DEFAULT_I18N: Final = "en_US"

UNITS: Final = {
    "POWER": "W",
    "POWER_KW": "kW",
    "APPARENT_POWER": "VA",
    "ENERGY": "kWh",
    "VOLTAGE": "V",
    "CURRENT": "A",
    "FREQUENCY": "Hz",
    "TEMPERATURE": "°C",
    "PERCENTAGE": "%",
}

OUTPUT_PRIORITIES = [
    "SBU",
    "SUB",
    "UTI",
    "SOL",
]

CHARGER_PRIORITIES = [
    "Utility First",
    "PV First",
    "PV Is At The Same Level As Utility",
    "Only PV",
    "Only PV charging is allowed",
]

BATTERY_TYPES = ["AGM", "FLD", "USER", "Li1", "Li2", "Li3", "Li4"]

OPERATING_MODES = [
    "Power On",
    "Standby",
    "Line",
    "Battery",
    "Fault",
    "Shutdown Approaching",
    "Off-Grid Mode",
    "Grid Mode",
    "Hybrid Mode",
    "Unknown",
]


SENSOR_TYPES = {
    "pv_voltage": {
        "name": "PV1 Voltage",
        "unit": UNITS["VOLTAGE"],
        "device_class": "voltage",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "pv_voltage_2": {
        "name": "PV2 Voltage",
        "unit": UNITS["VOLTAGE"],
        "device_class": "voltage",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "pv_voltage_3": {
        "name": "PV3 Voltage",
        "unit": UNITS["VOLTAGE"],
        "device_class": "voltage",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "pv_voltage_4": {
        "name": "PV4 Voltage",
        "unit": UNITS["VOLTAGE"],
        "device_class": "voltage",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "pv_power1": {
        "name": "PV1 Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "pv_power2": {
        "name": "PV2 Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "pv_power3": {
        "name": "PV3 Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "pv_power4": {
        "name": "PV4 Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "pv_output_power": {
        "name": "PV Total Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "energy_today": {
        "name": "PV Energy Today",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "energy_total": {
        "name": "PV Energy Total",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:solar-power",
        "category": "pv_",
    },
    "bt_battery_voltage": {
        "name": "Battery Voltage",
        "unit": UNITS["VOLTAGE"],
        "device_class": "voltage",
        "state_class": "measurement",
        "icon": "mdi:battery",
        "category": "bt_",
    },
    "bt_battery_capacity": {
        "name": "Battery SOC",
        "unit": UNITS["PERCENTAGE"],
        "device_class": "battery",
        "state_class": "measurement",
        "icon": "mdi:battery-high",
        "category": "bt_",
    },
    "battery_active_discharging_power": {
        "name": "Battery Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:battery",
        "category": "bt_",
    },
    "battery_energy_today_charge": {
        "name": "Battery Charge Today",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:battery-plus",
        "category": "bt_",
    },
    "battery_energy_today_discharge": {
        "name": "Battery Discharge Today",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:battery-minus",
        "category": "bt_",
    },
    "battery_energy_total_charge": {
        "name": "Battery Charge Total",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:battery-plus",
        "category": "bt_",
    },
    "battery_energy_total_discharge": {
        "name": "Battery Discharge Total",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:battery-minus",
        "category": "bt_",
    },
    "gd_grid_voltage": {
        "name": "Grid Voltage",
        "unit": UNITS["VOLTAGE"],
        "device_class": "voltage",
        "state_class": "measurement",
        "icon": "mdi:transmission-tower",
        "category": "gd_",
    },
    "grid_active_sell_power": {
        "name": "Grid Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:transmission-tower",
        "category": "gd_",
    },
    "grid_ct_sell_power": {
        "name": "Grid CT Power",
        "unit": UNITS["POWER_KW"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:transmission-tower",
        "category": "gd_",
    },
    "energy_today_from_grid": {
        "name": "Grid Energy Today Import",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:transmission-tower-import",
        "category": "gd_",
    },
    "energy_today_to_grid": {
        "name": "Grid Energy Today Export",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:transmission-tower-export",
        "category": "gd_",
    },
    "energy_total_from_grid": {
        "name": "Grid Energy Total Import",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:transmission-tower-import",
        "category": "gd_",
    },
    "energy_total_to_grid": {
        "name": "Grid Energy Total Export",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:transmission-tower-export",
        "category": "gd_",
    },
    "load_active_power": {
        "name": "Load Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt",
        "category": "bc_",
    },
    "load_energy_today": {
        "name": "Load Energy Today",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:home-lightning-bolt",
        "category": "bc_",
    },
    "load_energy_total": {
        "name": "Load Energy Total",
        "unit": UNITS["ENERGY"],
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:home-lightning-bolt",
        "category": "bc_",
    },
    "generator_output_power": {
        "name": "Generator Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:generator",
        "category": "fd_",
    },
    "inverter_active_power": {
        "name": "Inverter Power",
        "unit": UNITS["POWER"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:flash",
        "category": "inv_",
    },
    "grid_home_load_sell_power": {
        "name": "Home Load Power",
        "unit": UNITS["POWER_KW"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt",
        "category": "bc_",
    },
    "grid_all_load_sell_power": {
        "name": "All Load Power",
        "unit": UNITS["POWER_KW"],
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt",
        "category": "bc_",
    },
}

SYSTEM_SENSORS = {
    "status": {
        "name": "System State",
        "unit": "",
        "icon": "mdi:power-settings",
        "category": "sy_",
    },
    "eybond_read_31834": {
        "name": "Charge State",
        "unit": "",
        "icon": "mdi:battery-charging",
        "category": "system",
    },
    "eybond_read_31839": {
        "name": "Inverter Temperature",
        "unit": UNITS["TEMPERATURE"],
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
        "category": "system",
    },
    "eybond_read_31840": {
        "name": "DC Temperature",
        "unit": UNITS["TEMPERATURE"],
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
        "category": "system",
    },
    "eybond_read_31841": {
        "name": "Transformer Temperature",
        "unit": UNITS["TEMPERATURE"],
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
        "category": "system",
    },
    "eybond_read_31842": {
        "name": "Environment Temperature",
        "unit": UNITS["TEMPERATURE"],
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
        "category": "system",
    },
    "eybond_read_31843": {
        "name": "Battery Temperature",
        "unit": UNITS["TEMPERATURE"],
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
        "category": "system",
    },
    "eybond_read_31802": {
        "name": "Grid Frequency",
        "unit": UNITS["FREQUENCY"],
        "device_class": "frequency",
        "state_class": "measurement",
        "icon": "mdi:sine-wave",
        "category": "system",
    },
    "eybond_read_31807": {
        "name": "Inverter Frequency",
        "unit": UNITS["FREQUENCY"],
        "device_class": "frequency",
        "state_class": "measurement",
        "icon": "mdi:sine-wave",
        "category": "system",
    },
    "soft_version_1": {
        "name": "Software Version 1",
        "unit": "",
        "icon": "mdi:chip",
        "entity_category": "diagnostic",
        "category": "system",
    },
    "soft_version_2": {
        "name": "Software Version 2",
        "unit": "",
        "icon": "mdi:chip",
        "entity_category": "diagnostic",
        "category": "system",
    },
    "soft_version_3": {
        "name": "Software Version 3",
        "unit": "",
        "icon": "mdi:chip",
        "entity_category": "diagnostic",
        "category": "system",
    },
    "hardware_version_1": {
        "name": "Hardware Version",
        "unit": "",
        "icon": "mdi:chip",
        "entity_category": "diagnostic",
        "category": "system",
    },
    "sn": {
        "name": "Serial Number",
        "unit": "",
        "icon": "mdi:identifier",
        "entity_category": "diagnostic",
        "category": "system",
    },
}

ENUM_SENSOR_TITLES = {
    "status",
    "eybond_read_31834",
}

DIAGNOSTIC_SENSOR_TITLES = {
    "soft_version_1",
    "soft_version_2",
    "soft_version_3",
    "hardware_version_1",
    "sn",
}

BINARY_SENSOR_TYPES: dict = {}

DIAGNOSTIC_SENSOR_TYPES: dict = {}

ENERGY_FLOW_SENSORS = {
    "battery_capacity": {
        "key": "bt_battery_capacity",
        "section": "bt_status",
        "name": "Battery SOC",
        "unit": "%",
        "device_class": "battery",
        "state_class": "measurement",
        "icon": "mdi:battery-high",
    },
    "battery_power_flow": {
        "key": "battery_active_power",
        "section": "bt_status",
        "name": "Battery Power Flow",
        "unit": "W",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:battery",
    },
    "pv_power_flow": {
        "key": "pv_output_power",
        "section": "pv_status",
        "name": "PV Power Flow",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
    },
    "grid_power_flow": {
        "key": "grid_active_power",
        "section": "gd_status",
        "name": "Grid Power Flow",
        "unit": "W",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:transmission-tower",
    },
    "load_power_flow": {
        "key": "load_active_power",
        "section": "bc_status",
        "name": "Load Power Flow",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt",
    },
}
