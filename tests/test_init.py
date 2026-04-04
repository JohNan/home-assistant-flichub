import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.flichub.const import DOMAIN, DATA_VIRTUAL_DEVICES
from pyflichub.event import Event

@pytest.fixture
def mock_flichub_client():
    with patch("custom_components.flichub.FlicHubTcpClient") as mock_client:
        client_instance = mock_client.return_value
        client_instance.get_server_info = AsyncMock()
        client_instance.get_buttons = AsyncMock(return_value=[])
        hub_info = MagicMock()
        hub_info.has_wifi.return_value = True
        hub_info.wifi.ip = "192.168.1.64"
        hub_info.wifi.mac = "11:22:33:44:55:66"
        hub_info.has_ethernet.return_value = False
        client_instance.get_hubinfo = AsyncMock(return_value=hub_info)
        client_instance.async_connect = AsyncMock()
        client_instance.disconnect = MagicMock()
        yield client_instance

async def test_virtual_device_update_does_not_reload(hass: HomeAssistant, mock_flichub_client):
    """Test that virtual device update does not reload the integration."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Flic Hub",
        data={"ip_address": "192.168.1.64", "port": "8124"},
    )
    config_entry.add_to_hass(hass)

    # Set up the integration
    with patch("custom_components.flichub.CLIENT_READY_TIMEOUT", 0.1):
        # We need to simulate the client ready event immediately to avoid waiting timeout
        async def mock_connect(*args, **kwargs):
            await mock_flichub_client.async_on_connected()
        mock_flichub_client.async_connect.side_effect = mock_connect

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.LOADED

    # Get the client instance to simulate an event
    data_entry = hass.data[DOMAIN][config_entry.entry_id]

    # Check that our update listener is set
    assert data_entry.unsub_update_listener is not None

    # Store old reload function reference to ensure it's not called
    with patch("custom_components.flichub.async_reload_entry") as mock_reload:
        # Simulate a virtualDeviceUpdate event
        event_data = {
            "event": "virtualDeviceUpdate",
            "meta_data": {
                "button_id": "90:88:a9:5b:12:89",
                "virtual_device_id": "Virtual Light",
                "dimmable_type": "Light"
            },
            "values": {
                "brightness": 0.91
            }
        }
        event = Event(event_data["event"])
        event.meta_data = event_data["meta_data"]
        event.values = event_data["values"]

        # Get the callback that was attached to the mocked client
        import sys
        flichub_client_mock_class = sys.modules['custom_components.flichub'].FlicHubTcpClient
        on_event = flichub_client_mock_class.call_args.kwargs.get("event_callback")

        on_event(None, event)
        await hass.async_block_till_done()

        # Config entry data should be updated with the virtual device
        assert DATA_VIRTUAL_DEVICES in config_entry.data
        assert len(config_entry.data[DATA_VIRTUAL_DEVICES]) == 1
        assert config_entry.data[DATA_VIRTUAL_DEVICES][0]["virtual_device_id"] == "Virtual Light"

        # The reload method should NOT have been called due to our fix
        mock_reload.assert_not_called()

        # Data entry listener should be re-subscribed
        assert data_entry.unsub_update_listener is not None
