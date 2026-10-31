"""Minimal mocked Home Assistant integration exercise; no HA installation needed.

This tests API and state flow, not real ZHA hardware behaviour.
"""
import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def module(name, **values):
    m = types.ModuleType(name)
    m.__dict__.update(values)
    sys.modules[name] = m
    return m


def identity_decorator(*args, **kwargs):
    return lambda f: f


class AnySchema:
    def __init__(self, *args, **kwargs):
        pass


def optional(value, **kwargs): return value


vol = module('voluptuous', Schema=AnySchema, Optional=optional, Required=optional,
             Any=lambda *a:a, All=lambda *a:a, Coerce=lambda x:x, Range=lambda **k:None,
             Length=lambda **k:None, In=lambda v:v, ALLOW_EXTRA=1)
module('homeassistant')
module('homeassistant.components')
module('homeassistant.components.http', StaticPathConfig=lambda *a: a)
module('homeassistant.components.websocket_api', websocket_command=identity_decorator,
       require_admin=lambda f:f, async_response=lambda f:f, async_register_command=lambda *a:None, ActiveConnection=object)
module('homeassistant.const', EVENT_HOMEASSISTANT_STOP='stop', EVENT_HOMEASSISTANT_STARTED='start')
module('homeassistant.core', HomeAssistant=object, ServiceCall=object, CoreState=SimpleNamespace(running='running'), callback=lambda f:f)
class HomeAssistantError(Exception): pass
module('homeassistant.exceptions', HomeAssistantError=HomeAssistantError)
module('homeassistant.helpers')
module('homeassistant.helpers.config_validation', entity_ids=lambda x:x, string=str, boolean=bool)
device_module = module('homeassistant.helpers.device_registry', CONNECTION_ZIGBEE='zigbee')
entity_module = module('homeassistant.helpers.entity_registry')
class Store:
    _value = None
    def __init__(self, *args): pass
    async def async_load(self): return self._value
    async def async_save(self, data): self._value = data
module('homeassistant.helpers.storage', Store=Store)

async def fake_get_integration(hass, domain):
    import json
    manifest_path = ROOT / 'custom_components' / 'hue_gradient_studio' / 'manifest.json'
    return SimpleNamespace(version=json.loads(manifest_path.read_text())['version'])

module('homeassistant.loader', async_get_integration=fake_get_integration)

integration = importlib.import_module('custom_components.hue_gradient_studio')


class StateStore:
    def __init__(self):
        self.val = {
            'light.signe':SimpleNamespace(state='off'),
            'light.color':SimpleNamespace(state='on'),
        }
    def get(self, entity_id): return self.val.get(entity_id)
    def is_state(self, entity_id, value): return self.val.get(entity_id, SimpleNamespace(state=None)).state == value


class FakeServices:
    def __init__(self): self.calls=[]
    async def async_call(self,domain,service,data,blocking=False):
        self.calls.append((domain,service,data,blocking))
    def async_register(self,*args,**kwargs): pass


class TestManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        dev_signe = SimpleNamespace(id='dev_signe',manufacturer='Signify Netherlands B.V.',
            model='915005986901', name='Hue Signe gradient table lamp',name_by_user=None,
            identifiers={('zha','00:17:88:01:0D:FE:86:95')},connections=set())
        dev_color = SimpleNamespace(id='dev_color',manufacturer='Philips',
            model='LCA001',name='Hue color',name_by_user=None,
            identifiers={('zha','00:17:88:01:11:22:33:44')},connections=set())
        devices={'dev_signe':dev_signe,'dev_color':dev_color}
        entries={
            'light.signe':SimpleNamespace(domain='light',platform='zha',disabled_by=None,device_id='dev_signe',entity_id='light.signe'),
            'light.color':SimpleNamespace(domain='light',platform='zha',disabled_by=None,device_id='dev_color',entity_id='light.color'),
        }
        device_module.async_get=lambda hass:SimpleNamespace(async_get=devices.get)
        entity_module.async_get=lambda hass:SimpleNamespace(entities=entries)
        self.hass=SimpleNamespace(
            services=FakeServices(),states=StateStore(),data={},
            bus=SimpleNamespace(async_listen_once=lambda *a:None),
            async_create_task=lambda coro:asyncio.create_task(coro)
        )
        self.manager=integration.GradientManager(self.hass)
        await self.manager.initialize()

    async def asyncTearDown(self):
        self.manager._on_stop(None)
        await asyncio.sleep(0)

    async def test_ui_setup_registers_resource_once(self):
        class Resources:
            loaded = True
            def __init__(self): self.rows = []
            def async_items(self): return self.rows
            async def async_create_item(self, data):
                self.rows.append({'id': len(self.rows) + 1, 'url': data['url'], 'type': data['res_type']})
            async def async_update_item(self, index, data):
                self.rows[index - 1].update({'url': data['url'], 'type': data['res_type']})

        class HTTP:
            def __init__(self): self.static_paths = []
            async def async_register_static_paths(self, paths): self.static_paths.extend(paths)

        self.hass.http = HTTP()
        self.hass.state = 'running'
        resources = Resources()
        self.hass.data['lovelace'] = SimpleNamespace(resource_mode='storage', resources=resources)

        self.assertFalse(hasattr(integration, 'async_setup'))
        self.assertTrue(await integration.async_setup_entry(self.hass, SimpleNamespace()))
        await asyncio.sleep(0)
        self.assertEqual(len(self.hass.http.static_paths), 1)
        self.assertEqual(len(resources.rows), 1)
        version = (await fake_get_integration(self.hass, 'hue_gradient_studio')).version
        self.assertEqual(resources.rows[0]['url'], '/hue-gradient-studio/hue-gradient-studio.js?v=' + version)

        manager = self.hass.data['hue_gradient_studio']
        self.assertTrue(await integration.async_setup_entry(self.hass, SimpleNamespace()))
        self.assertIs(self.hass.data['hue_gradient_studio'], manager)
        self.assertEqual(len(self.hass.http.static_paths), 1)
        manager._on_stop(None)

    async def test_discovery_and_independent_presets(self):
        devices=self.manager.discover()
        self.assertEqual(len(devices),2)
        self.assertEqual(self.manager.settings_for('dev_signe',devices['dev_signe'])['mode'],'gradient')
        self.assertEqual(self.manager.settings_for('dev_color',devices['dev_color'])['mode'],'solid')
        await self.manager.set_selection(['dev_signe','dev_color'])
        await self.manager.set_preset('dev_signe',1,['#FF0000','#00FF00','#0000FF'],'Meine Farben')
        self.assertEqual(self.manager.settings_for('dev_signe',devices['dev_signe'])['presets'][0]['name'],'Meine Farben')
        self.assertNotEqual(self.manager.settings_for('dev_color',devices['dev_color'])['presets'][0]['name'],'Meine Farben')
        result=await self.manager.control('apply',preset=1)
        self.assertEqual(set(result['applied']),{'light.signe','light.color'})
        self.assertEqual(result['errors'],{})
        calls=self.hass.services.calls
        self.assertTrue(any(domain=='zha' and data['ieee']=='00:17:88:01:0D:FE:86:95' and data['endpoint_id']==11 for domain,_,data,_ in calls))
        self.assertTrue(any(domain=='light' and data.get('rgb_color') for domain,_,data,_ in calls))
        next_result=await self.manager.control('next',device_ids=['dev_signe'])
        self.assertFalse(next_result['errors'])
        self.assertEqual(self.manager.data['devices']['dev_signe']['active'],2)
        await self.manager.control('previous',device_ids=['dev_signe'])
        self.assertEqual(self.manager.data['devices']['dev_signe']['active'],1)

    async def test_auto_and_copy(self):
        await self.manager.set_selection(['dev_signe'])
        await self.manager.control('auto',enabled=True)
        self.assertTrue(self.manager.data['devices']['dev_signe']['auto'])
        self.assertIn('dev_signe',self.manager.tasks)
        await self.manager.control('auto',enabled=False)
        self.assertFalse(self.manager.data['devices']['dev_signe']['auto'])
        self.assertNotIn('dev_signe',self.manager.tasks)
        await self.manager.set_preset('dev_signe',1,['#111111','#222222','#333333'],'Test')
        await self.manager.copy_presets('dev_signe',['dev_color'])
        self.assertEqual(self.manager.data['devices']['dev_color']['presets'][0]['name'],'Test')


if __name__ == '__main__': unittest.main()
