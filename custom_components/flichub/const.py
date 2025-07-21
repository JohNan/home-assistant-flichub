"""Constants for Flic Hub."""
from homeassistant.const import Platform

# Base component constants
NAME = "Flic Hub"
DOMAIN = "flichub"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.0"
REQUIRED_SERVER_VERSION = "0.1.11"
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
EVENT_DATA_CLICK_TYPE = "click_type"
EVENT_DATA_NAME = "name"
EVENT_DATA_SERIAL_NUMBER = "serial_number"

# Platforms
PLATFORMS = [str(Platform.BINARY_SENSOR), str(Platform.SENSOR)]

# Defaults
DEFAULT_NAME = DOMAIN