"""BotasticSmartmeterEntity class."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntityDescription,
)

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import coordinator

from .const import ATTRIBUTION, DOMAIN, NAME, MODEL, VERSION, MANUFACTURER


@dataclass(frozen=False)
class BotasticSmartmeterSensorEntityDescription(SensorEntityDescription):
    """Describes the botastic sensor entity."""

    def __init__(self, octet: str, conversion_factor: float, *args, **kwargs):
        self.conversion_factor = conversion_factor
        self.octet = octet
        super().__init__(*args, **kwargs)
        self.translation_key = (
            self.translation_key or self.key.replace("#", "_").lower()
        )


class BotasticSmartmeterEntity(CoordinatorEntity):
    """BotasticSmartmeterEntity class."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        _coordinator: coordinator.BotasticSmartmeterDataUpdateCoordinator,
        entity_description: BotasticSmartmeterSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(_coordinator)
        self._attr_unique_id = f"{entity_description.key}"
        sn = _coordinator._api.device_info["serial_number"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            name=NAME,
            model=MODEL,
            hw_version=VERSION,
            sw_version=VERSION,
            manufacturer=MANUFACTURER,
        )
