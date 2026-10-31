"""Serve and register the bundled Lovelace editor.

HACS installs only files under custom_components/hue_gradient_studio, therefore the
JavaScript asset lives next to the integration instead of /config/www.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant, callback

_LOGGER = logging.getLogger(__name__)

URL_BASE = "/hue-gradient-studio"
SCRIPT_NAME = "hue-gradient-studio.js"


async def async_setup_frontend(hass: HomeAssistant, version: str) -> None:
    """Expose the JavaScript file and register it in storage-mode dashboards."""
    js_path = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(URL_BASE, str(js_path), False)]
        )
    except RuntimeError:
        # A duplicate static route is harmless in dev/hot-reload scenarios.
        _LOGGER.debug("Gradient Studio frontend path was already registered")

    async def add_resource() -> None:
        """Lovelace resources sometimes load shortly after HA starts."""
        for attempt in range(12):
            lovelace = hass.data.get("lovelace")
            if lovelace is None:
                await asyncio.sleep(2)
                continue
            if getattr(lovelace, "mode", None) != "storage":
                _LOGGER.info(
                    "Lovelace is in YAML mode: add the JavaScript resource manually "
                    "using %s/%s?v=%s", URL_BASE, SCRIPT_NAME, version
                )
                return
            resources = getattr(lovelace, "resources", None)
            if resources is None or not getattr(resources, "loaded", False):
                await asyncio.sleep(2)
                continue

            base_url = f"{URL_BASE}/{SCRIPT_NAME}"
            wanted = f"{base_url}?v={version}"
            try:
                matches = [
                    item for item in resources.async_items()
                    if item.get("url", "").split("?", 1)[0] == base_url
                ]
                if matches:
                    if matches[0]["url"] != wanted or matches[0].get("res_type") != "module":
                        await resources.async_update_item(
                            matches[0]["id"], {"res_type": "module", "url": wanted}
                        )
                else:
                    await resources.async_create_item(
                        {"res_type": "module", "url": wanted}
                    )
                _LOGGER.debug("Lovelace resource ready: %s", wanted)
            except Exception:  # never block ZHA controls because of a Lovelace problem
                _LOGGER.exception(
                    "Could not register Gradient Studio Lovelace resource. "
                    "Add %s manually as a JavaScript module.", wanted
                )
            return
        _LOGGER.warning("Lovelace resources did not become ready; register %s/%s?v=%s manually", URL_BASE, SCRIPT_NAME, version)

    if hass.state == CoreState.running:
        hass.async_create_task(add_resource())
    else:
        @callback
        def on_start(_event) -> None:
            hass.async_create_task(add_resource())

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, on_start)
