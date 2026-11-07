"""Binary sensors (battery, connectivity) for Yale Connect."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import YaleConnectConfigEntry, YaleConnectCoordinator
from .entity import YaleConnectEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YaleConnectConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for device_id, device in coordinator.data.items():
        entities.append(YaleConnectOnline(coordinator, device_id))
        if "lowBattery" in device:
            entities.append(YaleConnectLowBattery(coordinator, device_id))
    async_add_entities(entities)


class YaleConnectOnline(YaleConnectEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: YaleConnectCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{self.device['deviceUS']}_online"

    @property
    def available(self) -> bool:
        # Reports the connectivity itself, so only depends on the coordinator.
        return self.coordinator.last_update_success and (
            self._device_id in self.coordinator.data
        )

    @property
    def is_on(self) -> bool:
        return bool(self.device.get("isOnline"))


class YaleConnectLowBattery(YaleConnectEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.BATTERY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: YaleConnectCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{self.device['deviceUS']}_low_battery"

    @property
    def is_on(self) -> bool:
        return bool(self.device.get("lowBattery"))
