"""Hue Gradient Studio: scalable per-device ZHA color-gradient control.

Installed through HACS and configured using Home Assistant's UI.
Storage: .storage/hue_gradient_studio (managed by Home Assistant).
The Zigbee manufacturer command is model-specific, so the UI permits choosing
between gradient (experimental except for tested devices) and solid-color mode.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .gradient import DEFAULT_PRESETS, encode_gradient, validate_colors
from .frontend_resources import async_setup_frontend

DOMAIN = "hue_gradient_studio"
STORAGE_VERSION = 1
_LOGGER = logging.getLogger(__name__)

MIN_INTERVAL = 30
MAX_INTERVAL = 3600


def _defaults(model: str, name: str) -> dict[str, Any]:
    """Choose a conservative transport for ordinary Hue lamps."""
    likely_gradient = "gradient" in (model + " " + name).lower() or model.upper().startswith("LCX")
    return {
        "mode": "gradient" if likely_gradient else "solid",
        "endpoint": 11,
        "reverse": True,
        "active": 1,
        "interval": 120,
        "auto": False,
        "presets": deepcopy(DEFAULT_PRESETS),
    }


class GradientManager:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, DOMAIN)
        self.data: dict[str, Any] = {"devices": {}, "selection": []}
        self.tasks: dict[str, asyncio.Task] = {}
        self.locks: dict[str, asyncio.Lock] = {}
        self.write_lock = asyncio.Lock()

    async def initialize(self) -> None:
        loaded = await self.store.async_load()
        if isinstance(loaded, dict):
            self.data = {"devices": loaded.get("devices", {}), "selection": loaded.get("selection", [])}
        for device_id, settings in list(self.data["devices"].items()):
            if settings.get("auto"):
                self._start_cycle(device_id)
        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._on_stop)

    @callback
    def _on_stop(self, event) -> None:
        for task in self.tasks.values():
            task.cancel()
        self.tasks.clear()

    def discover(self) -> dict[str, dict[str, Any]]:
        """Resolve ZHA IEEE addresses from the public HA device registry."""
        devices = dr.async_get(self.hass)
        entities = er.async_get(self.hass)
        result: dict[str, dict[str, Any]] = {}
        for entry in entities.entities.values():
            if entry.domain != "light" or entry.platform != "zha" or entry.disabled_by or not entry.device_id:
                continue
            device = devices.async_get(entry.device_id)
            if not device:
                continue
            maker = (device.manufacturer or "").lower()
            if "philips" not in maker and "signify" not in maker:
                continue
            ieee = next((idval for domain, idval in device.identifiers if domain == "zha"), None)
            if not ieee:
                ieee = next((idval for domain, idval in device.connections if domain == dr.CONNECTION_ZIGBEE), None)
            if not ieee:
                continue
            model = device.model or ""
            name = device.name_by_user or device.name or entry.entity_id
            if device.id not in result:
                result[device.id] = {
                    "device_id": device.id,
                    "entity_id": entry.entity_id,
                    "name": name,
                    "model": model,
                    "manufacturer": device.manufacturer or "",
                    "ieee": str(ieee),
                }
            elif self.hass.states.get(result[device.id]["entity_id"]) is None:
                result[device.id]["entity_id"] = entry.entity_id
        return dict(sorted(result.items(), key=lambda item: (item[1]["name"].lower(), item[1]["entity_id"])))

    def settings_for(self, device_id: str, device: dict[str, Any]) -> dict[str, Any]:
        stored = self.data["devices"].get(device_id)
        return deepcopy(stored) if stored is not None else _defaults(device["model"], device["name"])

    def _editable(self, device_id: str, devices: dict[str, dict[str, Any]]) -> dict[str, Any]:
        if device_id not in devices:
            raise HomeAssistantError(f"ZHA Philips light is unavailable: {device_id}")
        if device_id not in self.data["devices"]:
            dev = devices[device_id]
            self.data["devices"][device_id] = _defaults(dev["model"], dev["name"])
        return self.data["devices"][device_id]

    async def save(self) -> None:
        async with self.write_lock:
            await self.store.async_save(self.data)

    def snapshot(self) -> dict[str, Any]:
        available = self.discover()
        return {
            "devices": [{**d, "settings": self.settings_for(device_id, d),
                         "online": self.hass.states.get(d["entity_id"]) is not None
                         and self.hass.states.get(d["entity_id"]).state not in ("unavailable", "unknown")}
                        for device_id, d in available.items()],
            "selection": [id_ for id_ in self.data["selection"] if id_ in available],
        }

    async def set_selection(self, device_ids: list[str]) -> None:
        available = self.discover()
        if any(i not in available for i in device_ids):
            raise HomeAssistantError("Unknown or non-Hue ZHA device in selection")
        self.data["selection"] = list(dict.fromkeys(device_ids))
        await self.save()

    async def set_preset(self, device_id: str, index: int, colors: list[str], name: str) -> None:
        devices = self.discover()
        settings = self._editable(device_id, devices)
        settings["presets"][index - 1] = {
            "name": name.strip() or f"Preset {index}",
            "colors": validate_colors(colors),
        }
        await self.save()

    async def set_config(self, device_id: str, update: dict[str, Any]) -> None:
        devices = self.discover()
        settings = self._editable(device_id, devices)
        for field in ("endpoint", "reverse", "mode", "interval", "auto"):
            if field in update:
                settings[field] = update[field]
        await self.save()
        if "auto" in update or ("interval" in update and settings["auto"]):
            self._stop_cycle(device_id)
            if settings["auto"]:
                self._start_cycle(device_id)

    async def copy_presets(self, source: str, targets: list[str]) -> None:
        devices = self.discover()
        if source not in devices or any(target not in devices for target in targets):
            raise HomeAssistantError("Source/target lamp not found")
        saved = self.settings_for(source, devices[source])["presets"]
        for target in targets:
            self._editable(target, devices)["presets"] = deepcopy(saved)
        await self.save()

    def _targets(self, device_ids: list[str] | None = None, entity_ids: list[str] | None = None) -> list[str]:
        available = self.discover()
        if device_ids is not None:
            targets = device_ids
        elif entity_ids is not None:
            ids = {d["entity_id"]: key for key, d in available.items()}
            invalid = [e for e in entity_ids if e not in ids]
            if invalid:
                raise HomeAssistantError(f"Not a registered ZHA Philips light: {', '.join(invalid)}")
            targets = [ids[e] for e in entity_ids]
        else:
            targets = self.data["selection"]
        targets = list(dict.fromkeys(targets))
        if not targets:
            raise HomeAssistantError("No Hue lights selected. Select lights in Gradient Studio first.")
        if any(i not in available for i in targets):
            raise HomeAssistantError("A selected lamp is no longer registered with ZHA")
        return targets

    async def control(self, action: str, *, device_ids: list[str] | None = None,
                      entity_ids: list[str] | None = None, preset: int | None = None,
                      enabled: bool | None = None) -> dict[str, Any]:
        available = self.discover()
        targets = self._targets(device_ids, entity_ids)
        successes: list[str] = []
        errors: dict[str, str] = {}
        for device_id in targets:
            dev = available[device_id]
            lock = self.locks.setdefault(device_id, asyncio.Lock())
            try:
                async with lock:
                    settings = self._editable(device_id, available)
                    if action == "auto":
                        settings["auto"] = bool(enabled)
                        await self.save()
                        self._stop_cycle(device_id)
                        if settings["auto"]:
                            self._start_cycle(device_id)
                    else:
                        if action == "next":
                            settings["active"] = settings["active"] % 4 + 1
                        elif action == "previous":
                            settings["active"] = (settings["active"] - 2) % 4 + 1
                        elif action == "apply" and preset is not None:
                            settings["active"] = preset
                        if action not in ("next", "previous", "apply"):
                            raise HomeAssistantError("Unsupported action")
                        await self.save()
                        await self._send(dev, settings)
                successes.append(dev["entity_id"])
            except Exception as err:  # continue targeting other lights
                _LOGGER.warning("Gradient command failed for %s: %s", dev["name"], err)
                errors[dev["entity_id"]] = str(err)
        return {"applied": successes, "errors": errors}

    async def _send(self, dev: dict[str, Any], settings: dict[str, Any]) -> None:
        colors = settings["presets"][settings["active"] - 1]["colors"]
        if settings["mode"] == "solid":
            rgb = tuple(int(colors[1][i : i + 2], 16) for i in (1, 3, 5))
            await self.hass.services.async_call(
                "light", "turn_on", {"entity_id": dev["entity_id"], "rgb_color": rgb}, blocking=True
            )
            return
        payload = encode_gradient(colors, settings["reverse"])
        if self.hass.states.is_state(dev["entity_id"], "off"):
            await self.hass.services.async_call(
                "light", "turn_on", {"entity_id": dev["entity_id"]}, blocking=True
            )
            await asyncio.sleep(0.35)
        await self.hass.services.async_call(
            "zha", "issue_zigbee_cluster_command", {
                "ieee": dev["ieee"],
                "endpoint_id": settings["endpoint"],
                "cluster_id": 0xFC03,
                "command": 0,
                "command_type": "server",
                "params": {"data": payload},
            }, blocking=True,
        )

    def _stop_cycle(self, device_id: str) -> None:
        task = self.tasks.pop(device_id, None)
        if task and task is not asyncio.current_task():
            task.cancel()

    def _start_cycle(self, device_id: str) -> None:
        if device_id in self.tasks:
            return
        self.tasks[device_id] = self.hass.async_create_task(self._cycle(device_id))

    async def _cycle(self, device_id: str) -> None:
        """Independent cycle per lamp; survives dashboard close and HA restart."""
        try:
            while True:
                settings = self.data["devices"].get(device_id)
                if not settings or not settings.get("auto"):
                    return
                await asyncio.sleep(max(MIN_INTERVAL, settings["interval"]))
                if not settings.get("auto"):
                    return
                result = await self.control("next", device_ids=[device_id])
                if result["errors"]:
                    _LOGGER.debug("Auto gradient failed: %s", result["errors"])
        except asyncio.CancelledError:
            return
        finally:
            if self.tasks.get(device_id) is asyncio.current_task():
                self.tasks.pop(device_id, None)


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up the integration from Settings -> Devices & services."""
    await _ensure_setup(hass)
    return True


async def _ensure_setup(hass: HomeAssistant) -> None:
    """Initialize the manager and register actions once per Home Assistant instance."""
    if DOMAIN in hass.data:
        return
    manager = GradientManager(hass)
    await manager.initialize()
    hass.data[DOMAIN] = manager

    # HACS only deploys files under custom_components; the bundled card gets
    # its own static path and is registered automatically in Lovelace storage mode.
    try:
        from homeassistant.loader import async_get_integration
        integration = await async_get_integration(hass, DOMAIN)
        await async_setup_frontend(hass, integration.version or "0.1.0")
    except Exception:
        _LOGGER.exception("Cannot serve Gradient Studio card; backend services remain available")

    action_schema = vol.Schema({
        vol.Optional("entity_id"): cv.entity_ids,
        vol.Optional("preset"): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
    })
    auto_schema = vol.Schema({
        vol.Optional("entity_id"): cv.entity_ids,
        vol.Required("enabled"): cv.boolean,
    })

    async def handle(call: ServiceCall) -> None:
        targets = call.data.get("entity_id")
        if targets is not None:
            targets = list(targets) if not isinstance(targets, str) else [targets]
        result = await manager.control(
            "auto" if call.service == "set_auto" else call.service, entity_ids=targets,
            preset=call.data.get("preset"), enabled=call.data.get("enabled"),
        )
        if result["errors"]:
            raise HomeAssistantError("Gradient errors: " + "; ".join(f"{k}: {v}" for k, v in result["errors"].items()))

    for action in ("apply", "next", "previous"):
        hass.services.async_register(DOMAIN, action, handle, schema=action_schema)
    hass.services.async_register(DOMAIN, "set_auto", handle, schema=auto_schema)

    websocket_api.async_register_command(hass, ws_list)
    websocket_api.async_register_command(hass, ws_select)
    websocket_api.async_register_command(hass, ws_save_preset)
    websocket_api.async_register_command(hass, ws_configure)
    websocket_api.async_register_command(hass, ws_control)
    websocket_api.async_register_command(hass, ws_copy)
    return None


def _manager(hass: HomeAssistant) -> GradientManager:
    return hass.data[DOMAIN]


def _error(connection: websocket_api.ActiveConnection, msg: dict, err: Exception) -> None:
    connection.send_error(msg["id"], "gradient_error", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/list"})
@websocket_api.async_response
async def ws_list(hass, connection, msg) -> None:
    connection.send_result(msg["id"], _manager(hass).snapshot())


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/select",
    vol.Required("device_ids"): [cv.string],
})
@websocket_api.async_response
async def ws_select(hass, connection, msg) -> None:
    try:
        await _manager(hass).set_selection(msg["device_ids"])
        connection.send_result(msg["id"], {"ok": True})
    except (ValueError, HomeAssistantError) as err:
        _error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_preset",
    vol.Required("device_id"): cv.string,
    vol.Required("preset"): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
    vol.Required("colors"): [cv.string],
    vol.Required("name"): vol.All(cv.string, vol.Length(max=48)),
})
@websocket_api.async_response
async def ws_save_preset(hass, connection, msg) -> None:
    try:
        await _manager(hass).set_preset(msg["device_id"], msg["preset"], msg["colors"], msg["name"])
        connection.send_result(msg["id"], {"ok": True})
    except (ValueError, HomeAssistantError) as err:
        _error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/configure",
    vol.Required("device_id"): cv.string,
    vol.Optional("endpoint"): vol.All(vol.Coerce(int), vol.Range(min=1, max=240)),
    vol.Optional("reverse"): cv.boolean,
    vol.Optional("mode"): vol.In(("gradient", "solid")),
    vol.Optional("interval"): vol.All(vol.Coerce(int), vol.Range(min=MIN_INTERVAL, max=MAX_INTERVAL)),
    vol.Optional("auto"): cv.boolean,
})
@websocket_api.async_response
async def ws_configure(hass, connection, msg) -> None:
    try:
        await _manager(hass).set_config(msg["device_id"], msg)
        connection.send_result(msg["id"], {"ok": True})
    except (ValueError, HomeAssistantError) as err:
        _error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/control",
    vol.Required("action"): vol.In(("apply", "next", "previous", "auto")),
    vol.Optional("device_ids"): [cv.string],
    vol.Optional("preset"): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
    vol.Optional("enabled"): cv.boolean,
})
@websocket_api.async_response
async def ws_control(hass, connection, msg) -> None:
    try:
        result = await _manager(hass).control(
            msg["action"], device_ids=msg.get("device_ids"),
            preset=msg.get("preset"), enabled=msg.get("enabled"),
        )
        connection.send_result(msg["id"], result)
    except (ValueError, HomeAssistantError) as err:
        _error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/copy",
    vol.Required("source"): cv.string,
    vol.Required("targets"): [cv.string],
})
@websocket_api.async_response
async def ws_copy(hass, connection, msg) -> None:
    try:
        await _manager(hass).copy_presets(msg["source"], msg["targets"])
        connection.send_result(msg["id"], {"ok": True})
    except (ValueError, HomeAssistantError) as err:
        _error(connection, msg, err)
