# Hue Gradient Studio — HACS Integration

> **Version 0.1.0** · Custom integration for Home Assistant **ZHA** with a bundled Lovelace color-gradient editor. This GitHub release is based on the previously working v3.0.1 multi-light prototype.

Hue Gradient Studio stores **four individually editable three-color presets per Philips/Signify light**. The dashboard offers color pickers, multi-light selection, preset sharing, and manual or timed preset changes. Everything uses the existing ZHA connection; no Hue Bridge or Zigbee2MQTT is required.

**Scope and limitations:** Works with Hue lights paired through **ZHA**, not Hue Bridge lights. A true three-color gradient requires a compatible Hue gradient lamp; normal Hue color bulbs show only the middle preset color. The Philips-specific `0xFC03` Zigbee command is model-dependent. Test each new gradient-capable model individually, verify its endpoint, and use **Solid color** for unsupported models. No hardware-wide compatibility is promised.

## Install from your own GitHub repository via HACS

1. Publish this repository to GitHub (see [PUBLISHING.md](docs/PUBLISHING.md)). The repository must be public for ordinary HACS custom-repository use.
2. Home Assistant: **HACS → ⋮ → Custom repositories** (or the corresponding menu in your HACS version).
3. Enter `https://github.com/derhopp/hue-gradient-studio` and select category **Integration**; click **Add**.
4. Open **HACS**, locate **Hue Gradient Studio**, and choose **Download** (version `0.1.0`).
5. Restart Home Assistant: **Settings → System → Restart**.
6. New installations: **Settings → Devices & services → Add integration**, search **Hue Gradient Studio** and finish the one-step setup. ZHA must already be configured.
7. For an existing dashboard, use **Edit dashboard → + (new view/tab) → Edit view → ⋮ → Edit in YAML** and paste [docs/view-only.yaml](docs/view-only.yaml). The existing dashboard views remain untouched.

**Included in HACS updates:** Python backend, `services.yaml`, translations, and the **`hue-gradient-studio.js`** card. HACS installs everything within `custom_components/hue_gradient_studio/`. **Do not copy a JS file to `/config/www` for new installs.** In storage-mode dashboards the integration automatically creates/updates the Lovelace module resource at `/hue-gradient-studio/hue-gradient-studio.js?v=0.1.0`. Reload the browser after installing or updating.

If your Lovelace configuration uses `resource_mode: yaml`, add the resource manually in `configuration.yaml` (UI resource registration cannot modify YAML-mode resources):

```yaml
lovelace:
  resource_mode: yaml
  resources:
    - url: /hue-gradient-studio/hue-gradient-studio.js?v=0.1.0
      type: module
```

For storage mode, the fallback manual path is **Settings → Dashboards → ⋮ → Resources → Add resource**, URL `/hue-gradient-studio/hue-gradient-studio.js?v=0.1.0`, type **JavaScript Module**. Normally this is unnecessary: if the resource has not appeared shortly after startup, check **Settings → System → Logs** before adding it yourself. If the dashboard displays **Custom element doesn't exist: hue-gradient-studio**, check this resource URL and type, then reload the browser. Avoid duplicate resource entries.

## Upgrade from the original manually installed v3.0.1

1. **Create a Home Assistant backup** (including `.storage`) before replacing custom-component files.
2. Add the GitHub repository to HACS and install v0.1.0. HACS will manage the same `/config/custom_components/hue_gradient_studio/` directory. **Do not delete this directory before the HACS install** and **do not delete `.storage/hue_gradient_studio`**.
3. Restart Home Assistant. Your stored selections, four presets per lamp, and automatic settings will be loaded from the existing storage file. The integration domain and service names are unchanged.
4. In **Settings → Dashboards → ⋮ → Resources**, **remove the obsolete** `/local/hue-gradient-studio.js?v=3` resource. The old file in `/config/www/` can be deleted *later*, after checking the new version. The old resource may otherwise win the custom-element registration race and hide future frontend updates.
5. Your existing tab that uses `type: custom:hue-gradient-studio` **stays exactly as it is**; no dashboard re-import is required. Hard-refresh the browser (on macOS Safari, close/reopen the tab or clear site cache).
6. To migrate from **legacy YAML setup** to UI setup: go to **Settings → Devices & services → Add integration → Hue Gradient Studio** and complete the setup. Then **remove only** the `hue_gradient_studio: {}` line from `configuration.yaml`, check the configuration, and restart Home Assistant. This does *not* remove your saved presets. Alternatively, leave the YAML line in place: v0.1.0 supports it for compatibility. Do **not** remove your `homeassistant:` or unrelated dashboard configuration.

## Usage

After selecting lights in the Gradient Studio dashboard, you can call these actions from **Developer tools → Actions** or from a Hue Dimmer V2 automation:

```yaml
# Switch to the next preset for all selected lights
- action: hue_gradient_studio.next

# Set preset 2 for the saved selection
- action: hue_gradient_studio.apply
  data:
    preset: 2

# Set a preset on a specific ZHA light, bypassing the dashboard selection
- action: hue_gradient_studio.apply
  data:
    entity_id: light.philips_hue_schreibtisch
    preset: 3

# Start automatic cycling for the saved selection
- action: hue_gradient_studio.set_auto
  data:
    enabled: true
```

These are **examples for the `actions:` section of a Home Assistant automation**. In **Developer tools → Actions**, use a single action at a time without the leading `-`. See [docs/example_automations.yaml](docs/example_automations.yaml).

## Compatibility and upgrades

- Requires **Home Assistant 2025.7 or newer** and ZHA.
- Every HACS release should have a published GitHub **Release** with a tag matching `manifest.json` (`0.1.0`, then `0.1.1`, ...). A Git tag without an actual GitHub Release is not sufficient for proper HACS version tracking.
- HACS updates the code; you must **restart Home Assistant** to load new Python code. The dashboard JS is updated with the same release and versioned resource URL.
- Storage is under `/config/.storage/hue_gradient_studio`, managed by Home Assistant. **Do not add `.storage` to the GitHub repository and do not edit it manually.**
- `services.yaml` actions: `hue_gradient_studio.apply`, `.next`, `.previous`, `.set_auto`.
- The UI is an optional bundled dashboard custom card, not a separate HACS Dashboard plugin.
- If a lamp is not listed: check that it is a light device whose integration is ZHA and manufacturer contains Philips or Signify, and that it is enabled.

## For the repository owner

Follow **[docs/PUBLISHING.md](docs/PUBLISHING.md)** for a complete macOS Terminal/GitHub CLI walkthrough: replacing GitHub owner placeholders, creating the public repository, pushing `main`, publishing release `0.1.0`, testing HACS, and publishing future versions.

For the official HACS catalog (rather than a custom repository), additional publisher requirements may apply, such as Home Assistant Brands. Listing in the catalog is **not** required to install or update this repository as a HACS custom integration. See [HACS integration publishing rules](https://hacs.dev/docs/publish/integration/).

## Tests

```bash
python3 -m compileall -q custom_components tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --check custom_components/hue_gradient_studio/frontend/hue-gradient-studio.js
node tests/test_ui.cjs
```

These are offline smoke tests, not a live test against your installed Home Assistant/Zigbee hardware.

## License

MIT license. See [LICENSE](LICENSE).
