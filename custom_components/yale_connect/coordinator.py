"""Data coordinator for Yale Connect."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import YaleConnectApi, YaleConnectAuthError, YaleConnectError
from .const import (
    CATEGORY_LOCK,
    DOMAIN,
    EVENT_UNKNOWN,
    EVENT_UNLOCKED,
    REGISTER_STATUS_EVENTS,
    SCAN_INTERVAL_SECONDS,
    SIGNAL_ACTIVITY,
)

_LOGGER = logging.getLogger(__name__)

type YaleConnectConfigEntry = ConfigEntry[YaleConnectCoordinator]


class YaleConnectCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Polls the cloud for the state and the access log of all devices."""

    config_entry: YaleConnectConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: YaleConnectConfigEntry,
        api: YaleConnectApi,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api = api
        # deviceId -> operationDateTime (naive ISO string) of the newest entry seen
        self._last_seen: dict[int, str] = {}
        self._registers_seeded = False
        # deviceId -> last unlock entry (user, method, time)
        self.last_unlock: dict[int, dict[str, Any]] = {}

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        try:
            devices = await self.api.async_get_devices()
        except YaleConnectAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except YaleConnectError as err:
            raise UpdateFailed(str(err)) from err
        await self._async_update_activity(devices)
        return devices

    async def _async_update_activity(self, devices: dict[int, dict[str, Any]]) -> None:
        """Read the access log and fire an event for every new entry."""
        home_ids = {
            device["_home_id"]
            for device in devices.values()
            if device.get("category") == CATEGORY_LOCK and device.get("_home_id")
        }
        entries: list[dict[str, Any]] = []
        try:
            for home_id in home_ids:
                entries += await self.api.async_get_access_registers(
                    home_id, dt_util.now().date()
                )
        except YaleConnectError as err:
            # The log is a bonus: never make the lock state unavailable for it.
            _LOGGER.debug("Could not read the access log: %s", err)
            return

        entries = [e for e in entries if e.get("operationDateTime")]
        entries.sort(key=lambda e: e["operationDateTime"])  # oldest first
        new: list[dict[str, Any]] = []
        for entry in entries:
            device_id = entry.get("deviceId")
            stamp = entry["operationDateTime"]
            if REGISTER_STATUS_EVENTS.get(entry.get("statusId")) == EVENT_UNLOCKED:
                self.last_unlock[device_id] = self._describe(entry)
            if stamp > self._last_seen.get(device_id, ""):
                self._last_seen[device_id] = stamp
                new.append(entry)

        if not self._registers_seeded:
            # First read: only learn the history, don't replay it as new events.
            self._registers_seeded = True
            return
        if new:
            async_dispatcher_send(
                self.hass,
                SIGNAL_ACTIVITY.format(self.config_entry.entry_id),
                [self._describe(e) | {"device_id": e.get("deviceId")} for e in new],
            )

    @staticmethod
    def _describe(entry: dict[str, Any]) -> dict[str, Any]:
        when = dt_util.parse_datetime(entry["operationDateTime"])
        if when is not None and when.tzinfo is None:
            # The log reports the home's local wall-clock time.
            when = when.replace(tzinfo=dt_util.get_default_time_zone())
        return {
            "event_type": REGISTER_STATUS_EVENTS.get(
                entry.get("statusId"), EVENT_UNKNOWN
            ),
            "user": entry.get("userName") or None,
            "method": entry.get("sourceName") or None,
            "reason": entry.get("reasonName") or None,
            "time": when.isoformat() if when else None,
        }
