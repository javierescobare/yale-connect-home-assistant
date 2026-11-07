"""Lock activity events for Yale Connect (who locked/unlocked, and how)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CATEGORY_LOCK,
    EVENT_LOCKED,
    EVENT_UNKNOWN,
    EVENT_UNLOCKED,
    SIGNAL_ACTIVITY,
)
from .coordinator import YaleConnectConfigEntry, YaleConnectCoordinator
from .entity import YaleConnectEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YaleConnectConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        YaleConnectActivity(coordinator, entry, device_id)
        for device_id, device in coordinator.data.items()
        if device.get("category") == CATEGORY_LOCK
    )


class YaleConnectActivity(YaleConnectEntity, EventEntity):
    """Fires on every lock/unlock reported by the cloud access log."""

    _attr_name = "Activity"
    _attr_event_types = [EVENT_LOCKED, EVENT_UNLOCKED, EVENT_UNKNOWN]

    def __init__(
        self,
        coordinator: YaleConnectCoordinator,
        entry: YaleConnectConfigEntry,
        device_id: int,
    ) -> None:
        super().__init__(coordinator, device_id)
        self._entry = entry
        self._attr_unique_id = f"{self.device['deviceUS']}_activity"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_ACTIVITY.format(self._entry.entry_id),
                self._handle_activity,
            )
        )

    @callback
    def _handle_activity(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            if event["device_id"] != self._device_id:
                continue
            self._trigger_event(
                event["event_type"],
                {k: event[k] for k in ("user", "method", "reason", "time")},
            )
            # One state write per event, or a batch would hide all but the last.
            self.async_write_ha_state()
