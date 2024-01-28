"""Sensor platform for Botastic Smartmeter."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)

from .const import DOMAIN
from .coordinator import BotasticSmartmeterDataUpdateCoordinator
from .entity import BotasticSmartmeterEntity


@dataclass(frozen=True)
class BotasticSmartmeterSensorEntityDescription(SensorEntityDescription):
    """Describes the botastic sensor entity."""

    value: Callable[[float | int], float] | Callable[[datetime], datetime] | None = None


ENTITY_DESCRIPTIONS = (
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_voltage_1",
        translation_key="smartmeter_voltage_1",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_current_1",
        translation_key="smartmeter_current_1",
        icon="mdi:lightning-bolt-outline",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_voltage_2",
        translation_key="smartmeter_voltage_2",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_current_2",
        translation_key="smartmeter_current_2",
        icon="mdi:lightning-bolt-outline",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_voltage_3",
        translation_key="smartmeter_voltage_3",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_current_3",
        translation_key="smartmeter_current_3",
        icon="mdi:lightning-bolt-outline",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_import_power",
        translation_key="smartmeter_import_power",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_export_power",
        translation_key="smartmeter_export_power",
        icon="mdi:flash-outline",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_import_energy",
        translation_key="smartmeter_import_energy",
        icon="mdi:home-lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_export_energy",
        translation_key="smartmeter_export_energy",
        icon="mdi:home-lightning-bolt-outline",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="smartmeter_power_factor",
        translation_key="smartmeter_power_factor",
        icon="mdi:angle-acute",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        value=lambda value: value * 100,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BotasticSmartmeterSensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class BotasticSmartmeterSensor(BotasticSmartmeterEntity, SensorEntity):
    """botastic_smartmeter sensor class."""

    def __init__(
        self,
        coordinator: BotasticSmartmeterDataUpdateCoordinator,
        entity_description: BotasticSmartmeterSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return self.coordinator.data.get("body")
