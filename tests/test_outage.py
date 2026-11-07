"""Tests for how the integration behaves when the Flic Hub stops answering."""
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pyflichub.button import FlicButton

from custom_components.flichub.const import DATA_BUTTONS, DOMAIN

SERIAL = "button_serial_123"


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


def _hub_info() -> MagicMock:
    hub_info = MagicMock()
    hub_info.has_wifi.return_value = True
    hub_info.wifi.ip = "192.168.1.64"
    hub_info.wifi.mac = "11:22:33:44:55:66"
    hub_info.has_ethernet.return_value = False
    return hub_info


@pytest.fixture
def mock_client():
    with patch("custom_components.flichub.FlicHubTcpClient") as mock_client_class:
        client = mock_client_class.return_value
        client.get_server_info = AsyncMock()
        client.get_buttons = AsyncMock(return_value=[_button()])
        client.get_hubinfo = AsyncMock(return_value=_hub_info())
        client.disconnect = MagicMock()

        async def connect(*args, **kwargs):
            await client.async_on_connected()

        client.async_connect = AsyncMock(side_effect=connect)
        yield client


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Flic Hub",
        data={"ip_address": "192.168.1.64", "port": "8124"},
    )
    entry.add_to_hass(hass)
    return entry


async def test_setup_retries_and_disconnects_when_hub_does_not_answer(
    hass: HomeAssistant, mock_client, config_entry
):
    """A first refresh with no hub info puts the entry in retry and closes the client."""
    mock_client.get_hubinfo.return_value = None

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    mock_client.disconnect.assert_called()


async def test_outage_marks_entities_unavailable_then_recovers(
    hass: HomeAssistant, mock_client, config_entry, caplog
):
    """A hub timeout makes button entities unavailable without errors, then they recover."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    coordinator = hass.data[DOMAIN][config_entry.entry_id].coordinator
    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, config_entry.entry_id)
    # The battery timestamp sensor is deliberately always available while the button is known.
    watched = [e.entity_id for e in entities if not e.unique_id.endswith("-battery-timestamp")]
    assert watched
    assert all(hass.states.get(entity_id).state != STATE_UNAVAILABLE for entity_id in watched if hass.states.get(entity_id))

    # Hub stops answering: hub info times out (None) and buttons come back empty.
    mock_client.get_hubinfo.return_value = None
    mock_client.get_buttons.return_value = []
    caplog.clear()
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is False
    # Last known data is kept, so entities do not look up a missing button.
    assert SERIAL in coordinator.data[DATA_BUTTONS]
    for entity_id in watched:
        state = hass.states.get(entity_id)
        if state is not None:
            assert state.state == STATE_UNAVAILABLE, entity_id
    assert "KeyError" not in caplog.text
    errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(errors) == 1
    assert "Error fetching" in errors[0].getMessage()

    # A second failed poll does not log the outage again.
    caplog.clear()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert "Error fetching" not in caplog.text

    # Hub answers again.
    mock_client.get_hubinfo.return_value = _hub_info()
    mock_client.get_buttons.return_value = [_button()]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is True
    assert "recovered" in caplog.text
    for entity_id in watched:
        state = hass.states.get(entity_id)
        if state is not None:
            assert state.state != STATE_UNAVAILABLE, entity_id
