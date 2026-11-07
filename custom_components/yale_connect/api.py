"""Client for the Yale Connect cloud API (ASSA ABLOY)."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import aiohttp

from .const import API_BASE, BRAND_PLATFORM_GUID

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=20)


class YaleConnectError(Exception):
    """Generic API failure."""


class YaleConnectAuthError(YaleConnectError):
    """Credentials rejected or session could not be renewed."""


class YaleConnectApi:
    """Thin async client mirroring what the Yale Connect mobile app does."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
        uuid: str,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._uuid = uuid
        self._token: str | None = None

    async def _request(
        self, path: str, body: dict[str, Any], *, auth: bool = True
    ) -> tuple[int, Any]:
        headers = {
            "content-type": "application/json",
            "accept": "application/json, text/plain, */*",
            "brandplatformguid": BRAND_PLATFORM_GUID,
        }
        if auth and self._token:
            headers["access-token"] = self._token
        try:
            async with self._session.post(
                f"{API_BASE}/{path}", json=body, headers=headers, timeout=_TIMEOUT
            ) as resp:
                if resp.status == 429 or 500 <= resp.status < 600:
                    raise YaleConnectError(
                        f"Yale Connect temporarily unavailable (HTTP {resp.status})"
                    )
                try:
                    data = await resp.json(content_type=None)
                except aiohttp.ContentTypeError, ValueError:
                    data = None
                return resp.status, data
        except (aiohttp.ClientError, TimeoutError) as err:
            raise YaleConnectError(f"Cannot reach Yale Connect: {err}") from err

    async def async_login(self) -> dict[str, Any]:
        """Log in and keep the access token. Returns the account data."""
        status, data = await self._request(
            "Account/Login",
            {
                "email": self._email,
                "password": self._password,
                "mobileInformation": {
                    "os": "Home Assistant",
                    "information": "Home Assistant",
                    "appVersion": "5.9.12",
                    "pushToken": "",
                    "UUID": self._uuid,
                },
            },
            auth=False,
        )
        if (
            status == 400
            or not isinstance(data, dict)
            or not data.get("success", False)
        ):
            raise YaleConnectAuthError("Invalid email or password")
        token = data.get("accessToken")
        if not token:
            raise YaleConnectAuthError("Login did not return an access token")
        self._token = token
        return data.get("accountData") or {}

    async def async_get_devices(self) -> dict[int, dict[str, Any]]:
        """Return every device of every home, keyed by deviceId."""
        data = await self._sync()
        devices: dict[int, dict[str, Any]] = {}
        for home in (data.get("account") or {}).get("homeList") or []:
            for device in home.get("deviceList") or []:
                device = dict(device)
                device["_home"] = home.get("description")
                device["_home_id"] = home.get("homeId")
                devices[device["deviceId"]] = device
        return devices

    async def _sync(self) -> dict[str, Any]:
        for attempt in (0, 1):
            if self._token is None:
                await self.async_login()
            status, data = await self._request("App/SyncAccount", {})
            if status == 200 and isinstance(data, dict) and "account" in data:
                return data
            if attempt == 0:
                _LOGGER.debug("SyncAccount failed (%s), renewing session", status)
                self._token = None
                continue
            raise YaleConnectError(f"SyncAccount failed with HTTP {status}")
        raise YaleConnectError("unreachable")

    async def async_get_access_registers(
        self, home_id: int, day: date
    ) -> list[dict[str, Any]]:
        """Return the access log of a home for one day (newest first)."""
        body = {
            "homeId": home_id,
            "date": {"year": day.year, "month": day.month, "day": day.day},
        }
        for attempt in (0, 1):
            if self._token is None:
                await self.async_login()
            status, data = await self._request(
                "AccessControl/GetAccessRegistersForHome", body
            )
            if status == 200 and isinstance(data, list):
                return data
            if attempt == 0 and status in (401, 403):
                self._token = None
                continue
            raise YaleConnectError(f"Access register failed with HTTP {status}")
        raise YaleConnectError("unreachable")

    async def async_set_locked(
        self, device_id: int, locked: bool, entry_code: str
    ) -> None:
        """Send a lock/unlock command (asynchronous on the lock side)."""
        for attempt in (0, 1):
            if self._token is None:
                await self.async_login()
            status, data = await self._request(
                "DoorLock/DoorlockLockUnlock",
                {"deviceId": device_id, "isLocked": locked, "entryCode": entry_code},
            )
            if status == 200 and isinstance(data, dict) and data.get("success"):
                return
            if attempt == 0 and status in (401, 403):
                self._token = None
                continue
            raise YaleConnectError(f"Lock command rejected (HTTP {status})")
