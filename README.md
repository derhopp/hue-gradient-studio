# Hue Gradient Studio

**HACS custom integration for Home Assistant ZHA** — configure, save and switch color-gradient presets on Philips Hue lights. Current integration version: **0.1.3**.

> [!IMPORTANT]
> **AI-GENERATED / AI-ASSISTED SOFTWARE — UNOFFICIAL PROJECT**
>
> Substantial parts of this integration's Python code, JavaScript code, tests, and documentation were developed with **OpenAI ChatGPT**. This is an experimental, independently maintained community project, **not official software** from Philips, Signify, Home Assistant, HACS, or their affiliated organizations.
>
> AI-generated software may contain bugs, has not been independently security-audited, and has not been comprehensively tested with every Home Assistant version or Philips Hue light model. Review the source code and use it at your own risk.

The integration uses the existing **Zigbee Home Automation (ZHA)** network. It requires **no Hue Bridge** and does not use Zigbee2MQTT. It provides four editable three-color presets **per lamp**; you can manage multiple lamps and control them from the dashboard, scripts, automations, or a Zigbee remote.

## Language support

The integration supports **English and German only**. Its dashboard card follows your **Home Assistant user-interface language** automatically:

- **German** (`de`, `de-DE`, `de-AT`, `de-CH`): German buttons, labels, descriptions and messages.
- **English** (`en`, `en-US`, `en-GB`): English UI.
- **Other interface languages**: English fallback; no additional translations are shipped.

Set the language in your Home Assistant **user profile**. The card reflects language changes without deleting presets or modifying their user-defined names. Home Assistant setup and action descriptions have English and German translations as well.

## What it does

| Feature | Behavior |
|---|---|
| Lamp discovery | Finds enabled Philips/Signify light entities paired through ZHA |
| Gradient presets | Four named presets **per lamp**, each with three editable colors |
| Editor | Three color pickers (top, middle, bottom), HEX inputs and a gradient preview |
| Multiple lamps | Select a group of lamps for control without losing their individual presets |
| Save and apply | Save preset data independently from sending a command to a lamp |
| Copy | Copy all four presets from one lamp to other selected lamps |
| Preset switching | Previous / apply current / next, including Home Assistant actions |
| Automatic cycling | Per-lamp switching at a configurable interval; works without an open dashboard |
| Standard Hue color bulbs | Solid-color mode uses the middle preset color instead of a multi-zone gradient |

**Compatibility:** True three-color output uses a Philips-specific Zigbee command on cluster `0xFC03`. Only compatible Hue Gradient models can display multiple colors simultaneously. The tested **Hue Signe Gradient table lamp** uses endpoint **11**; that endpoint is **not guaranteed to work on other models**. Test with one lamp first. For a lamp without genuine Gradient support, choose **Solid color (middle color)**.

### Prerequisites

- Home Assistant with **ZHA** configured
- Compatible Philips/Signify lights paired with **ZHA**, not through the Hue Bridge or Zigbee2MQTT
- **HACS** for installation and updates
- A Home Assistant **administrator** account to configure the integration

## Install with HACS

1. Open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/derhopp/hue-gradient-studio` as category **Integration**.
3. Open **Hue Gradient Studio → Download** in HACS.
4. Restart Home Assistant: **Settings → System → Restart**.
5. Open **Settings → Devices & services → Add integration**, find **Hue Gradient Studio**, and finish setup.
6. Confirm it appears in **Settings → Devices & services → Integrations**.

The integration bundles the Lovelace JavaScript card. In **storage resource mode**, it registers the following **JavaScript Module** automatically:

```text
/hue-gradient-studio/hue-gradient-studio.js?v=0.1.3
```

If the card does not load, see [Troubleshooting](#troubleshooting) before adding any duplicate resources.

### Add a card to an existing dashboard

In your existing dashboard, click **Edit dashboard → Add card → Manual** and paste:

```yaml
type: custom:hue-gradient-studio
title: Hue Gradient Studio
```

This only adds one card. Other cards and tabs remain untouched.

### Add a new dashboard tab

Use **Edit dashboard → Add view/tab** to create a view. Open the new tab's **View configuration → Edit in YAML** and paste the contents of [docs/view-only.yaml](docs/view-only.yaml).

> **Do not paste** `docs/view-only.yaml` into the dashboard's global **Raw configuration editor** to replace its contents. The file describes **one view only**; replacing the entire dashboard YAML would remove your other tabs.

## Using the dashboard: step by step

### 1. Select your control group

At **"1. Select lights"**, each checkbox adds or removes a lamp from the **saved control selection**. This selection is also used by Home Assistant actions when no specific `entity_id` is supplied.

The buttons above the editor act on **all selected lamps**:

| Dashboard button | What happens |
|---|---|
| **"Previous (selection)"** | Each selected lamp moves to its previous preset (1 → 4 → 3 → 2 → 1) |
| **"Apply current (selection)"** | Re-applies each selected lamp's **currently active** preset |
| **"Next (selection)"** | Each selected lamp moves to its next preset (1 → 2 → 3 → 4 → 1) |

**The selected lamps do not need to share the same colors or active preset.** A group command operates independently on each lamp.

### 2. Choose which lamp to edit

In **"2. Edit presets for a light"**, use the dropdown **"Light to edit"**.

- This dropdown controls **which lamp's preset definitions and settings are shown**.
- It **does not** automatically tick or untick that lamp in the group selection.
- You can edit one lamp while controlling several others from the selected group.

### 3. Set the lamp's mode and options

| Setting in the card | Purpose |
|---|---|
| **"Control mode" → "Three-color gradient (ZHA)"** | Send the proprietary multi-color Gradient command (supported models only) |
| **"Control mode" → "Solid color (middle)"** | Use the preset's **middle** color as an ordinary RGB light command |
| **"Zigbee endpoint"** | Device-specific Zigbee endpoint for the Gradient command; **11** worked for a Hue Signe table lamp |
| **"Color order"** | Reverse or retain the order in which gradient colors are sent |
| **"Auto interval (seconds)"** | Time between automatic preset changes; **30–3600 seconds** |
| **"Automatic cycling"** | Turn automatic cycling on/off for the lamp currently being edited |

After changing these options, click **"Save settings"**. Changing a dropdown or number alone does **not** save these device settings.

**Safety tip:** If you don't know whether a lamp supports proprietary Gradient commands or which endpoint it uses, start with **Solid color (middle)**. A normal Hue bulb can show only one color at a time.

### 4. Create and save the four presets

Every lamp has **Preset 1**, **Preset 2**, **Preset 3** and **Preset 4**. Each has:

- A name
- **"Top"** — first color
- **"Middle"** — middle color
- **"Bottom"** — third color
- A preview showing the intended arrangement

Set colors using the color pickers or HEX values such as `#FF5722`, `#FFB347` and `#6633C8`.

Each preset offers three different actions:

| Button | What it does |
|---|---|
| **"Save"** | Stores this preset's name and colors; **does not change lamp output** |
| **"Apply to this light"** | Saves unsaved changes to this preset (if any), then sends it to the **editing lamp** (even if not checked above) |
| **"Apply to selection"** | Applies this **preset number** to all checked lamps, using **each lamp's own saved colors**; does not copy the editing lamp's draft colors |

For example, suppose **Signe A** has blue–cyan–green in **Preset 2**, while **Signe B** has red–orange–yellow in **Preset 2**. Click **"Apply to selection"** in the Preset 2 panel with both lamps selected: **A shows its blue gradient; B shows its red gradient**.

**Unsaved edits:** Save a preset before applying it to the group. Group actions use each lamp's previously saved preset data.

### 5. Copy presets between lamps

To make multiple lamps share the same four preset definitions:

1. Set up and **save** the four presets on your source lamp.
2. Select the **target lamps** with the checkboxes under **"1. Select lights"**.
3. In **"Light to edit"**, choose the **source lamp**.
4. Click **"Copy all 4 presets from this light to selection"**.
5. Confirm the overwrite.

This **replaces all four stored presets** on the checked target lamps (excluding the source lamp). It does **not** automatically apply those presets; use **"Apply to selection"** or **"Apply current (selection)"** afterwards.

### 6. Enable automatic switching

There are two ways to enable automatic preset cycling:

- **One lamp:** Choose it in **"Light to edit"**, set **"Auto interval (seconds)"** (30–3600), choose **"Automatic cycling" → "On"**, then click **"Save settings"**.
- **Selected group:** Use **"Enable automatic cycling for selection"** or **"Disable automatic cycling for selection"** at the bottom of the card. Every checked lamp retains its own saved interval.

The integration cycles each enabled lamp independently through Preset 1–4. This runs inside Home Assistant; **the browser/dashboard does not need to remain open**. Cycling settings are persisted and resumed after Home Assistant restarts.

## Actions for scripts, automations and remote buttons

You can call these from **Developer tools → Actions** or a Home Assistant automation/script.

**Important:** When `entity_id` is omitted, the integration uses the **saved selection from the dashboard**. Set `entity_id` to target particular lamps independently of that selection.

### Next / previous preset

```yaml
action: hue_gradient_studio.next
```

```yaml
action: hue_gradient_studio.previous
```

These switch each selected lamp to its next or previous saved preset.

### Apply a specific preset to the selection

```yaml
action: hue_gradient_studio.apply
data:
  preset: 2
```

This activates Preset 2 on each selected lamp, with its **own** stored colors.

To re-apply the current preset instead, omit `preset`:

```yaml
action: hue_gradient_studio.apply
```

### Target one lamp (or several) explicitly

```yaml
action: hue_gradient_studio.apply
data:
  entity_id: light.example_hue_gradient
  preset: 3
```

For multiple lamps, provide an entity ID list:

```yaml
action: hue_gradient_studio.next
data:
  entity_id:
    - light.example_hue_gradient_1
    - light.example_hue_gradient_2
```

Replace the example entity IDs with those shown in **Developer tools → States**.

### Start or stop automatic cycling

```yaml
action: hue_gradient_studio.set_auto
data:
  enabled: true
```

```yaml
action: hue_gradient_studio.set_auto
data:
  enabled: false
```

Both act on the saved selection unless you provide `entity_id`.

### Philips Hue Dimmer Switch V2 (RWL022)

If you already have a working ZHA automation or blueprint for the dimmer, attach the next-preset action to its **Hue button short press** action:

```yaml
- action: hue_gradient_studio.next
```

This is an **action inside an existing automation or blueprint configuration**, not a complete standalone automation. How button events are triggered depends on your chosen remote blueprint or ZHA device triggers.

See [more automation examples](docs/example_automations.yaml).

## Storage, upgrades and limitations

- Presets, per-lamp configuration and saved multi-selection are stored in Home Assistant under `/config/.storage/hue_gradient_studio`. **Do not edit or commit this storage file.** Back up Home Assistant regularly.
- Install new versions via **HACS → Hue Gradient Studio → Update** and restart Home Assistant.
- The card is delivered with the integration, not as a separate HACS dashboard package.
- Colors are encoded for supported Gradient models using vendor-specific ZHA commands. Correct operation is **model- and endpoint-dependent**.
- The project is **AI-generated/AI-assisted experimental community software**; automated tests and individual successful device tests do not guarantee operation on every Hue lamp or Home Assistant version.

## Troubleshooting

| Problem | Check |
|---|---|
| **Custom element doesn't exist: hue-gradient-studio** | Under **Settings → Dashboards → ⋮ → Resources**, check the module resource `/hue-gradient-studio/hue-gradient-studio.js?v=0.1.3`; avoid duplicates, inspect **Settings → System → Logs**, then reload the browser |
| Card opens but no lamps are listed | Make sure the lamps are enabled, connected to **ZHA** and reported as Philips/Signify |
| Pressing a button affects the wrong lamps | Check the **checkbox selection**; the edit-lamp dropdown is separate |
| Changing a color does not change the lamp | Use **"Save"** to store the preset, then **"Apply to this light"** or **"Apply to selection"** to apply it |
| Only one color appears | Verify the lamp supports Gradient output and is in **Three-color gradient (ZHA)** mode; standard Hue color bulbs use **Solid color (middle)** |
| Gradient is not applied | Verify the Zigbee endpoint, lamp compatibility, availability and ZHA logs; test one lamp first |
| Auto-cycling does not start | Check the lamp's **Automatic cycling** setting, saved interval, selected lamp(s), and **"Save settings"** |
| Integration not listed in Integrations | Complete **Settings → Devices & services → Add integration → Hue Gradient Studio** and restart Home Assistant |

If you can reproduce a problem, create a [GitHub issue](https://github.com/derhopp/hue-gradient-studio/issues) with your Home Assistant version, lamp model, ZHA endpoint, reproduction steps and relevant logs (remove personal network details/tokens first).

## Development and release process

The backend is in `custom_components/hue_gradient_studio/` and the card in its `frontend/` subfolder. See [publishing instructions](docs/PUBLISHING.md).

Available offline tests:

```bash
python3 -m compileall -q custom_components tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --check custom_components/hue_gradient_studio/frontend/hue-gradient-studio.js
node tests/test_ui.cjs
```

These tests do **not** replace live testing with actual Zigbee devices, security review, or testing across Home Assistant versions.

## Trademarks and independent-project notice

**Philips** (including the PHILIPS word mark) is a registered trademark of **Koninklijke Philips N.V.** The **Philips Hue** lighting brand is operated by **Signify** under license from Royal Philips; Hue and related marks are the property of their respective owners. **Home Assistant** and its logo are trademarks of the **Open Home Foundation**. Other names, including **HACS**, **ZHA**, **Zigbee**, **GitHub**, and **ChatGPT**, are referenced solely to identify their respective products, services, or standards; applicable trademark rights remain with their owners.

**Hue Gradient Studio is an independent, unofficial integration.** References to third-party brands describe intended compatibility only. Nothing in this repository claims sponsorship, authorization, certification, or endorsement by Koninklijke Philips N.V., Signify, the Open Home Foundation, HACS, GitHub, OpenAI, or other trademark holders.

Trademark references: [Philips trademark-use guidelines](https://www.philips.com/a-w/about/innovation/ips/philips-general-trademark-use-guidelines) · [Philips Hue / Signify legal information](https://www.signify.com/content/hue/us/en/support/legal/privacy-policy.html) · [Home Assistant brand guidelines](https://contributors.home-assistant.io/brand/name-and-logo/).

## License

MIT License — see [LICENSE](LICENSE).
