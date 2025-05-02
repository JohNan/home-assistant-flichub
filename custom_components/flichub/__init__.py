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
from homeassistant.helpers.issue_registry import async_create_issue, IssueSeverity

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyflichub.button import FlicButton
from pyflichub.client import FlicHubTcpClient, ServerCommand
from pyflichub.command import Command
from pyflichub.event import Event
from .const import CLIENT_READY_TIMEOUT, EVENT_CLICK, EVENT_DATA_NAME, EVENT_DATA_CLICK_TYPE, \
    EVENT_DATA_SERIAL_NUMBER, DATA_BUTTONS, DATA_HUB, REQUIRED_SERVER_VERSION, DEFAULT_SCAN_INTERVAL
from .const import DOMAIN
from .const import PLATFORMS

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


@dataclass
class FlicHubEntryData:
    """Class for sharing data within the Nanoleaf integration."""

    client: FlicHubTcpClient
    coordinator: DataUpdateCoordinator[dict]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    def on_event(button: FlicButton, event: Event):
        _LOGGER.debug(f"Event: {event}")
        if event.event == "button":
            hass.bus.fire(EVENT_CLICK, {
                EVENT_DATA_SERIAL_NUMBER: button.serial_number,
                EVENT_DATA_NAME: button.name,
                EVENT_DATA_CLICK_TYPE: event.action
            })
        if event.event == "buttonReady":
            hass.async_create_task(coordinator.async_refresh())

    def on_command(command: Command):
        _LOGGER.debug(f"Command: {command.command}, data: {command.data}")
        if command is None:
            return
        if command.command == ServerCommand.SERVER_INFO:
            hub_version = command.data.version
            if hub_version != REQUIRED_SERVER_VERSION:
                async_create_issue(
                    hass,
                    DOMAIN,
                    f"invalid_server_version_{entry.entry_id}",
                    is_fixable=False,
                    severity=IssueSeverity.ERROR,
                    translation_key=f"{DOMAIN}_invalid_server_version",
                    translation_placeholders={
                        "required_version": REQUIRED_SERVER_VERSION,
                        "flichub_version": hub_version,
                    },
                )
        if command.command == ServerCommand.BUTTONS:
            coordinator.async_set_updated_data(
                {
                    DATA_BUTTONS: {button.serial_number: button for button in command.data},
                    DATA_HUB: coordinator.data.get(DATA_HUB, None) if coordinator.data else None
                }
            )

    client = FlicHubTcpClient(
        ip=entry.data[CONF_IP_ADDRESS],
        port=entry.data[CONF_PORT],
        loop=asyncio.get_event_loop(),
        event_callback=on_event,
        command_callback=on_command
    )
    client_ready = asyncio.Event()

    async def async_update() -> dict:
        buttons = await client.get_buttons()
        hub_info = await client.get_hubinfo()
        return {
            DATA_BUTTONS: {button.serial_number: button for button in buttons} if buttons is not None else {},
            DATA_HUB: hub_info if hub_info is not None else {}
        }

    async def client_connected():
        _LOGGER.debug("Connected!")
        client_ready.set()
        await client.get_server_info()

    async def client_disconnected():
        _LOGGER.debug("Disconnected!")

    def stop_client(event):
        client.disconnect()

    client.async_on_connected = client_connected
    client.async_on_disconnected = client_disconnected

    await client.async_connect()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_client)

    try:
        async with async_timeout.timeout(CLIENT_READY_TIMEOUT):
            await client_ready.wait()
    except asyncio.TimeoutError:
        _LOGGER.error(f"Client not connected after {CLIENT_READY_TIMEOUT} secs. Discontinuing setup")
        client.disconnect()
        raise ConfigEntryNotReady

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=entry.title,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        update_method=async_update
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
