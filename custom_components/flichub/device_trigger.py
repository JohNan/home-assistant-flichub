"""Provides device triggers for Flic Hub."""
import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant, CALLBACK_TYPE
from homeassistant.helpers import config_validation as cv, device_registry as dr, entity_registry as er
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.components.homeassistant.triggers import event as event_trigger

import re

from .const import DOMAIN, EVENT_CLICK, EVENT_DATA_CLICK_TYPE, EVENT_DATA_SERIAL_NUMBER, EVENT_DATA_BUTTON_NUMBER

# The trigger types that a button can emit
TRIGGER_TYPES = {"single", "double", "hold", "down", "up", "double_hold"}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): cv.matches_regex(r"^(single|double|hold|down|up|double_hold)(?:_button_(\d+))?$"),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict]:
    """List device triggers for Flic Hub button devices."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)

    # Make sure device is managed by this domain
    if device is None or DOMAIN not in [identifier[0] for identifier in device.identifiers]:
        return []

    # We shouldn't add button triggers for the Hub itself.
    is_hub = device.model == "LR" or device.name == "Flic Hub"
    if is_hub:
        return []

    triggers = [
        {
            CONF_PLATFORM: "device",
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_id,
            CONF_TYPE: trigger_type,
        }
        for trigger_type in TRIGGER_TYPES
    ]

    # Flic Duo dynamically populates a button_number when an event with multiple buttons is seen.
    # To check if this button supports button_number, we can inspect its binary sensor entity.
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_device(entity_registry, device_id)
    has_multiple_buttons = False

    for entry in entities:
        if entry.domain == "binary_sensor":
            state = hass.states.get(entry.entity_id)
            if state and state.attributes.get("button_number") is not None:
                has_multiple_buttons = True
                break

    if has_multiple_buttons:
        for trigger_type in TRIGGER_TYPES:
            for button_number in (0, 1):
                triggers.append(
                    {
                        CONF_PLATFORM: "device",
                        CONF_DOMAIN: DOMAIN,
                        CONF_DEVICE_ID: device_id,
                        CONF_TYPE: f"{trigger_type}_button_{button_number}",
                    }
                )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: dict,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    config = TRIGGER_SCHEMA(config)
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(config[CONF_DEVICE_ID])

    if device is None:
        raise ValueError(f"Device {config[CONF_DEVICE_ID]} not found")

    # Find the serial number from identifiers
    serial_number = next(
        (
            identifier[1]
            for identifier in device.identifiers
            if identifier[0] == DOMAIN
        ),
        None,
    )

    if not serial_number:
        raise ValueError(f"Device {config[CONF_DEVICE_ID]} is missing serial number")

    trigger_type_config = config[CONF_TYPE]

    match = re.match(r"^(single|double|hold|down|up|double_hold)(?:_button_(\d+))?$", trigger_type_config)
    if not match:
        raise ValueError(f"Invalid trigger type {trigger_type_config}")

    trigger_type = match.group(1)
    button_number_str = match.group(2)

    event_data = {
        EVENT_DATA_SERIAL_NUMBER: serial_number,
        EVENT_DATA_CLICK_TYPE: trigger_type,
    }

    if button_number_str is not None:
        event_data[EVENT_DATA_BUTTON_NUMBER] = int(button_number_str)

    # Listen for the corresponding EVENT_CLICK
    event_config = event_trigger.TRIGGER_SCHEMA({
        event_trigger.CONF_PLATFORM: "event",
        event_trigger.CONF_EVENT_TYPE: EVENT_CLICK,
        event_trigger.CONF_EVENT_DATA: event_data,
    })

    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )
