"""Adds config flow for Blueprint."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .api import (
    BotasticSmartmeterApi,
    BotasticSmartmeterApiCommunicationError,
    BotasticSmartmeterApiError,
)
from .const import NAME, DOMAIN, LOGGER, CONF_SERIAL_PORT, CONF_MBUS_KEY


class BlueprintFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Botastic Smartmeter."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                del _errors
                # await self._test_serial_port(
                #     serial_port=user_input[CONF_SERIAL_PORT],
                #     mbus_key=user_input[CONF_MBUS_KEY],
                # )
            except BotasticSmartmeterApiCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except BotasticSmartmeterApiError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=NAME,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERIAL_PORT,
                        default=(user_input or {}).get(CONF_SERIAL_PORT),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_MBUS_KEY,
                        default=(user_input or {}).get(CONF_MBUS_KEY),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    # async def _test_serial_port(self, serial_port: str, mbus_key: str) -> None:
    #     """Validate serial port connection."""
    #     client = BotasticSmartmeterApi(
    #         hass=
    #         serial_port=serial_port,
    #         mbus_key=mbus_key,
    #     )
    #     await client.async_get_data()
