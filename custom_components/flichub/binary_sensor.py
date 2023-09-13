"""Binary sensor platform for Flic Hub."""
import logging

from homeassistant import core
from homeassistant.components.binary_sensor import BinarySensorEntity, ENTITY_ID_FORMAT
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from pyflichub.button import FlicButton
from pyflichub.event import Event
from . import FlicHubEntryData
from .const import DEFAULT_NAME, EVENT_CLICK, EVENT_DATA_CLICK_TYPE, \
    EVENT_DATA_SERIAL_NUMBER, EVENT_DATA_NAME
from .const import DOMAIN
from .entity import FlicHubEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup binary_sensor platform."""
    data_entry: FlicHubEntryData = hass.data[DOMAIN][entry.entry_id]
    buttons = await data_entry.client.get_buttons()
    for button in buttons:
        async_add_devices([FlicHubBinarySensor(hass, data_entry.coordinator, entry, button)])


class FlicHubBinarySensor(FlicHubEntity, BinarySensorEntity):
    """flichub binary_sensor class."""

    def __init__(self, hass: HomeAssistant, coordinator, config_entry, button: FlicButton):
        super().__init__(coordinator, config_entry, button.serial_number)
        self.entity_id = ENTITY_ID_FORMAT.format(f"{DEFAULT_NAME}_{self.button.name}")
        self._is_on = False
        self._click_type = None
        hass.bus.async_listen(EVENT_CLICK, self._event_callback)

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
    def extra_state_attributes(self):
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

    def _event_callback(self, event: core.Event):
        serial_number = event.data[EVENT_DATA_SERIAL_NUMBER]
        name = event.data[EVENT_DATA_NAME]
        click_type: Event = event.data[EVENT_DATA_CLICK_TYPE]
        """Update the entity."""
        _LOGGER.debug(f"Button {name} clicked: {click_type}")
        if self.serial_number == serial_number:
            if click_type == 'single':
                self._click_type = click_type
            elif click_type == 'double':
                self._click_type = click_type

            if click_type == 'down':
                self._is_on = True
            if click_type == 'hold':
                self._click_type = click_type
                self._is_on = True
            if click_type == 'up':
                self._is_on = False
            self.async_write_ha_state()
