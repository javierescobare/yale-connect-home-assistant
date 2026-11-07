"""The Yale Connect integration (ASSA ABLOY cloud, YDM60 and friends)."""

from __future__ import annotations

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import YaleConnectApi, YaleConnectAuthError, YaleConnectError
from .const import CONF_UUID
from .coordinator import YaleConnectConfigEntry, YaleConnectCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.EVENT, Platform.LOCK, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: YaleConnectConfigEntry) -> bool:
    api = YaleConnectApi(
        async_get_clientsession(hass),
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_UUID],
    )
    try:
        await api.async_login()
    except YaleConnectAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except YaleConnectError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = YaleConnectCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: YaleConnectConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: YaleConnectConfigEntry
) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
