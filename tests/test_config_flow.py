"""Verify PIN masking and saving through real Home Assistant flows."""

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.helpers.selector import TextSelector, TextSelectorType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.yale_connect.const import (
    CONF_ALLOW_UNLOCK,
    CONF_ENTRY_CODE,
    DOMAIN,
)


def assert_masked_pin(schema):
    """Check the field sent to the frontend uses its password selector."""
    validator = next(
        value for key, value in schema.schema.items() if key.schema == CONF_ENTRY_CODE
    )
    assert isinstance(validator, TextSelector)
    assert validator.config["type"] == TextSelectorType.PASSWORD


async def test_initial_pin_is_masked(hass):
    """The initial form must use a password selector and retain leading zeros."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == "form"
    schema = result["data_schema"]
    assert_masked_pin(schema)
    values = schema(
        {
            "email": "test@example.invalid",
            "password": "dummy",
            CONF_ENTRY_CODE: "001234",
        }
    )
    assert values[CONF_ENTRY_CODE] == "001234"
    assert values[CONF_ALLOW_UNLOCK] is False


@pytest.mark.parametrize("replacement", ["004321", ""])
async def test_options_pin_is_masked_and_can_be_saved(hass, replacement):
    """Mask the stored PIN while preserving, replacing and clearing its value."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={CONF_ENTRY_CODE: "001234", CONF_ALLOW_UNLOCK: False},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    schema = result["data_schema"]
    assert_masked_pin(schema)
    assert schema({CONF_ALLOW_UNLOCK: False})[CONF_ENTRY_CODE] == "001234"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=schema({CONF_ENTRY_CODE: replacement, CONF_ALLOW_UNLOCK: False}),
    )
    assert result["type"] == "create_entry"
    assert entry.options[CONF_ENTRY_CODE] == replacement
    assert entry.options[CONF_ALLOW_UNLOCK] is False
