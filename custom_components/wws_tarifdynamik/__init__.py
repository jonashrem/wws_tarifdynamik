"""The WestfalenWIND Tarifdynamik integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import WWSTarifdynamikApi
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
from .coordinator import WWSTarifdynamikCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WestfalenWIND Tarifdynamik from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Get prices from options first, then data, then defaults
    price_smart = entry.options.get(
        CONF_PRICE_SMART,
        entry.data.get(CONF_PRICE_SMART, DEFAULT_PRICE_SMART)
    )
    price_standard = entry.options.get(
        CONF_PRICE_STANDARD,
        entry.data.get(CONF_PRICE_STANDARD, DEFAULT_PRICE_STANDARD)
    )
    saving_window_hours = entry.options.get(
        CONF_SAVING_WINDOW_HOURS,
        entry.data.get(CONF_SAVING_WINDOW_HOURS, DEFAULT_SAVING_WINDOW_HOURS)
    )
    
    api = WWSTarifdynamikApi(
        hass,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    
    coordinator = WWSTarifdynamikCoordinator(
        hass,
        api,
        price_smart=price_smart,
        price_standard=price_standard,
        saving_window_hours=saving_window_hours,
    )
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
