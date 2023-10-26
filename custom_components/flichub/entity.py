"""FlicHubEntity class"""
from typing import Mapping, Any

from homeassistant.const import CONF_IP_ADDRESS

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, CONNECTION_NETWORK_MAC, format_mac

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from pyflichub.button import FlicButton
from pyflichub.flichub import FlicHubInfo

from .const import DOMAIN, DATA_BUTTONS, DATA_HUB


class FlicHubButtonEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, config_entry, serial_number, flic_hub: FlicHubInfo):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.serial_number = serial_number
        self.config_entry = config_entry
        self.flic_hub = flic_hub

    @property
    def hub_mac_address(self):
        """Return a unique ID to use for this entity."""
        if self.flic_hub.has_ethernet():
            return format_mac(self.flic_hub.ethernet.mac)
        if self.flic_hub.has_wifi():
            return format_mac(self.flic_hub.wifi.mac)

    @property
    def mac_address(self):
        return format_mac(self.button.bdaddr)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.serial_number)},
            "name": self.button.name,
            "model": self.button.flic_version,
            "connections": {(CONNECTION_BLUETOOTH, self.mac_address)},
            "sw_version": self.button.firmware_version,
            "hw_version": self.button.flic_version,
            "manufacturer": "Flic",
            "via_device": (DOMAIN, self.hub_mac_address)
        }

    @property
    def button(self) -> FlicButton:
        return self.coordinator.data[DATA_BUTTONS][self.serial_number]

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes."""
        return {
            "color": self.button.color,
            "bluetooth_address": self.button.bdaddr,
            "serial_number": self.button.serial_number,
            "integration": DOMAIN,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.button.connected


class FlicHubEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, config_entry, flic_hub: FlicHubInfo):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._flic_hub = flic_hub
        self._ip_address = config_entry.data[CONF_IP_ADDRESS]
        self.config_entry = config_entry

    @property
    def mac_address(self):
        """Return a unique ID to use for this entity."""
        if self.flic_hub.has_ethernet() and self._ip_address == self.flic_hub.ethernet.ip:
            return format_mac(self.flic_hub.ethernet.mac)
        if self.flic_hub.has_wifi() and self._ip_address == self.flic_hub.wifi.ip:
            return format_mac(self.flic_hub.wifi.mac)

    @property
    def device_info(self):
        identifiers = set()
        connections = set()

        if self.flic_hub.has_ethernet() and self._ip_address == self.flic_hub.ethernet.ip:
            identifiers.add((DOMAIN, format_mac(self.flic_hub.ethernet.mac)))
            connections.add((DOMAIN, format_mac(self.flic_hub.ethernet.mac)))
        if self.flic_hub.has_wifi() and self._ip_address == self.flic_hub.wifi.ip:
            identifiers.add((DOMAIN, format_mac(self.flic_hub.wifi.mac)))
            connections.add((DOMAIN, format_mac(self.flic_hub.wifi.mac)))

        return {
            "identifiers": identifiers,
            "name": "FlicHub",
            "model": "LR",
            "connections": connections,
            "manufacturer": "Flic"
        }

    @property
    def flic_hub(self) -> FlicHubInfo:
        if DATA_HUB not in self.coordinator.data:
            return self._flic_hub
        else:
            return self.coordinator.data[DATA_HUB]
