"""Run the integration against an isolated Home Assistant test instance."""

import pytest


@pytest.fixture(autouse=True)
def enable_integration(enable_custom_integrations):
    """Allow Home Assistant to load the local custom integration."""
    yield
