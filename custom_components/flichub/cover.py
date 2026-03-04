"""Cover platform for Flic Hub Virtual Devices."""
import logging
from typing import Any

from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from pyflichub.flichub import FlicHubInfo

from . import FlicHubEntryData
from .const import DOMAIN, DATA_BUTTONS, DATA_HUB, DATA_VIRTUAL_DEVICES
from .const import EVENT_VIRTUAL_DEVICE_UPDATE, EVENT_DATA_META_DATA, EVENT_DATA_VALUES
from .entity import FlicHubButtonEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Set up the cover platform."""
    data_entry: FlicHubEntryData = hass.data[DOMAIN][entry.entry_id]
    flic_hub = data_entry.coordinator.data[DATA_HUB]

    # Add existing virtual devices
    virtual_devices = entry.data.get(DATA_VIRTUAL_DEVICES, [])
    devices = []
    for device_info in virtual_devices:
        if device_info.get("dimmable_type") == "Blind":
            button_id = device_info.get("button_id")
            virtual_device_id = device_info.get("virtual_device_id")
            if button_id in data_entry.coordinator.data[DATA_BUTTONS]:
                devices.append(
                    FlicHubVirtualBlind(
                        hass,
                        data_entry.coordinator,
                        entry,
                        button_id,
                        virtual_device_id,
                        flic_hub
                    )
                )

    if devices:
        async_add_devices(devices)

    def async_add_virtual_device(device_info):
        """Add virtual device dynamically."""
        if device_info.get("dimmable_type") == "Blind":
            button_id = device_info.get("button_id")
            virtual_device_id = device_info.get("virtual_device_id")
            if button_id in data_entry.coordinator.data[DATA_BUTTONS]:
                async_add_devices([
                    FlicHubVirtualBlind(
                        hass,
                        data_entry.coordinator,
                        entry,
                        button_id,
                        virtual_device_id,
                        flic_hub
                    )
                ])

    entry.async_on_unload(
        async_dispatcher_connect(hass, f"{DOMAIN}_{entry.entry_id}_add_virtual_device", async_add_virtual_device)
    )


class FlicHubVirtualBlind(FlicHubButtonEntity, CoverEntity):
    """Flic Hub Virtual Blind class."""

    _attr_has_entity_name = True
    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = CoverEntityFeature.SET_POSITION

    def __init__(self, hass: HomeAssistant, coordinator, config_entry, serial_number: str, virtual_device_id: str, flic_hub: FlicHubInfo):
        """Initialize the virtual cover."""
        super().__init__(coordinator, config_entry, serial_number, flic_hub)
        self._virtual_device_id = virtual_device_id

        # Entity attributes
        self._attr_unique_id = f"{self.serial_number}-{virtual_device_id}"
        self._attr_name = virtual_device_id

        # State
        self._position = 100 # Default open

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_VIRTUAL_DEVICE_UPDATE, self._event_callback)
        )

    def _event_callback(self, event: Event):
        """Handle virtual device update event."""
        meta_data = event.data.get(EVENT_DATA_META_DATA, {})
        button_id = meta_data.get("button_id")
        virtual_device_id = meta_data.get("virtual_device_id")

        if button_id != self.serial_number or virtual_device_id != self._virtual_device_id:
            return

        values = event.data.get(EVENT_DATA_VALUES, {})

        # The values themselves are always floating point numbers between 0 and 1
        # Extract and convert values
        if "position" in values:
            self._position = int(values["position"] * 100)

        self.schedule_update_ha_state()

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover. None is unknown, 0 is closed, 100 is fully open."""
        return self._position

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        if self._position is None:
            return None
        return self._position == 0

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get("position", 100)
        client = self.coordinator.hass.data[DOMAIN][self.config_entry.entry_id].client
        values = {"position": position / 100.0}
        self._position = position
        client.send_virtual_device_update_state("Blind", self._virtual_device_id, values)
        self.async_write_ha_state()