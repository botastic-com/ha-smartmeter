"""Custom integration to integrate botastic_smartmeter with Home Assistant.

For more details about this integration, please refer to
https://github.com/botastic-com/ha-smartmeter
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import api
from . import coordinator
from .const import *

PLATFORMS: list[Platform] = [Platform.SENSOR]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    _api_ = api.BotasticSmartmeterApi(
        hass,
        entry.data[CONF_SERIAL_PORT],
        entry.data[CONF_MBUS_KEY],
    )
    _coordinator = coordinator.BotasticSmartmeterDataUpdateCoordinator(
        hass=hass,
        _api=_api_,
    )
    _api_.coordinator = _coordinator
    hass.data[DOMAIN][entry.entry_id] = _coordinator

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await _coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
