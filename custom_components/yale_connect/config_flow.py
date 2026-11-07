"""Config flow for Yale Connect."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import YaleConnectApi, YaleConnectAuthError, YaleConnectError
from .const import CONF_ALLOW_UNLOCK, CONF_ENTRY_CODE, CONF_UUID, DOMAIN
from .coordinator import YaleConnectConfigEntry


class YaleConnectConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(
        self, email: str, password: str, device_uuid: str
    ) -> str | None:
        api = YaleConnectApi(
            async_get_clientsession(self.hass), email, password, device_uuid
        )
        try:
            await api.async_login()
        except YaleConnectAuthError:
            return "invalid_auth"
        except YaleConnectError:
            return "cannot_connect"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()
            await self.async_set_unique_id(email)
            self._abort_if_unique_id_configured()
            device_uuid = str(uuid.uuid4()).upper()
            if error := await self._validate(
                email, user_input[CONF_PASSWORD], device_uuid
            ):
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_UUID: device_uuid,
                    },
                    options={
                        CONF_ENTRY_CODE: user_input.get(CONF_ENTRY_CODE, ""),
                        CONF_ALLOW_UNLOCK: user_input.get(CONF_ALLOW_UNLOCK, False),
                    },
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_ENTRY_CODE, default=""): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Optional(CONF_ALLOW_UNLOCK, default=False): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            if error := await self._validate(
                entry.data[CONF_EMAIL], user_input[CONF_PASSWORD], entry.data[CONF_UUID]
            ):
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"email": entry.data[CONF_EMAIL]},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: YaleConnectConfigEntry) -> OptionsFlow:
        return YaleConnectOptionsFlow()


class YaleConnectOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        opts = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ENTRY_CODE, default=opts.get(CONF_ENTRY_CODE, "")
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                    vol.Optional(
                        CONF_ALLOW_UNLOCK, default=opts.get(CONF_ALLOW_UNLOCK, False)
                    ): bool,
                }
            ),
        )
