"""Binary sensor platform for Flic Hub."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, ENTITY_ID_FORMAT
from pyflichub.button import FlicButton
from pyflichub.event import Event

from .const import BINARY_SENSOR, UPDATE_TOPIC
from .const import BINARY_SENSOR_DEVICE_CLASS
from .const import DEFAULT_NAME
from .const import DOMAIN
from .entity import FlicHubEntity
from homeassistant.const import PERCENTAGE
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup binary_sensor platform."""
    client = hass.data[DOMAIN][entry.entry_id]
    buttons = await client.get_buttons()
    for button in buttons:
        async_add_devices([FlicHubBinarySensor(client, entry, button)])


class FlicHubBinarySensor(FlicHubEntity, BinarySensorEntity):
    """flichub binary_sensor class."""

    def __init__(self, client, config_entry, button: FlicButton):
        super().__init__(client, config_entry, button.serial_number)
        self.button = button
        self.entity_id = ENTITY_ID_FORMAT.format(f"{DEFAULT_NAME}_{self.button.name}")
        self._is_on = False
        self._click_type = None

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        return self.button.name

    @property
    def icon(self):
        """Return the icon."""
        return 'mdi:hockey-puck'

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.button.connected

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self._is_on

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "click_type": self._click_type,
            "firmware": self.button.firmware_version,
            "flic_version": self.button.flic_version,
            "color": self.button.color,
            "bluetooth_address": self.button.bdaddr,
            "serial_number": self.button.serial_number,
            "battery_status": f"{self.button.battery_status}{PERCENTAGE}",
            "integration": DOMAIN,
        }

    @callback
    async def _async_update_callback(self, button: FlicButton, event: Event):
        """Update the entity."""
        _LOGGER.debug(f"Button {button.name} clicked: {event.action}")
        if self.serial_number == button.serial_number:
            self._is_on = event.action == 'down'
            self._click_type = event.action
            self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(
            self.hass, UPDATE_TOPIC, self._async_update_callback
        )
