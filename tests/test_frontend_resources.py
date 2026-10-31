"""Regression tests for resource registration without a running HA instance."""

import asyncio
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch


FILE = (
    Path(__file__).resolve().parents[1]
    / "custom_components/hue_gradient_studio/frontend_resources.py"
)


def _load_frontend_module():
    components = ModuleType("homeassistant.components")
    ha = ModuleType("homeassistant")
    http = ModuleType("homeassistant.components.http")
    const = ModuleType("homeassistant.const")
    core = ModuleType("homeassistant.core")

    http.StaticPathConfig = lambda *args: args
    const.EVENT_HOMEASSISTANT_STARTED = "homeassistant_started"
    core.CoreState = SimpleNamespace(running="running")
    core.HomeAssistant = type("HomeAssistant", (), {})
    core.callback = lambda fn: fn

    modules = {
        "homeassistant": ha,
        "homeassistant.components": components,
        "homeassistant.components.http": http,
        "homeassistant.const": const,
        "homeassistant.core": core,
    }
    spec = importlib.util.spec_from_file_location(
        "hgs_frontend_resources_test", FILE
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class FakeResources:
    def __init__(self, items=None):
        self.loaded = False
        self.items = items or []
        self.info_calls = 0
        self.create_calls = 0
        self.update_calls = 0

    async def async_get_info(self):
        self.info_calls += 1
        self.loaded = True
        return {"resources": len(self.items)}

    def async_items(self):
        if not self.loaded:
            raise AssertionError("Resources read before storage loaded")
        return list(self.items)

    async def async_create_item(self, item):
        if not self.loaded:
            raise AssertionError("Resources created before storage loaded")
        self.create_calls += 1
        self.items.append(
            {"id": "new", "url": item["url"], "type": item["res_type"]}
        )

    async def async_update_item(self, item_id, item):
        self.update_calls += 1
        for old in self.items:
            if old["id"] == item_id:
                old.update(url=item["url"], type=item["res_type"])
                return
        raise KeyError(item_id)


class ResourceRegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.frontend = _load_frontend_module()
        self.tasks = []
        self.resources = FakeResources()
        self.hass = SimpleNamespace(
            state="running",
            data={
                "lovelace": SimpleNamespace(
                    resource_mode="storage", resources=self.resources
                )
            },
            http=SimpleNamespace(async_register_static_paths=AsyncMock()),
            async_create_task=self._schedule,
        )

    def _schedule(self, coroutine):
        self.tasks.append(asyncio.create_task(coroutine))

    async def _run(self):
        await self.frontend.async_setup_frontend(self.hass, "0.1.0")
        await asyncio.gather(*self.tasks)

    async def test_registers_module_in_storage_mode_after_lazy_load(self):
        await self._run()
        self.assertEqual(self.resources.info_calls, 1)
        self.assertEqual(self.resources.create_calls, 1)
        self.assertEqual(self.resources.items[0]["type"], "module")
        self.assertEqual(
            self.resources.items[0]["url"],
            "/hue-gradient-studio/hue-gradient-studio.js?v=0.1.0",
        )

    async def test_updates_existing_wrong_version_or_type(self):
        self.resources.items = [
            {
                "id": "old",
                "url": "/hue-gradient-studio/hue-gradient-studio.js?v=0.0.9",
                "type": "css",
            }
        ]
        await self._run()
        self.assertEqual(self.resources.update_calls, 1)
        self.assertEqual(self.resources.create_calls, 0)
        self.assertEqual(self.resources.items[0]["type"], "module")

    async def test_does_not_rewrite_valid_resource(self):
        self.resources.items = [
            {
                "id": "existing",
                "url": "/hue-gradient-studio/hue-gradient-studio.js?v=0.1.0",
                "type": "module",
            }
        ]
        await self._run()
        self.assertEqual(self.resources.update_calls, 0)
        self.assertEqual(self.resources.create_calls, 0)

    async def test_does_not_register_when_resource_mode_is_yaml(self):
        self.hass.data["lovelace"].resource_mode = "yaml"
        await self._run()
        self.assertEqual(self.resources.create_calls, 0)
        self.assertEqual(self.resources.update_calls, 0)


if __name__ == "__main__":
    unittest.main()
