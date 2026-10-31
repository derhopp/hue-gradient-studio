## Hue Gradient Studio 0.1.0

First GitHub/HACS-ready release, based on the working multi-light v3.0.1 proof of concept.

- Supports multiple Philips/Signify ZHA lights, four independent three-color presets per light.
- UI color pickers, selection and individual automatic preset switching.
- Retains the v3.0.1 WebSocket admin authorization fix.
- Bundles the dashboard JavaScript in the integration so it is updated together with the Python backend.
- Adds setup from **Settings → Devices & services → Add integration**, while keeping existing `hue_gradient_studio: {}` YAML configurations working.
- Automatically registers the dashboard resource in Lovelace storage mode.
- Existing `.storage/hue_gradient_studio` data is retained; no manual migration is performed.

### Upgrading from the v3.0.1 ZIP

1. Create a Home Assistant backup.
2. Install this repository via HACS as a custom **Integration**, restart Home Assistant.
3. Remove the obsolete `/local/hue-gradient-studio.js?v=3` entry from **Settings → Dashboards → Resources** if present.
4. Existing dashboard tabs using `custom:hue-gradient-studio` continue to work.
5. Optionally add the integration via **Settings → Devices & services → Add integration**. Then remove the old YAML entry and restart.

No change to the Zigbee encoding, stored presets, existing service names or custom card type is intended.
