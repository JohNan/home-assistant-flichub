try:
    from homeassistant.components.infrared import InfraredEntity, InfraredCommand
except ImportError:
    InfraredEntity = object
    InfraredCommand = object
from .entity import FlicHubEntity
from .const import DOMAIN, DATA_HUB

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Flic Hub infrared platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.coordinator
    client = data.client

    hub_info = coordinator.data.get(DATA_HUB)

    if hub_info:
        async_add_entities([FlicHubInfraredEntity(coordinator, entry, client, hub_info)])

class FlicHubInfraredEntity(FlicHubEntity, InfraredEntity):
    """Flic Hub IR Transmitter Entity."""

    _attr_name = "IR Transmitter"
    _attr_icon = "mdi:remote"

    def __init__(self, coordinator, config_entry, client, flic_hub):
        """Initialize the infrared entity."""
        super().__init__(coordinator, config_entry, flic_hub)
        self.client = client
        self._attr_unique_id = f"{self.mac_address}-infrared"

    @property
    def device_info(self):
        """Return device info to attach to the Flic Hub device."""
        return {
            "identifiers": {(DOMAIN, self.mac_address)}
        }

    async def async_send_command(self, command: InfraredCommand) -> None:
        """Send an IR command."""
        timings = [
            interval
            for timing in command.get_raw_timings()
            for interval in (timing.high_us, -timing.low_us)
        ]

        arr = [command.modulation] + timings
        await self.client.play_ir_raw(arr)
