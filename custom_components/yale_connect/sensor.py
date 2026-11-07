"""Sensors for Yale Connect."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CATEGORY_LOCK
from .coordinator import YaleConnectConfigEntry, YaleConnectCoordinator
from .entity import YaleConnectEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YaleConnectConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        YaleConnectLastUnlock(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if device.get("category") == CATEGORY_LOCK
    )


class YaleConnectLastUnlock(YaleConnectEntity, SensorEntity):
    """Who opened the door last today (name, or the method if it has no user)."""

    _attr_name = "Last unlock"

    def __init__(self, coordinator: YaleConnectCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{self.device['deviceUS']}_last_unlock"

    @property
    def _last(self) -> dict[str, Any] | None:
        return self.coordinator.last_unlock.get(self._device_id)

    @property
    def native_value(self) -> str | None:
        last = self._last
        return (last["user"] or last["method"]) if last else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        last = self._last or {}
        return {k: last.get(k) for k in ("user", "method", "time")}
