"""Lock platform for Yale Connect."""

from __future__ import annotations

import time
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .api import YaleConnectError
from .const import (
    CATEGORY_LOCK,
    CONF_ALLOW_UNLOCK,
    CONF_ENTRY_CODE,
    STATE_LOCKED,
    STATE_MOVING,
    STATE_UNLOCKED,
)
from .coordinator import YaleConnectConfigEntry, YaleConnectCoordinator
from .entity import YaleConnectEntity

PARALLEL_UPDATES = 1
_PENDING_TIMEOUT = 45
_REFRESH_DELAYS = (3, 8, 15)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YaleConnectConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        YaleConnectLock(coordinator, entry, device_id)
        for device_id, device in coordinator.data.items()
        if device.get("category") == CATEGORY_LOCK
    )


class YaleConnectLock(YaleConnectEntity, LockEntity):
    """A Yale Connect door lock."""

    _attr_name = None

    def __init__(
        self,
        coordinator: YaleConnectCoordinator,
        entry: YaleConnectConfigEntry,
        device_id: int,
    ) -> None:
        super().__init__(coordinator, device_id)
        self._entry = entry
        self._attr_unique_id = f"{self.device['deviceUS']}_lock"
        self._pending: tuple[int, float] | None = None  # (target state, deadline)
        self._seen_moving = False

    @property
    def _raw_state(self) -> int | None:
        return self.device.get("state")

    @property
    def is_locked(self) -> bool | None:
        if self._raw_state == STATE_LOCKED:
            return True
        if self._raw_state == STATE_UNLOCKED:
            return False
        return None

    @property
    def is_locking(self) -> bool:
        return self._pending is not None and self._pending[0] == STATE_LOCKED

    @property
    def is_unlocking(self) -> bool:
        return self._pending is not None and self._pending[0] == STATE_UNLOCKED

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "raw_state": self._raw_state,
            "alarm": self.device.get("alarm"),
            "unlock_allowed": self._entry.options.get(CONF_ALLOW_UNLOCK, False),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._device_id not in self.coordinator.data:
            self._pending = None
            self._seen_moving = False
        elif self._pending:
            if self._raw_state == STATE_MOVING:
                self._seen_moving = True
            # Stop waiting once the target is reached, the lock finished moving
            # (it may have auto-relocked before we polled), or we timed out.
            if (
                self._raw_state == self._pending[0]
                or (self._seen_moving and self._raw_state != STATE_MOVING)
                or time.monotonic() > self._pending[1]
            ):
                self._pending = None
                self._seen_moving = False
        super()._handle_coordinator_update()

    async def async_lock(self, **kwargs: Any) -> None:
        await self._send(STATE_LOCKED)

    async def async_unlock(self, **kwargs: Any) -> None:
        if not self._entry.options.get(CONF_ALLOW_UNLOCK, False):
            raise HomeAssistantError(
                "Unlocking from Home Assistant is disabled. Enable it in the "
                "Yale Connect integration options."
            )
        await self._send(STATE_UNLOCKED)

    async def _send(self, target: int) -> None:
        code = self._entry.options.get(CONF_ENTRY_CODE) or self._entry.data.get(
            CONF_ENTRY_CODE, ""
        )
        try:
            await self.coordinator.api.async_set_locked(
                self._device_id, target == STATE_LOCKED, code
            )
        except YaleConnectError as err:
            raise HomeAssistantError(str(err)) from err
        self._pending = (target, time.monotonic() + _PENDING_TIMEOUT)
        self._seen_moving = False
        self.async_write_ha_state()
        for delay in _REFRESH_DELAYS:
            self._entry.async_on_unload(
                async_call_later(self.hass, delay, self._refresh)
            )

    async def _refresh(self, _now: Any) -> None:
        if self._pending:
            await self.coordinator.async_refresh()
