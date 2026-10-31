# Hue Gradient Studio

**Version 0.1.1** — A HACS custom integration for controlling Philips Hue lights paired with **Zigbee Home Automation (ZHA)** in Home Assistant.

Hue Gradient Studio offers:

- Automatic discovery of eligible Philips/Signify ZHA lights
- Four persistent presets per light, with three editable colors each
- A dashboard card with color pickers, previews, multi-light selection and preset copying
- Individual or group controls, and timed automatic preset cycling
- Home Assistant actions for automations and remotes
- Bundled dashboard JavaScript, updated together with the integration via HACS

Compatible Hue Gradient models can receive proprietary Zigbee cluster `0xFC03` commands. On ordinary Hue color bulbs, select **Solid color** to apply the preset's middle color. Zigbee endpoints are device-specific; the Signe Gradient table lamp has been tested with endpoint 11. Not all Hue models support multi-zone gradients.

## Requirements

- Home Assistant with ZHA configured and Philips/Signify lights paired through ZHA
- HACS
- An administrator account to configure the integration

This integration uses ZHA directly. Hue Bridge and Zigbee2MQTT devices are not supported.

## Install with HACS

1. Open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/derhopp/hue-gradient-studio` with category **Integration**.
3. In HACS, open **Hue Gradient Studio → Download**.
4. Restart Home Assistant using **Settings → System → Restart**.
5. Go to **Settings → Devices & services → Add integration**, search for **Hue Gradient Studio**, and complete the setup.
6. Confirm that **Hue Gradient Studio** appears under **Settings → Devices & services → Integrations**.

The integration serves its own JavaScript card and registers `/hue-gradient-studio/hue-gradient-studio.js?v=0.1.1` as a Lovelace **JavaScript Module** in storage resource mode.

If your Lovelace resources are configured in YAML mode, include the resource in your existing Lovelace resources configuration:

```yaml
lovelace:
  resource_mode: yaml
  resources:
    - url: /hue-gradient-studio/hue-gradient-studio.js?v=0.1.1
      type: module
```

For storage mode, check **Settings → Dashboards → ⋮ → Resources** if the card does not appear. There should be one module resource for `/hue-gradient-studio/hue-gradient-studio.js?v=0.1.1`. Avoid duplicate resources and reload the dashboard after an update.

## Add the card to an existing dashboard

Open **Edit dashboard** and create or edit a tab. In its **View configuration → Edit in YAML** paste [docs/view-only.yaml](docs/view-only.yaml). This modifies only that tab; it does not replace the other views.

Alternatively, add a single **Manual card** using:

```yaml
type: custom:hue-gradient-studio
title: Hue Gradient Studio
```

The card offers lamp selection, four named three-color presets per lamp, per-lamp mode and Zigbee endpoint, preset copying, and automatic switching.

## Home Assistant actions

Select lights in the card, then use these actions through **Developer tools → Actions** or automations:

```yaml
# Next saved preset for the selected lamps
action: hue_gradient_studio.next
```

```yaml
# Apply preset 2 to selected lamps
action: hue_gradient_studio.apply
data:
  preset: 2
```

```yaml
# Apply preset 3 to a specific ZHA light
action: hue_gradient_studio.apply
data:
  entity_id: light.example_hue_gradient
  preset: 3
```

```yaml
# Enable timed switching for the selected lamps
action: hue_gradient_studio.set_auto
data:
  enabled: true
```

Available actions: `hue_gradient_studio.apply`, `.next`, `.previous`, and `.set_auto`. See [example automations](docs/example_automations.yaml).

## Settings and updates

Presets, active selections, and auto-cycle settings are stored by Home Assistant in `/config/.storage/hue_gradient_studio`. They are not stored in GitHub. Include Home Assistant configuration and storage in your backups.

Install updates in **HACS**, then restart Home Assistant. Home Assistant updates the JavaScript resource URL according to the integration version. Reopen or refresh your dashboard to load the current card.

To troubleshoot:

- **Custom element doesn't exist: hue-gradient-studio**: Verify the JavaScript Module under **Settings → Dashboards → ⋮ → Resources**, check **Settings → System → Logs**, and reload the browser.
- **No lights listed**: Confirm that the lamp is enabled, paired through ZHA, and has manufacturer Philips/Signify.
- **Gradient not applied**: Confirm the lamp supports multi-zone gradients, test its endpoint, or select **Solid color**.
- **Integration missing from Integrations**: Ensure setup was completed through **Settings → Devices & services → Add integration** and restart Home Assistant.

## Development and releases

The integration lives in `custom_components/hue_gradient_studio/` and its dashboard card is bundled under `frontend/`. See [publishing instructions](docs/PUBLISHING.md).

Run local tests:

```bash
python3 -m compileall -q custom_components tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --check custom_components/hue_gradient_studio/frontend/hue-gradient-studio.js
node tests/test_ui.cjs
```

These are offline tests; device behavior must also be verified with actual ZHA hardware.

## License

MIT — see [LICENSE](LICENSE).
