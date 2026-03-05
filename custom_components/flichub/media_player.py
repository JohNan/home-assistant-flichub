"""Media Player platform for Flic Hub Virtual Devices."""
import logging
from typing import Any

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerDeviceClass, MediaPlayerEntityFeature, MediaPlayerState
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from pyflichub.flichub import FlicHubInfo

from . import FlicHubEntryData
from .const import DOMAIN, DATA_BUTTONS, DATA_HUB, DATA_VIRTUAL_DEVICES, get_button_by_id
from .const import EVENT_VIRTUAL_DEVICE_UPDATE, EVENT_DATA_META_DATA, EVENT_DATA_VALUES
from .entity import FlicHubButtonEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Set up the media player platform."""
    data_entry: FlicHubEntryData = hass.data[DOMAIN][entry.entry_id]
    flic_hub = data_entry.coordinator.data[DATA_HUB]

    # Add existing virtual devices
    virtual_devices = entry.data.get(DATA_VIRTUAL_DEVICES, [])
    devices = []
    for device_info in virtual_devices:
        if device_info.get("dimmable_type") == "Speaker":
            button_id = device_info.get("button_id")
            virtual_device_id = device_info.get("virtual_device_id")
            button = get_button_by_id(data_entry.coordinator.data[DATA_BUTTONS], button_id)
            if button:
                devices.append(
                    FlicHubVirtualSpeaker(
                        hass,
                        data_entry.coordinator,
                        entry,
                        button.serial_number,
                        virtual_device_id,
                        flic_hub
                    )
                )

    if devices:
        async_add_devices(devices)

    def async_add_virtual_device(device_info):
        """Add virtual device dynamically."""
        if device_info.get("dimmable_type") == "Speaker":
            button_id = device_info.get("button_id")
            virtual_device_id = device_info.get("virtual_device_id")
            button = get_button_by_id(data_entry.coordinator.data[DATA_BUTTONS], button_id)
            if button:
                async_add_devices([
                    FlicHubVirtualSpeaker(
                        hass,
                        data_entry.coordinator,
                        entry,
                        button.serial_number,
                        virtual_device_id,
                        flic_hub
                    )
                ])

    entry.async_on_unload(
        async_dispatcher_connect(hass, f"{DOMAIN}_{entry.entry_id}_add_virtual_device", async_add_virtual_device)
    )


class FlicHubVirtualSpeaker(FlicHubButtonEntity, MediaPlayerEntity):
    """Flic Hub Virtual Speaker class."""

    _attr_has_entity_name = True
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_supported_features = MediaPlayerEntityFeature.VOLUME_SET

    def __init__(self, hass: HomeAssistant, coordinator, config_entry, serial_number: str, virtual_device_id: str, flic_hub: FlicHubInfo):
        """Initialize the virtual speaker."""
        super().__init__(coordinator, config_entry, serial_number, flic_hub)
        self._virtual_device_id = virtual_device_id

        # Entity attributes
        self._attr_unique_id = f"{self.serial_number}-{virtual_device_id}"
        self._attr_name = virtual_device_id

        # State
        self._volume_level = 0.5
        self._state = MediaPlayerState.PLAYING

        self._latest_values = {}
        self._update_timer = None

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

        if button_id not in [self.serial_number, self.button.bdaddr] or virtual_device_id != self._virtual_device_id:
            return

        values = event.data.get(EVENT_DATA_VALUES, {})

        # The values themselves are always floating point numbers between 0 and 1
        # Extract and convert values
        self._latest_values.update(values)

        if self._update_timer is None:
            self._update_timer = self.hass.loop.call_later(0.1, self._apply_latest_values)

    def _apply_latest_values(self):
        """Apply the latest values and update HA state."""
        self._update_timer = None
        values = self._latest_values
        self._latest_values = {}

        if "volume" in values:
            self._volume_level = float(values["volume"])

        self.schedule_update_ha_state()

    @property
    def state(self) -> MediaPlayerState | None:
        """State of the player."""
        return self._state

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        return self._volume_level

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        client = self.coordinator.hass.data[DOMAIN][self.config_entry.entry_id].client
        values = {"volume": volume}
        self._volume_level = volume
        client.send_virtual_device_update_state("Speaker", self._virtual_device_id, values)
        self.async_write_ha_state()