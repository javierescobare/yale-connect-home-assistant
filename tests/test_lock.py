"""Regression tests for removed devices and the unlock safety guard."""

import time
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.yale_connect.const import (
    DOMAIN,
    STATE_LOCKED,
    STATE_UNLOCKED,
)
from custom_components.yale_connect.coordinator import YaleConnectCoordinator
from custom_components.yale_connect.lock import YaleConnectLock


@pytest.fixture
def lock(hass):
    """Construct real entities with a simulated cloud client."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    coordinator = YaleConnectCoordinator(hass, entry, AsyncMock())
    coordinator.data = {
        1: {"deviceUS": "test-lock", "state": STATE_LOCKED, "isOnline": True}
    }
    coordinator.last_update_success = True
    entity = YaleConnectLock(coordinator, entry, 1)
    entity.hass = hass
    return entity


@pytest.mark.parametrize("target", [STATE_LOCKED, STATE_UNLOCKED])
async def test_removed_device_cancels_pending_operation(lock, target):
    """A removed device becomes unavailable without raising or refreshing again."""
    lock._pending = (target, time.monotonic() + 45)
    lock._seen_moving = True
    lock.coordinator.data = {}

    with patch.object(lock, "async_write_ha_state") as write_state:
        lock._handle_coordinator_update()

    assert lock._pending is None
    assert lock._seen_moving is False
    assert lock.available is False
    assert lock.is_locking is False
    assert lock.is_unlocking is False
    write_state.assert_called_once()

    with patch.object(
        lock.coordinator, "async_refresh", new_callable=AsyncMock
    ) as refresh:
        await lock._refresh(None)
    refresh.assert_not_awaited()


async def test_existing_device_still_completes_pending_operation(lock):
    """Reaching the requested state still clears the pending operation."""
    lock._pending = (STATE_LOCKED, time.monotonic() + 45)
    with patch.object(lock, "async_write_ha_state"):
        lock._handle_coordinator_update()
    assert lock._pending is None
    assert lock.available is True
    assert lock.is_locked is True


async def test_unlock_disabled_never_sends_command(lock):
    """The default permission continues to prevent all unlock API calls."""
    with pytest.raises(HomeAssistantError, match="disabled"):
        await lock.async_unlock()
    lock.coordinator.api.async_set_locked.assert_not_awaited()
