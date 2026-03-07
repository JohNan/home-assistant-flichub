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

CONF_DEADBAND_ENTER = "deadband_enter"
CONF_DEADBAND_EXIT = "deadband_exit"

# Icons
ICON = "mdi:format-quote-close"

DATA_BUTTONS = "buttons"
DATA_HUB = "network"
DATA_VIRTUAL_DEVICES = "virtual_devices"

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
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.LIGHT, Platform.MEDIA_PLAYER, Platform.COVER]

# Defaults
DEFAULT_NAME = DOMAIN

def get_button_by_id(buttons, button_id: str):
    """Helper function to find a button by serial_number or bdaddr."""
    if button_id in buttons:
        return buttons[button_id]
    for button in buttons.values():
        if button.bdaddr == button_id:
            return button
    return None