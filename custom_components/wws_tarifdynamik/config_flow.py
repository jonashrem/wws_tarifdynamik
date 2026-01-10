"""Config flow for WestfalenWIND Tarifdynamik integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import WWSTarifdynamikApi, WWSTarifdynamikAuthError, WWSTarifdynamikApiError
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PRICE_SMART,
    CONF_PRICE_STANDARD,
    CONF_SAVING_WINDOW_HOURS,
    DEFAULT_PRICE_SMART,
    DEFAULT_PRICE_STANDARD,
    DEFAULT_SAVING_WINDOW_HOURS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_PRICE_SMART, default=DEFAULT_PRICE_SMART): vol.Coerce(float),
        vol.Optional(CONF_PRICE_STANDARD, default=DEFAULT_PRICE_STANDARD): vol.Coerce(float),
        vol.Optional(CONF_SAVING_WINDOW_HOURS, default=DEFAULT_SAVING_WINDOW_HOURS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=24)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    api = WWSTarifdynamikApi(hass, data[CONF_USERNAME], data[CONF_PASSWORD])
    
    if not await api.test_connection():
        raise InvalidAuth
    
    return {"title": f"WWS ({data[CONF_USERNAME]})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WestfalenWIND Tarifdynamik."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> WWSTarifdynamikOptionsFlowHandler:
        """Get the options flow for this handler."""
        return WWSTarifdynamikOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class WWSTarifdynamikOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for WWS Tarifdynamik."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PRICE_SMART,
                        default=self.config_entry.options.get(
                            CONF_PRICE_SMART,
                            self.config_entry.data.get(CONF_PRICE_SMART, DEFAULT_PRICE_SMART)
                        ),
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_PRICE_STANDARD,
                        default=self.config_entry.options.get(
                            CONF_PRICE_STANDARD,
                            self.config_entry.data.get(CONF_PRICE_STANDARD, DEFAULT_PRICE_STANDARD)
                        ),
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_SAVING_WINDOW_HOURS,
                        default=self.config_entry.options.get(
                            CONF_SAVING_WINDOW_HOURS,
                            self.config_entry.data.get(CONF_SAVING_WINDOW_HOURS, DEFAULT_SAVING_WINDOW_HOURS)
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
                }
            ),
        )
