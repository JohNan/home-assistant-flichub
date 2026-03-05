"""Light platform for Flic Hub Virtual Devices."""
import logging
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from pyflichub.flichub import FlicHubInfo

from . import FlicHubEntryData
from .const import DOMAIN, DATA_BUTTONS, DATA_HUB, DATA_VIRTUAL_DEVICES, get_button_by_id
from .const import EVENT_VIRTUAL_DEVICE_UPDATE, EVENT_DATA_META_DATA, EVENT_DATA_VALUES
from .entity import FlicHubButtonEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Set up the light platform."""
    data_entry: FlicHubEntryData = hass.data[DOMAIN][entry.entry_id]
    flic_hub = data_entry.coordinator.data[DATA_HUB]

    # Add existing virtual devices
    virtual_devices = entry.data.get(DATA_VIRTUAL_DEVICES, [])
    devices = []
    for device_info in virtual_devices:
        if device_info.get("dimmable_type") == "Light":
            button_id = device_info.get("button_id")
            virtual_device_id = device_info.get("virtual_device_id")
            button = get_button_by_id(data_entry.coordinator.data[DATA_BUTTONS], button_id)
            if button:
                devices.append(
                    FlicHubVirtualLight(
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
        if device_info.get("dimmable_type") == "Light":
            button_id = device_info.get("button_id")
            virtual_device_id = device_info.get("virtual_device_id")
            button = get_button_by_id(data_entry.coordinator.data[DATA_BUTTONS], button_id)
            if button:
                async_add_devices([
                    FlicHubVirtualLight(
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


class FlicHubVirtualLight(FlicHubButtonEntity, LightEntity):
    """Flic Hub Virtual Light class."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.HS
    _attr_supported_color_modes = {ColorMode.HS, ColorMode.COLOR_TEMP}

    def __init__(self, hass: HomeAssistant, coordinator, config_entry, serial_number: str, virtual_device_id: str, flic_hub: FlicHubInfo):
        """Initialize the virtual light."""
        super().__init__(coordinator, config_entry, serial_number, flic_hub)
        self._virtual_device_id = virtual_device_id

        # Entity attributes
        self._attr_unique_id = f"{self.serial_number}-{virtual_device_id}"
        self._attr_name = virtual_device_id

        # State
        self._is_on = False
        self._brightness = 255
        self._hs_color = None
        self._color_temp = None

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

        if "brightness" in values:
            self._brightness = int(values["brightness"] * 255)
            self._is_on = self._brightness > 0

        if "hue" in values and "saturation" in values:
            self._hs_color = (values["hue"] * 360, values["saturation"] * 100)
            self._attr_color_mode = ColorMode.HS

        if "colorTemperature" in values:
            # We don't have min/max mireds strictly defined by flic, keep it simple or convert if needed
            self._color_temp = int(values["colorTemperature"] * 500)  # rough estimation
            self._attr_color_mode = ColorMode.COLOR_TEMP

        if "is_on" in values:
            self._is_on = bool(values["is_on"])

        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the hue and saturation color value [float, float]."""
        return self._hs_color

    @property
    def color_temp(self) -> int | None:
        """Return the CT color value in mireds."""
        return self._color_temp

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        client = self.coordinator.hass.data[DOMAIN][self.config_entry.entry_id].client

        values = {}
        if "brightness" in kwargs:
            values["brightness"] = kwargs["brightness"] / 255.0
            self._brightness = kwargs["brightness"]
        else:
            values["brightness"] = self._brightness / 255.0 if self._brightness else 1.0
            self._brightness = self._brightness if self._brightness else 255

        if "hs_color" in kwargs:
            values["hue"] = kwargs["hs_color"][0] / 360.0
            values["saturation"] = kwargs["hs_color"][1] / 100.0
            self._hs_color = kwargs["hs_color"]

        if "color_temp" in kwargs:
            values["colorTemperature"] = kwargs["color_temp"] / 500.0
            self._color_temp = kwargs["color_temp"]

        self._is_on = True

        client.send_virtual_device_update_state("Light", self._virtual_device_id, values)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        client = self.coordinator.hass.data[DOMAIN][self.config_entry.entry_id].client
        values = {"brightness": 0.0}
        self._is_on = False
        client.send_virtual_device_update_state("Light", self._virtual_device_id, values)
        self.async_write_ha_state()