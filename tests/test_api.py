"""Regression tests for temporary failures and safe command errors."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.yale_connect.api import (
    YaleConnectApi,
    YaleConnectAuthError,
    YaleConnectError,
)
from custom_components.yale_connect.const import API_BASE


@pytest.fixture
async def api(hass, aioclient_mock):
    """Use synthetic credentials and a session intercepted by aioclient_mock."""
    client = YaleConnectApi(
        async_get_clientsession(hass), "test@example.invalid", "dummy-password", "uuid"
    )
    client._token = "existing-token"
    return client


@pytest.mark.parametrize("status", [429, 500, 502, 503, 599])
@pytest.mark.parametrize("operation", ["login", "devices", "history", "lock", "unlock"])
async def test_temporary_failure_does_not_reauthenticate(
    api, aioclient_mock, status, operation
):
    """Server/rate-limit failures preserve the session and never replay commands."""
    paths = {
        "login": "Account/Login",
        "devices": "App/SyncAccount",
        "history": "AccessControl/GetAccessRegistersForHome",
        "lock": "DoorLock/DoorlockLockUnlock",
        "unlock": "DoorLock/DoorlockLockUnlock",
    }
    aioclient_mock.post(
        f"{API_BASE}/{paths[operation]}",
        status=status,
        json={"success": False, "detail": "dummy-sensitive-response"},
    )

    with pytest.raises(YaleConnectError) as caught:
        if operation == "login":
            await api.async_login()
        elif operation == "devices":
            await api.async_get_devices()
        elif operation == "history":
            await api.async_get_access_registers(1, date(2026, 11, 6))
        else:
            await api.async_set_locked(1, operation == "lock", "001234")

    assert not isinstance(caught.value, YaleConnectAuthError)
    assert str(status) in str(caught.value)
    assert "dummy-sensitive-response" not in str(caught.value)
    assert api._token == "existing-token"
    assert aioclient_mock.call_count == 1


async def test_invalid_credentials_still_raise_auth_error(api, aioclient_mock):
    """A genuine credential rejection must still start the normal reauth flow."""
    aioclient_mock.post(
        f"{API_BASE}/Account/Login", status=400, json={"success": False}
    )
    with pytest.raises(YaleConnectAuthError):
        await api.async_login()


async def test_expired_session_still_renews(api):
    """The temporary-error guard must not break renewal after HTTP 401."""
    with patch.object(
        api,
        "_request",
        AsyncMock(
            side_effect=[
                (401, {}),
                (200, {"success": True, "accessToken": "renewed-token"}),
                (200, {"account": {"homeList": []}}),
            ]
        ),
    ) as request:
        assert await api.async_get_devices() == {}
    assert api._token == "renewed-token"
    assert [call.args[0] for call in request.await_args_list] == [
        "App/SyncAccount",
        "Account/Login",
        "App/SyncAccount",
    ]


@pytest.mark.parametrize("status", [200, 400, 422])
async def test_command_error_does_not_expose_response(
    api, aioclient_mock, caplog, status
):
    """Do not pass echoed PINs, tokens or passwords to HA exceptions or logs."""
    secrets = ("001234", "dummy-private-token", "dummy-private-password")
    aioclient_mock.post(
        f"{API_BASE}/DoorLock/DoorlockLockUnlock",
        status=status,
        json={"success": False, "entryCode": secrets[0], "details": list(secrets)},
    )

    with pytest.raises(YaleConnectError) as caught:
        await api.async_set_locked(1, False, secrets[0])

    assert str(caught.value) == f"Lock command rejected (HTTP {status})"
    for secret in secrets:
        assert secret not in str(caught.value)
        assert secret not in caplog.text
    assert aioclient_mock.call_count == 1


async def test_successful_command_is_sent_once(api, aioclient_mock):
    """Normal successful commands still work without retries."""
    aioclient_mock.post(
        f"{API_BASE}/DoorLock/DoorlockLockUnlock", json={"success": True}
    )
    await api.async_set_locked(1, True, "001234")
    assert aioclient_mock.call_count == 1
