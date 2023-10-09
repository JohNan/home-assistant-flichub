"""Binary sensor platform for Flic Hub."""

import logging

from homeassistant import core
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from pyflichub.button import FlicButton
from pyflichub.event import Event
from pyflichub.flichub import FlicHubInfo
from . import FlicHubEntryData
from .const import DOMAIN
from .const import EVENT_CLICK, EVENT_DATA_CLICK_TYPE, \
    EVENT_DATA_SERIAL_NUMBER, EVENT_DATA_NAME, DATA_BUTTONS, DATA_HUB
from .entity import FlicHubButtonEntity, FlicHubEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup binary_sensor platform."""
    data_entry: FlicHubEntryData = hass.data[DOMAIN][entry.entry_id]
    buttons = data_entry.coordinator.data[DATA_BUTTONS]
    flic_hub = data_entry.coordinator.data[DATA_HUB]
    devices = []
    for serial_number, button in buttons.items():
        devices.extend([
            FlicHubButtonBinarySensor(hass, data_entry.coordinator, entry, button, flic_hub),
            FlicHubButtonPassiveBinarySensor(data_entry.coordinator, entry, button, flic_hub),
            FlicHubButtonActiveDisconnectBinarySensor(data_entry.coordinator, entry, button, flic_hub),
            FlicHubButtonConnectedBinarySensor(data_entry.coordinator, entry, button, flic_hub),
            FlicHubButtonReadyBinarySensor(data_entry.coordinator, entry, button, flic_hub)
        ])
    devices.extend([
        FlicHubWifiBinarySensor(data_entry.coordinator, entry, flic_hub),
        FlicHubEthernetBinarySensor(data_entry.coordinator, entry, flic_hub),
    ])
    async_add_devices(devices)


class FlicHubWifiBinarySensor(FlicHubEntity, BinarySensorEntity):
    """flichub sensor class."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:wifi"
    _attr_name = "Wifi"

    def __init__(self, coordinator, config_entry, flic_hub: FlicHubInfo):
        super().__init__(coordinator, config_entry, flic_hub)
        self._attr_entity_registry_enabled_default = self.flic_hub.has_wifi()
        self._attr_unique_id = f"{self.mac_address}-wifi"

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self.flic_hub.wifi.connected if self.flic_hub.has_wifi() else False

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "mac_address": self.flic_hub.wifi.mac,
            "ip_address": self.flic_hub.wifi.ip,
            "state": self.flic_hub.wifi.state,
            "ssid": self.flic_hub.wifi.ssid
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.flic_hub.has_wifi()


class FlicHubEthernetBinarySensor(FlicHubEntity, BinarySensorEntity):
    """flichub sensor class."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:ethernet"
    _attr_name = "Ethernet"

    def __init__(self, coordinator, config_entry, flic_hub: FlicHubInfo):
        super().__init__(coordinator, config_entry, flic_hub)
        self._attr_entity_registry_enabled_default = self.flic_hub.has_ethernet()
        self._attr_unique_id = f"{self.mac_address}-ethernet"

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self.flic_hub.ethernet.connected if self.flic_hub.has_ethernet() else False

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "mac": self.flic_hub.ethernet.mac,
            "ip": self.flic_hub.ethernet.ip
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.flic_hub.has_ethernet()


class FlicHubButtonReadyBinarySensor(FlicHubButtonEntity, BinarySensorEntity):
    """flichub sensor class."""
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Ready"

    def __init__(self, coordinator, config_entry, button: FlicButton, flic_hub: FlicHubInfo):
        super().__init__(coordinator, config_entry, button.serial_number, flic_hub)
        self._attr_unique_id = f"{self.mac_address}-ready"

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return not self.button.ready


class FlicHubButtonConnectedBinarySensor(FlicHubButtonEntity, BinarySensorEntity):
    """flichub sensor class."""
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Connection"

    def __init__(self, coordinator, config_entry, button: FlicButton, flic_hub: FlicHubInfo):
        super().__init__(coordinator, config_entry, button.serial_number, flic_hub)
        self._attr_unique_id = f"{self.mac_address}-connected"

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self.button.connected


class FlicHubButtonPassiveBinarySensor(FlicHubButtonEntity, BinarySensorEntity):
    """flichub sensor class."""
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Passive Mode"

    def __init__(self, coordinator, config_entry, button: FlicButton, flic_hub: FlicHubInfo):
        super().__init__(coordinator, config_entry, button.serial_number, flic_hub)
        self._attr_unique_id = f"{self.mac_address}-passive_mode"

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self.button.passive_mode


class FlicHubButtonActiveDisconnectBinarySensor(FlicHubButtonEntity, BinarySensorEntity):
    """flichub sensor class."""
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Active Disconnect"

    def __init__(self, coordinator, config_entry, button: FlicButton, flic_hub: FlicHubInfo):
        super().__init__(coordinator, config_entry, button.serial_number, flic_hub)
        self._attr_unique_id = f"{self.mac_address}-active_disconnect"

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self.button.active_disconnect


class FlicHubButtonBinarySensor(FlicHubButtonEntity, BinarySensorEntity):
    """flichub binary_sensor class."""
    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:hockey-puck"

    def __init__(self, hass: HomeAssistant, coordinator, config_entry, button: FlicButton, flic_hub: FlicHubInfo):
        super().__init__(coordinator, config_entry, button.serial_number, flic_hub)
        self._attr_unique_id = f"{self.serial_number}-button"
        self._is_on = False
        self._click_type = None
        hass.bus.async_listen(EVENT_CLICK, self._event_callback)

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self._is_on

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = {"click_type": self._click_type}
        attrs.update(super().extra_state_attributes)
        return attrs

    def _event_callback(self, event: core.Event):
        serial_number = event.data[EVENT_DATA_SERIAL_NUMBER]
        """Update the entity."""
        if self.serial_number != serial_number:
            return

        name = event.data[EVENT_DATA_NAME]
        click_type: Event = event.data[EVENT_DATA_CLICK_TYPE]
        _LOGGER.debug(f"Button {name} clicked: {click_type}")
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
