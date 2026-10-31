"""UI setup for Hue Gradient Studio; no credentials or configuration required."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

DOMAIN = "hue_gradient_studio"


class HueGradientStudioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Allow a single integration entry per Home Assistant instance."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Hue Gradient Studio", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
