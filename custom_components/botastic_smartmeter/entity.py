"""BotasticSmartmeterEntity class."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorEntityDescription,
)

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME, MODEL, VERSION, MANUFACTURER
from .coordinator import BotasticSmartmeterDataUpdateCoordinator


@dataclass(frozen=False)
class BotasticSmartmeterSensorEntityDescription(SensorEntityDescription):
    """Describes the botastic sensor entity."""

    octet: str = None
    conversion_factor: float = 1.0
    value: Callable[[float | int], float] | Callable[[datetime], datetime] | None = None

    def __post_init__(self):
        """Defaults the translation_key to the sensor key."""
        self.translation_key = (
            self.translation_key or self.key.replace("#", "_").lower()
        )


class BotasticSmartmeterEntity(CoordinatorEntity):
    """BotasticSmartmeterEntity class."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BotasticSmartmeterDataUpdateCoordinator,
        entity_description: BotasticSmartmeterSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entity_description.key}"
        sn = coordinator._api.device_info["serial_number"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            name=NAME,
            model=MODEL,
            hw_version=VERSION,
            sw_version=VERSION,
            manufacturer=MANUFACTURER,
        )
