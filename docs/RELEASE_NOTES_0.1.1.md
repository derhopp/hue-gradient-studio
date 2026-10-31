## Hue Gradient Studio 0.1.1

Streamlined HACS installation and UI setup.

- Removed YAML-only integration setup and obsolete compatibility registration.
- Removed the historic preset importer from backend, WebSocket API, and dashboard card.
- Removed old-installation migration and upgrade instructions from documentation.
- Retained per-light presets, ZHA control, dashboard color pickers, preset copying, services, and automatic cycling.
- Simplified Lovelace resource-mode handling to the current Home Assistant API.
- Extended tests to verify that UI setup remains functional and legacy entry points are absent.

**Installation:** Install or update through HACS and restart Home Assistant. Set up the integration through **Settings → Devices & services → Add integration**.
