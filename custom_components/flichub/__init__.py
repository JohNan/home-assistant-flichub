"""
Custom integration to integrate Flic Hub with Home Assistant.

For more details about this integration, please refer to
https://github.com/JohNan/flichub
"""
import async_timeout
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from pyflichubclient.button import FlicButton
from pyflichubclient.client import FlicHubTcpClient
from pyflichubclient.event import Event
from .api import FlicHubApiClient
from .const import CONF_PASSWORD, CLIENT_READY_TIMEOUT, BINARY_SENSOR, UPDATE_TOPIC, EVENT_NAME, EVENT_DATA_NAME, \
    EVENT_DATA_ADDRESS, EVENT_DATA_TYPE
from .const import CONF_IP_ADDRESS
from .const import DOMAIN
from .const import PLATFORMS
from .const import STARTUP_MESSAGE
from ...helpers.dispatcher import dispatcher_send

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    client = FlicHubTcpClient('192.168.1.249', 8124)
    client_ready = asyncio.Event()

    def client_connected():
        _LOGGER.debug("Connected!")
        client_ready.set()

    def client_disconnected():
        _LOGGER.debug("Disconnected!")

    def on_button_clicked(button: FlicButton, event: Event):
        dispatcher_send(hass, UPDATE_TOPIC, button, event)
        _send_event(hass, button, event)

    client.on_connected = client_connected
    client.on_disconnected = client_disconnected
    client.on_button_clicked = on_button_clicked

    asyncio.create_task(client.async_connect())

    try:
        with async_timeout.timeout(CLIENT_READY_TIMEOUT):
            await client_ready.wait()
    except asyncio.TimeoutError:
        print(f"Client not connected after {CLIENT_READY_TIMEOUT} secs so continuing with setup")
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = client
    hass.config_entries.async_setup_platforms(entry, [BINARY_SENSOR])

    entry.add_update_listener(async_reload_entry)
    return True


def _send_event(hass: HomeAssistant, button: FlicButton, event: Event):
    hass.bus.fire(
        EVENT_NAME,
        {
            EVENT_DATA_NAME: button.name,
            EVENT_DATA_ADDRESS: button.bdaddr,
            EVENT_DATA_TYPE: event.action,
        },
    )

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
