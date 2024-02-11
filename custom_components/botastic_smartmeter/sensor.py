"""Sensor platform for Botastic Smartmeter."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)

import botastic_smartmeter.coordinator
from .const import DOMAIN, LOGGER
from .entity import BotasticSmartmeterEntity, BotasticSmartmeterSensorEntityDescription

ENTITY_DESCRIPTIONS = (
    BotasticSmartmeterSensorEntityDescription(
        key="voltage_1",
        octet="0100200700FF",
        conversion_factor=0.1,
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="current_1",
        octet="01001F0700FF",
        conversion_factor=0.01,
        icon="mdi:lightning-bolt-outline",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="voltage_2",
        octet="0100340700FF",
        conversion_factor=0.1,
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="current_2",
        octet="0100330700FF",
        conversion_factor=0.01,
        icon="mdi:lightning-bolt-outline",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="voltage_3",
        octet="0100480700FF",
        conversion_factor=0.1,
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="current_3",
        octet="0100470700FF",
        conversion_factor=0.01,
        icon="mdi:lightning-bolt-outline",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="power_import",
        octet="0100010700FF",
        icon="mdi:flash",
        conversion_factor=1.0,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="power_export",
        octet="0100020700FF",
        conversion_factor=1.0,
        icon="mdi:flash-outline",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="energy_import",
        octet="0100010800FF",
        conversion_factor=0.001,
        icon="mdi:home-lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="energy_export",
        octet="0100020800FF",
        conversion_factor=0.001,
        icon="mdi:home-lightning-bolt-outline",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    BotasticSmartmeterSensorEntityDescription(
        key="power_factor",
        octet="01000D0700FF",
        conversion_factor=0.001,
        icon="mdi:angle-acute",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        value=lambda value: value * 100,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities_to_add: list[SensorEntity] = []
    for entity_description in ENTITY_DESCRIPTIONS:
        entities_to_add.append(
            BotasticSmartmeterSensor(coordinator, entity_description)
        )
    async_add_entities(entities_to_add, False)


class BotasticSmartmeterSensor(BotasticSmartmeterEntity, SensorEntity):
    """botastic_smartmeter sensor class."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: botastic_smartmeter.BotasticSmartmeterDataUpdateCoordinator,
        entity_description: BotasticSmartmeterSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, entity_description)
        self.entity_description = entity_description
        LOGGER.info("Added entity %s", self.entity_description.key)

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        values = self.coordinator.data
        value = values.get(self.translation_key)
        if self.entity_description.value:
            return self.entity_description.value(value)
        return value
