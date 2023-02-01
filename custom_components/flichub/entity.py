"""FlicHubEntity class"""
from homeassistant.helpers import entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .const import DOMAIN
from .const import NAME
from .const import VERSION


class FlicHubEntity(entity.Entity):
    def __init__(self, client, config_entry, serial_number):
        self.serial_number = serial_number
        self.client = client
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
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            "integration": DOMAIN,
        }
