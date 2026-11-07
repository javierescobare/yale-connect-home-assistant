"""Base entity for Yale Connect."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import YaleConnectCoordinator


class YaleConnectEntity(CoordinatorEntity[YaleConnectCoordinator]):
    """Entity bound to one Yale Connect device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: YaleConnectCoordinator, device_id: int) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        device = self.device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device["deviceUS"]))},
            name=device.get("description"),
            manufacturer="Yale",
            model=device.get("deviceModelDescription"),
            sw_version=device.get("currentFirmwareVersion") or None,
            via_device=None
            if device.get("controllerType") == "Hub"
            else _hub_identifier(coordinator.data, device),
        )

    @property
    def device(self) -> dict[str, Any]:
        return self.coordinator.data[self._device_id]

    @property
    def available(self) -> bool:
        return (
            super().available
            and self._device_id in self.coordinator.data
            and bool(self.device.get("isOnline"))
        )


def _hub_identifier(
    data: dict[int, dict[str, Any]], device: dict[str, Any]
) -> tuple[str, str] | None:
    parent = (device.get("deviceParameters") or {}).get("parentDeviceId")
    hub = data.get(parent) if parent is not None else None
    return (DOMAIN, str(hub["deviceUS"])) if hub else None
