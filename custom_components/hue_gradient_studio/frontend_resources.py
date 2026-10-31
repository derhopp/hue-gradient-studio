"""Serve and register the bundled Lovelace editor.

HACS installs files under custom_components/hue_gradient_studio, so the
JavaScript asset is served directly from the integration.
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
    """Serve JavaScript and ensure it is a Lovelace resource (storage mode)."""
    js_path = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(URL_BASE, str(js_path), False)]
        )
    except RuntimeError:
        # A duplicate static route is harmless in dev/hot-reload scenarios.
        _LOGGER.debug("Gradient Studio frontend path was already registered")

    async def add_resource() -> None:
        """Wait until Lovelace is available, then register our JS module."""
        base_url = f"{URL_BASE}/{SCRIPT_NAME}"
        wanted = f"{base_url}?v={version}"
        for attempt in range(12):
            lovelace = hass.data.get("lovelace")
            if lovelace is None:
                await asyncio.sleep(2)
                continue

            resource_mode = getattr(lovelace, "resource_mode", None)
            if resource_mode == "yaml":
                _LOGGER.info(
                    "Lovelace resources use YAML; add %s manually as a "
                    "JavaScript module", wanted
                )
                return

            resources = getattr(lovelace, "resources", None)
            if resources is None:
                await asyncio.sleep(2)
                continue

            try:
                # Lovelace resource storage is loaded lazily. async_items()
                # must NOT run before loading: it could miss other resources.
                # In HA 2026.10, async_get_info() calls _async_ensure_loaded().
                if not getattr(resources, "loaded", False):
                    await resources.async_get_info()
                if not getattr(resources, "loaded", False):
                    await asyncio.sleep(2)
                    continue

                matches = [
                    item for item in resources.async_items()
                    if item.get("url", "").split("?", 1)[0] == base_url
                ]
                if matches:
                    item = matches[0]
                    # Stored resources expose "type" (not "res_type").
                    if item.get("url") != wanted or item.get("type") != "module":
                        await resources.async_update_item(
                            item["id"], {"res_type": "module", "url": wanted}
                        )
                else:
                    await resources.async_create_item(
                        {"res_type": "module", "url": wanted}
                    )
                _LOGGER.info("Gradient Studio Lovelace resource registered: %s", wanted)
            except Exception:
                # Never block ZHA controls because of a dashboard problem.
                _LOGGER.exception(
                    "Could not register Gradient Studio Lovelace resource. "
                    "Add %s manually as a JavaScript module", wanted
                )
            return

        _LOGGER.warning(
            "Lovelace resources not ready; register %s manually as a "
            "JavaScript module", wanted
        )

    if hass.state == CoreState.running:
        hass.async_create_task(add_resource())
    else:
        @callback
        def on_start(_event) -> None:
            hass.async_create_task(add_resource())

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, on_start)
