"""Adds config flow for Flic Hub."""
import asyncio
import logging

import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import callback
from pyflichub.client import FlicHubTcpClient
from .const import CLIENT_READY_TIMEOUT
from .const import DOMAIN
from .const import PLATFORMS
from homeassistant.helpers.aiohttp_client import async_create_clientsession

_LOGGER: logging.Logger = logging.getLogger(__package__)


class FlicHubFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for flichub."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self.ip_address = None
        self._errors = {}
        self.discovered_hubs = None
        self.task_discover_devices = None

    async def async_step_dhcp(self, discovery_info):
        """Handle dhcp discovery."""
        self.ip_address = discovery_info.ip
        self._async_abort_entries_match({CONF_IP_ADDRESS: self.ip_address})
        self.ip_address = discovery_info.ip
        self.context["title_placeholders"] = {CONF_IP_ADDRESS: self.ip_address}
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if self.ip_address is None:
            response = await FlicHubTcpClient.discover(async_create_clientsession(self.hass))
            if len(response) > 0:
                self.discovered_hubs = response
                return await self.async_step_devices(user_input)

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_IP_ADDRESS],
                user_input[CONF_PORT]
            )
            if valid:
                return await self._create_entry(user_input)
            self._errors["base"] = "auth"

        return await self._show_config_form(user_input)

    async def async_step_devices(self, user_input=None):
        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_IP_ADDRESS],
                user_input[CONF_PORT]
            )
            if valid:
                user_input[CONF_HUB_SERIAL] = next(
                    hub for hub in self.discovered_hubs if hub['local_ip'] == user_input[CONF_IP_ADDRESS]
                )
                user_input[CONF_FIRMWARE_VERSION] = next(
                    hub['serial_number'] for hub in self.discovered_hubs if hub['local_ip'] == user_input[CONF_IP_ADDRESS]
                )
                return await self._create_entry(user_input)
            self._errors["base"] = "auth"

        return await self._show_select_device_form(self.discovered_hubs)

    async def _create_entry(self, user_input):
        existing_entry = await self.async_set_unique_id(
            user_input[CONF_IP_ADDRESS]
        )
        if existing_entry:
            self.hass.config_entries.async_update_entry(
                existing_entry, data=user_input
            )
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")
        return self.async_create_entry(title=user_input[CONF_IP_ADDRESS], data=user_input)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IP_ADDRESS, default=self.ip_address): str,
                    vol.Required(CONF_PORT): str
                }
            ),
            errors=self._errors,
        )

    async def _show_select_device_form(self, discovered_hubs):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        hubs = {hub['local_ip']: f"{hub['serial_number']} ({hub['local_ip']})" for hub in discovered_hubs}
        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IP_ADDRESS): vol.In(hubs),
                    vol.Required(CONF_PORT): str
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, ip, port):
        """Return true if credentials is valid."""
        try:
            client = FlicHubTcpClient(ip, port, asyncio.get_event_loop())
            client_ready = asyncio.Event()

            def client_connected():
                client_ready.set()

            def client_disconnected():
                _LOGGER.debug("Disconnected")

            client.on_connected = client_connected
            client.on_disconnected = client_disconnected

            asyncio.create_task(client.async_connect())

            with async_timeout.timeout(CLIENT_READY_TIMEOUT):
                await client_ready.wait()

            client.disconnect()
            return True
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.error("Error connecting: %s", e)
            pass
        return False

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
