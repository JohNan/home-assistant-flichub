from unittest.mock import MagicMock
from custom_components.flichub.entity import FlicHubButtonEntity
from custom_components.flichub.const import DOMAIN, DATA_BUTTONS
from pyflichub.button import FlicButton

def create_mock_button(firmware_version, flic_version=2):
    return FlicButton(
        bdaddr="AA:BB:CC:DD:EE:FF",
        serial_number="button_serial_123",
        color="black",
        name="Test Button",
        active_disconnect=False,
        connected=True,
        ready=True,
        battery_status=100,
        uuid="uuid-1234",
        flic_version=flic_version,
        firmware_version=firmware_version,
        key="key123",
        passive_mode=False
    )

def test_flichub_button_entity_device_info_sw_version_int():
    button = create_mock_button(firmware_version=3)
    coordinator = MagicMock()
    coordinator.data = {DATA_BUTTONS: {"button_serial_123": button}}
    flic_hub = MagicMock()
    flic_hub.has_ethernet.return_value = False
    flic_hub.has_wifi.return_value = True
    flic_hub.wifi.mac = "11:22:33:44:55:66"

    entity = FlicHubButtonEntity(
        coordinator=coordinator,
        config_entry=MagicMock(),
        serial_number="button_serial_123",
        flic_hub=flic_hub
    )

    device_info = entity.device_info
    assert device_info["sw_version"] == "3"
    assert isinstance(device_info["sw_version"], str)
    assert device_info["hw_version"] == "2"
    assert device_info["model"] == "2"

def test_flichub_button_entity_device_info_sw_version_none():
    button = create_mock_button(firmware_version=None, flic_version=None)
    coordinator = MagicMock()
    coordinator.data = {DATA_BUTTONS: {"button_serial_123": button}}
    flic_hub = MagicMock()
    flic_hub.has_ethernet.return_value = False
    flic_hub.has_wifi.return_value = True
    flic_hub.wifi.mac = "11:22:33:44:55:66"

    entity = FlicHubButtonEntity(
        coordinator=coordinator,
        config_entry=MagicMock(),
        serial_number="button_serial_123",
        flic_hub=flic_hub
    )

    device_info = entity.device_info
    assert device_info["sw_version"] is None
    assert device_info["hw_version"] is None
    assert device_info["model"] is None
