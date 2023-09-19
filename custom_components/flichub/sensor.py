"""Binary sensor platform for Flic Hub."""
import logging
from homeassistant.helpers.device_registry import format_mac

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.const import CONF_IP_ADDRESS, EntityCategory, CONF_NAME, PERCENTAGE

from homeassistant.components.binary_sensor import ENTITY_ID_FORMAT
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from pyflichub.button import FlicButton
from pyflichub.flichub import FlicHubInfo
from . import FlicHubEntryData
from .const import DEFAULT_NAME, DATA_BUTTONS, DATA_HUB
from .const import DOMAIN
from .entity import FlicHubButtonEntity, FlicHubEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup binary_sensor platform."""
    data_entry: FlicHubEntryData = hass.data[DOMAIN][entry.entry_id]
    buttons = data_entry.coordinator.data[DATA_BUTTONS]
    flic_hub = data_entry.coordinator.data[DATA_HUB]
    devices = []
    for serial_number, button in buttons.items():
        devices.append(FlicHubButtonBatterySensor(data_entry.coordinator, entry, button, flic_hub))
    async_add_devices(devices)


class FlicHubButtonBatterySensor(FlicHubButtonEntity, SensorEntity):
    """flichub binary_sensor class."""
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config_entry, button: FlicButton, flic_hub: FlicHubInfo):
        super().__init__(coordinator, config_entry, button.serial_number, flic_hub)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.button.battery_status

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.serial_number}-battery"
