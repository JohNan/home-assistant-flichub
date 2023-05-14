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
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from pyflichub.button import FlicButton
from pyflichub.client import FlicHubTcpClient
from pyflichub.command import Command
from pyflichub.event import Event
from .api import FlicHubApiClient
from .const import CONF_PASSWORD, CLIENT_READY_TIMEOUT, BINARY_SENSOR, EVENT_TOPIC, EVENT_NAME, EVENT_DATA_NAME, \
    EVENT_DATA_ADDRESS, EVENT_DATA_TYPE, STATUS_TOPIC
from .const import DOMAIN
from .const import PLATFORMS
from .const import STARTUP_MESSAGE

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    def on_event(button: FlicButton, event: Event):
        dispatcher_send(hass, EVENT_TOPIC, button, event)
        _send_event(hass, button, event)

    def on_commend(command: Command):
        _LOGGER.debug(f"Command: {command.data}")
        if command.command == "buttons":
            for button in command.data:
                dispatcher_send(hass, STATUS_TOPIC, button)


    client = FlicHubTcpClient(
        ip=entry.data[CONF_IP_ADDRESS],
        port=entry.data[CONF_PORT],
        loop=asyncio.get_event_loop(),
        event_callback=on_event,
        command_callback=on_commend
    )
    client_ready = asyncio.Event()

    def client_connected():
        _LOGGER.debug("Connected!")
        client_ready.set()

    def client_disconnected():
        _LOGGER.debug("Disconnected!")

    client.on_connected = client_connected
    client.on_disconnected = client_disconnected

    asyncio.create_task(client.async_connect())

    try:
        with async_timeout.timeout(CLIENT_READY_TIMEOUT):
            await client_ready.wait()
    except asyncio.TimeoutError:
        print(f"Client not connected after {CLIENT_READY_TIMEOUT} secs so continuing with setup")
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = client
    await hass.config_entries.async_forward_entry_setups(entry, [BINARY_SENSOR])

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
