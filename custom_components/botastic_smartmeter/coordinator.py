"""DataUpdateCoordinator for botastic_smartmeter."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    BotasticSmartmeterApi,
    BotasticSmartmeterApiError,
)
from .const import DOMAIN, LOGGER


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class BotasticSmartmeterDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: BotasticSmartmeterApi,
    ) -> None:
        """Initialize."""
        self._api = api
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=1),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            return await self._api.async_get_data()
        except BotasticSmartmeterApiError as exception:
            raise UpdateFailed(exception) from exception
