"""
Custom integration to integrate Flic Hub with Home Assistant.

For more details about this integration, please refer to
https://github.com/JohNan/flichub
"""
import async_timeout
import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyflichub.button import FlicButton
from pyflichub.client import FlicHubTcpClient
from pyflichub.command import Command
from pyflichub.event import Event
from .const import CLIENT_READY_TIMEOUT, EVENT_CLICK, EVENT_DATA_NAME, EVENT_DATA_CLICK_TYPE, \
    EVENT_DATA_SERIAL_NUMBER, DATA_BUTTONS, DATA_HUB
from .const import DOMAIN
from .const import PLATFORMS

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


@dataclass
class FlicHubEntryData:
    """Class for sharing data within the Nanoleaf integration."""

    client: FlicHubTcpClient
    coordinator: DataUpdateCoordinator[None]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    def on_event(button: FlicButton, event: Event):
        hass.bus.fire(EVENT_CLICK, {
            EVENT_DATA_SERIAL_NUMBER: button.serial_number,
            EVENT_DATA_NAME: button.name,
            EVENT_DATA_CLICK_TYPE: event.action
        })

    def on_commend(command: Command):
        _LOGGER.debug(f"Command: {command.data}")
        if command.command == "buttons":
            coordinator.async_set_updated_data(
                {
                    DATA_BUTTONS: {button.serial_number: button for button in command.data},
                    DATA_HUB: coordinator.data.get(DATA_HUB, None) if coordinator.data else None
                }
            )
        if command.command == "network":
            coordinator.async_set_updated_data(
                {
                    DATA_BUTTONS: coordinator.data.get(DATA_BUTTONS, None) if coordinator.data else {},
                    DATA_HUB: command.data
                }
            )

    client = FlicHubTcpClient(
        ip=entry.data[CONF_IP_ADDRESS],
        port=entry.data[CONF_PORT],
        loop=asyncio.get_event_loop(),
        event_callback=on_event,
        command_callback=on_commend
    )
    client_ready = asyncio.Event()

    async def async_get_buttons() -> [FlicButton]:
        buttons = await client.get_buttons()
        hub_info = await client.get_hubinfo()
        return {
            DATA_BUTTONS: {button.serial_number: button for button in buttons},
            DATA_HUB: hub_info
        }

    def client_connected():
        _LOGGER.debug("Connected!")
        client_ready.set()

    def client_disconnected():
        _LOGGER.debug("Disconnected!")

    client.on_connected = client_connected
    client.on_disconnected = client_disconnected

    asyncio.create_task(client.async_connect())

    def stop_client(event):
        client.disconnect()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_client)

    try:
        with async_timeout.timeout(CLIENT_READY_TIMEOUT):
            await client_ready.wait()
    except asyncio.TimeoutError:
        print(f"Client not connected after {CLIENT_READY_TIMEOUT} secs so continuing with setup")
        raise ConfigEntryNotReady

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=entry.title,
        update_method=async_get_buttons
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = FlicHubEntryData(
        client=client,
        coordinator=coordinator
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    hass.data[DOMAIN][entry.entry_id].client.disconnect()
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
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
