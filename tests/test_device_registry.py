"""Tests for device registry usage."""
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import format_mac
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pyflichub.button import FlicButton

from custom_components.flichub.const import DOMAIN

SERIAL = "button_serial_123"
HUB_MAC = "11:22:33:44:55:66"


def _button() -> FlicButton:
    return FlicButton(
        bdaddr="AA:BB:CC:DD:EE:FF",
        serial_number=SERIAL,
        color="black",
        name="Test Button",
        active_disconnect=False,
        connected=True,
        ready=True,
        battery_status=100,
        uuid="uuid-1234",
        flic_version=2,
        firmware_version=3,
        key="key123",
        passive_mode=False,
    )


async def test_button_device_is_linked_to_hub_without_deprecations(hass: HomeAssistant, caplog):
    """Button devices point at the hub through via_device_id and no deprecated API is used."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Flic Hub",
        data={"ip_address": "192.168.1.64", "port": "8124"},
    )
    entry.add_to_hass(hass)

    with patch("custom_components.flichub.FlicHubTcpClient") as mock_client_class:
        client = mock_client_class.return_value
        client.get_server_info = AsyncMock()
        client.get_buttons = AsyncMock(return_value=[_button()])
        hub_info = MagicMock()
        hub_info.has_wifi.return_value = True
        hub_info.wifi.ip = "192.168.1.64"
        hub_info.wifi.mac = HUB_MAC
        hub_info.has_ethernet.return_value = False
        client.get_hubinfo = AsyncMock(return_value=hub_info)
        client.disconnect = MagicMock()

        async def connect(*args, **kwargs):
            await client.async_on_connected()

        client.async_connect = AsyncMock(side_effect=connect)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED

    registry = dr.async_get(hass)
    hub = registry.async_get_device_by_identifier((DOMAIN, format_mac(HUB_MAC)), entry.entry_id)
    button = registry.async_get_device_by_identifier((DOMAIN, SERIAL), entry.entry_id)
    assert hub is not None
    assert button is not None
    assert button.via_device_id == hub.id

    assert "deprecated" not in caplog.text
    assert "via_device" not in caplog.text
