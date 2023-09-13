"""FlicHubEntity class"""
from homeassistant.helpers import entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from pyflichub.button import FlicButton

from .const import DOMAIN
from .const import NAME
from .const import VERSION


class FlicHubEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry, serial_number):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.serial_number = serial_number
        self.config_entry = config_entry

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.serial_number

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, NAME)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
        }

    @property
    def button(self) -> FlicButton:
        return self.coordinator.data[self.serial_number]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "integration": DOMAIN,
        }
