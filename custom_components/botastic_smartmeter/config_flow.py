"""Adds config flow for Blueprint."""

from __future__ import annotations

from typing import Any
import serial.tools.list_ports
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import usb

from .api import (
    BotasticSmartmeterApi,
    BotasticSmartmeterApiCommunicationError,
    BotasticSmartmeterApiError,
)
from .const import (
    NAME,
    DOMAIN,
    LOGGER,
    CONF_SERIAL_PORT,
    CONF_SERIAL_PORT_MANUAL,
    CONF_MBUS_KEY,
    CONF_MBUS_KEY_DEFAULT,
)


class BlueprintFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Botastic Smartmeter."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._serial_port: str | None = None
        self._mbus_key: str | None = None

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            user_selection = user_input[CONF_SERIAL_PORT]
            if user_selection == CONF_SERIAL_PORT_MANUAL:
                self._mbus_key = user_input[CONF_MBUS_KEY]
                return await self.async_step_setup_serial_manual()

            user_input[CONF_SERIAL_PORT] = await self.hass.async_add_executor_job(
                usb.get_serial_by_id, user_input[CONF_SERIAL_PORT]
            )
            try:
                await self._validate_serial_port(user_input)

            except BotasticSmartmeterApiCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except BotasticSmartmeterApiError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_SERIAL_PORT])
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_SERIAL_PORT: user_input[CONF_SERIAL_PORT],
                        CONF_MBUS_KEY: user_input[CONF_MBUS_KEY],
                    }
                )
                self._serial_port = user_input[CONF_SERIAL_PORT]
                self._mbus_key = user_input[CONF_MBUS_KEY]
                return self.async_create_entry(title=NAME, data=user_input)

        ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)
        list_of_ports = {
            port.device: usb.human_readable_device_name(
                port.device,
                port.serial_number,
                port.manufacturer,
                port.description,
                port.vid,
                port.pid,
            )
            for port in ports
        }

        list_of_ports[CONF_SERIAL_PORT_MANUAL] = CONF_SERIAL_PORT_MANUAL

        schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL_PORT): vol.In(list_of_ports),
                vol.Required(CONF_MBUS_KEY, default=str(CONF_MBUS_KEY_DEFAULT)): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=_errors,
        )

    async def async_step_setup_serial_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Select path manually."""
        _errors = {}
        if user_input is not None:
            user_input[CONF_MBUS_KEY] = self._mbus_key
            try:
                await self._validate_serial_port(user_input)

            except BotasticSmartmeterApiCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except BotasticSmartmeterApiError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_SERIAL_PORT])
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_SERIAL_PORT: user_input[CONF_SERIAL_PORT],
                        CONF_MBUS_KEY: user_input[CONF_MBUS_KEY],
                    }
                )
                self._serial_port = user_input[CONF_SERIAL_PORT]
                # self._mbus_key = user_input[CONF_MBUS_KEY]
                return self.async_create_entry(title=NAME, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL_PORT): str,
            }
        )

        return self.async_show_form(
            step_id="setup_serial_manual", data_schema=schema, errors=_errors
        )

    async def _validate_serial_port(self, user_input: dict[str, Any]) -> bool:
        """Validate serial port connection."""
        client = None
        try:
            client = BotasticSmartmeterApi(
                hass=self.hass,
                serial_port=user_input[CONF_SERIAL_PORT],
                mbus_key=user_input[CONF_MBUS_KEY],
            )
            await client.async_open_port()
            LOGGER.info("Successfully connected to botastic smartmeter bridge")
            return True

        finally:
            if client is not None:
                await client.async_close_port()
