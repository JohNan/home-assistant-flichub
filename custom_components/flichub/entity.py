"""FlicHubEntity class"""
from typing import Mapping, Any

from homeassistant.const import CONF_IP_ADDRESS

from homeassistant.helpers import device_registry as dr
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
        info = {
            "identifiers": {(DOMAIN, self.serial_number)},
            "name": self.button.name,
            "model": str(self.button.flic_version) if self.button.flic_version is not None else None,
            "connections": {(CONNECTION_BLUETOOTH, self.mac_address)},
            "sw_version": str(self.button.firmware_version) if self.button.firmware_version is not None else None,
            "hw_version": str(self.button.flic_version) if self.button.flic_version is not None else None,
            "manufacturer": "Flic",
        }
        if (hub_device_id := self._hub_device_id()) is not None:
            info["via_device_id"] = hub_device_id
        return info

    def _hub_device_id(self) -> str | None:
        """Return the device registry id of the Flic Hub, if it is registered."""
        hub_mac_address = self.hub_mac_address
        if self.hass is None or hub_mac_address is None:
            return None
        hub_device = dr.async_get(self.hass).async_get_device_by_identifier(
            (DOMAIN, hub_mac_address), self.config_entry.entry_id
        )
        return hub_device.id if hub_device else None

    @property
    def button(self) -> FlicButton | None:
        """Return the button from coordinator data, or None if the hub did not report it."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(DATA_BUTTONS, {}).get(self.serial_number)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes."""
        button = self.button
        if button is None:
            return None
        return {
            "color": button.color,
            "bluetooth_address": button.bdaddr,
            "serial_number": button.serial_number,
            "integration": DOMAIN,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        button = self.button
        return super().available and button is not None and button.connected


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
    def flic_hub(self) -> FlicHubInfo:
        if DATA_HUB not in self.coordinator.data:
            return self._flic_hub
        else:
            return self.coordinator.data[DATA_HUB]
