"""Constants for Flic Hub."""
from homeassistant.const import Platform

# Base component constants
NAME = "Flic Hub"
DOMAIN = "flichub"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.0"
REQUIRED_SERVER_VERSION = "0.1.13"
DEFAULT_SCAN_INTERVAL = 60

CLIENT_READY_TIMEOUT = 20.0

# Icons
ICON = "mdi:format-quote-close"

DATA_BUTTONS = "buttons"
DATA_HUB = "network"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Events
EVENT_CLICK = f"{DOMAIN}_click"
EVENT_ACTION_MESSAGE = f"{DOMAIN}_action_message"
EVENT_VIRTUAL_DEVICE_UPDATE = f"{DOMAIN}_virtual_device_update"

EVENT_DATA_CLICK_TYPE = "click_type"
EVENT_DATA_NAME = "name"
EVENT_DATA_SERIAL_NUMBER = "serial_number"
EVENT_DATA_ACTION = "action"
EVENT_DATA_META_DATA = "meta_data"
EVENT_DATA_VALUES = "values"
EVENT_DATA_BUTTON_NUMBER = "button_number"

# Platforms
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

# Defaults
DEFAULT_NAME = DOMAIN