"""Adds config flow for Flic Hub."""
from homeassistant.data_entry_flow import FlowResult
from typing import Any

import async_timeout
import asyncio
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.device_registry import format_mac
from pyflichub.client import FlicHubTcpClient
from .const import CLIENT_READY_TIMEOUT
from .const import DOMAIN
from .const import PLATFORMS

_LOGGER: logging.Logger = logging.getLogger(__package__)


class FlicHubFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for flichub."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._ip_address = None
        self._mac_address = None
        self._errors = {}

    async def async_step_dhcp(self, discovery_info) -> FlowResult:
        """Handle dhcp discovery."""
        self._ip_address = discovery_info.ip
        self._mac_address = discovery_info.macaddress

        self._async_abort_entries_match({CONF_IP_ADDRESS: self._ip_address})
        await self.async_set_unique_id(format_mac(self._mac_address))
        self._abort_if_unique_id_configured(
            updates={
                CONF_IP_ADDRESS: self._ip_address
            }
        )

        self.context["title_placeholders"] = {CONF_IP_ADDRESS: self._ip_address}
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            valid, mac = await self._test_credentials(
                user_input[CONF_IP_ADDRESS],
                user_input[CONF_PORT]
            )
            if valid:
                self._mac_address = mac
                return await self._create_entry(user_input)
            self._errors["base"] = "cannot_connect"

        return await self._show_config_form(user_input)

    async def _create_entry(self, user_input) -> FlowResult:
        existing_entry = await self.async_set_unique_id(
            format_mac(self._mac_address)
        )

        self._abort_if_unique_id_configured(
            updates={
                CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                CONF_PORT: user_input[CONF_PORT],
            }
        )

        if existing_entry:
            self.hass.config_entries.async_update_entry(
                existing_entry, data=user_input
            )
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")
        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

    async def _show_config_form(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Show the configuration form to edit location data."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): str,
                        vol.Required(CONF_IP_ADDRESS, default=self._ip_address): str,
                        vol.Required(CONF_PORT, default="8124"): str
                    }
                ),
                errors=self._errors,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=user_input.get(CONF_NAME, None)): str,
                    vol.Required(CONF_IP_ADDRESS, default=user_input.get(CONF_IP_ADDRESS, self._ip_address)): str,
                    vol.Required(CONF_PORT, default=user_input.get(CONF_PORT, "8124")): str
                }
            ),
            errors=self._errors,
        )

    @staticmethod
    async def _test_credentials(ip, port) -> tuple[bool, str | None]:
        """Return true if credentials is valid."""
        client = FlicHubTcpClient(ip, port, asyncio.get_event_loop())
        try:
            client_ready = asyncio.Event()

            async def client_connected():
                client_ready.set()

            async def client_disconnected():
                _LOGGER.debug("Disconnected")

            client.async_on_connected = client_connected
            client.async_on_disconnected = client_disconnected

            asyncio.create_task(client.async_connect())

            async with async_timeout.timeout(CLIENT_READY_TIMEOUT):
                await client_ready.wait()

            hub_info = await client.get_hubinfo()
            if hub_info.has_wifi() and hub_info.wifi.ip == ip:
                client.disconnect()
                return True, hub_info.wifi.mac

            if hub_info.has_ethernet() and hub_info.ethernet.ip == ip:
                client.disconnect()
                return True, hub_info.ethernet.mac

            client.disconnect()
            return False, None
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.error("Error connecting", exc_info=e)
            client.disconnect()
            pass
        return False, None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return FlicHubOptionsFlowHandler(config_entry)


class FlicHubOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for flichub."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_IP_ADDRESS), data=self.options
        )
