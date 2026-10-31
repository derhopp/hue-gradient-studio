# Hue Gradient Studio

**HACS custom integration for Home Assistant ZHA** — configure, save and switch color-gradient presets on Philips Hue lights. Current integration version: **0.1.1**.

> [!IMPORTANT]
> **AI-GENERATED SOFTWARE / MIT KI ERSTELLTE SOFTWARE**
>
> **Deutsch:** Diese Integration einschließlich wesentlicher Teile des Python- und JavaScript-Codes, der Tests und der Dokumentation wurde mithilfe der KI **OpenAI ChatGPT** entwickelt. Es handelt sich um ein experimentelles Community-Projekt, **nicht** um eine offizielle Integration von Philips, Signify, Home Assistant oder HACS. KI-generierter Code kann Fehler enthalten. Er wurde **nicht umfassend auf allen Hue-Modellen oder Home-Assistant-Versionen getestet oder unabhängig sicherheitsgeprüft**. Verwendung auf eigene Verantwortung.
>
> **English:** This integration — including substantial parts of its Python and JavaScript code, tests, and documentation — was developed using **OpenAI ChatGPT**. It is an experimental, AI-assisted community project, **not** an official Philips, Signify, Home Assistant, or HACS integration. AI-generated software can contain bugs; it has **not been independently security-audited or exhaustively hardware-tested**. Use it at your own risk.

The integration uses the existing **Zigbee Home Automation (ZHA)** network. It requires **no Hue Bridge** and does not use Zigbee2MQTT. It provides four editable three-color presets **per lamp**; you can manage multiple lamps and control them from the dashboard, scripts, automations, or a Zigbee remote.

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

**Compatibility:** True three-color output uses a Philips-specific Zigbee command on cluster \`0xFC03\`. Only compatible Hue Gradient models can display multiple colors simultaneously. The tested **Hue Signe Gradient table lamp** uses endpoint **11**; that endpoint is **not guaranteed to work on other models**. Test with one lamp first. For a lamp without genuine Gradient support, choose **Solid color (middle color)**.

### Prerequisites

- Home Assistant with **ZHA** configured
- Compatible Philips/Signify lights paired with **ZHA**, not through the Hue Bridge or Zigbee2MQTT
- **HACS** for installation and updates
- A Home Assistant **administrator** account to configure the integration

## Schnellstart (Deutsch)

1. In Home Assistant **HACS → ⋮ → Custom repositories** öffnen. Das Repository \`https://github.com/derhopp/hue-gradient-studio\` mit Kategorie **Integration** hinzufügen und Hue Gradient Studio über **Download** installieren.
2. Unter **Settings → System → Restart** Home Assistant neu starten.
3. **Settings → Devices & services → Add integration → Hue Gradient Studio** öffnen und die Einrichtung abschließen.
4. Im bestehenden Dashboard **Edit dashboard → Add card → Manual** wählen und folgenden Code einfügen:

   \`\`\`yaml
   type: custom:hue-gradient-studio
   title: Hue Gradient Studio
   \`\`\`

   **Wichtig:** Das ist eine **einzelne Karte**. Damit wird **kein bestehendes Dashboard und kein anderer Tab überschrieben**. Für einen eigenen Tab siehe [Add a new dashboard tab](#add-a-new-dashboard-tab).

5. Unter **„1. Lampen auswählen“** die zu steuernden Lampen anhaken. Für den ersten Test am besten nur **eine** unterstützte Gradient-Leuchte auswählen.
6. Unter **„2. Presets einer Lampe bearbeiten“** im Dropdown die gewünschte Lampe auswählen. Das ist die **Bearbeitungslampe**, unabhängig von den Häkchen oben.
7. Bei **Preset 1–4** den Namen und die drei Farben über die Colorpicker festlegen. Mit **„Speichern“** werden die Werte dauerhaft abgelegt, **aber noch nicht an die Lampe gesendet**.
8. **„Auf diese Lampe“** aktiviert das Preset auf der bearbeiteten Lampe. **„Auf Auswahl“** aktiviert bei jeder angehakten Lampe **deren eigenes Preset derselben Nummer**.
9. Über **„Nächste (Auswahl)“** und **„Vorherige (Auswahl)“** zwischen den gespeicherten Presets wechseln. Derselbe Wechsel ist über die Action \`hue_gradient_studio.next\` in Automationen möglich.

**Merksatz:** **Angehakte Lampen = Steuerungsgruppe. Dropdown-Lampe = Lampe, deren Presets du gerade bearbeitest. Speichern ≠ Anwenden.**

## Install with HACS (English)

1. Open **HACS → ⋮ → Custom repositories**.
2. Add \`https://github.com/derhopp/hue-gradient-studio\` as category **Integration**.
3. Open **Hue Gradient Studio → Download** in HACS.
4. Restart Home Assistant: **Settings → System → Restart**.
5. Open **Settings → Devices & services → Add integration**, find **Hue Gradient Studio**, and finish setup.
6. Confirm it appears in **Settings → Devices & services → Integrations**.

The integration bundles the Lovelace JavaScript card. In **storage resource mode**, it registers the following **JavaScript Module** automatically:

\`\`\`text
/hue-gradient-studio/hue-gradient-studio.js?v=0.1.1
\`\`\`

If the card does not load, see [Troubleshooting](#troubleshooting) before adding any duplicate resources.

### Add a card to an existing dashboard

In your existing dashboard, click **Edit dashboard → Add card → Manual** and paste:

\`\`\`yaml
type: custom:hue-gradient-studio
title: Hue Gradient Studio
\`\`\`

This only adds one card. Other cards and tabs remain untouched.

### Add a new dashboard tab

Use **Edit dashboard → Add view/tab** to create a view. Open the new tab's **View configuration → Edit in YAML** and paste the contents of [docs/view-only.yaml](docs/view-only.yaml).

> **Do not paste** \`docs/view-only.yaml\` into the dashboard's global **Raw configuration editor** to replace its contents. The file describes **one view only**; replacing the entire dashboard YAML would remove your other tabs.

## Using the dashboard: step by step

### 1. Select your control group

At **„1. Lampen auswählen“**, each checkbox adds or removes a lamp from the **saved control selection**. This selection is also used by Home Assistant actions when no specific \`entity_id\` is supplied.

The buttons above the editor act on **all selected lamps**:

| Dashboard button | What happens |
|---|---|
| **„Vorherige (Auswahl)“** | Each selected lamp moves to its previous preset (1 → 4 → 3 → 2 → 1) |
| **„Aktuelle anwenden (Auswahl)“** | Re-applies each selected lamp's **currently active** preset |
| **„Nächste (Auswahl)“** | Each selected lamp moves to its next preset (1 → 2 → 3 → 4 → 1) |

**The selected lamps do not need to share the same colors or active preset.** A group command operates independently on each lamp.

### 2. Choose which lamp to edit

In **„2. Presets einer Lampe bearbeiten“**, use the dropdown **„Lampe zum Bearbeiten“**.

- This dropdown controls **which lamp's preset definitions and settings are shown**.
- It **does not** automatically tick or untick that lamp in the group selection.
- You can edit one lamp while controlling several others from the selected group.

### 3. Set the lamp's mode and options

| Setting in the card | Purpose |
|---|---|
| **„Steuermodus“ → „3-Farben-Gradient (ZHA)“** | Send the proprietary multi-color Gradient command (supported models only) |
| **„Steuermodus“ → „Einzelfarbe (Mitte)“** | Use the preset's **middle** color as an ordinary RGB light command |
| **„Zigbee Endpoint“** | Device-specific Zigbee endpoint for the Gradient command; **11** worked for a Hue Signe table lamp |
| **„Reihenfolge“** | Reverse or retain the order in which gradient colors are sent |
| **„Auto-Intervall (Sek.)“** | Time between automatic preset changes; **30–3600 seconds** |
| **„Automatik“** | Turn automatic cycling on/off for the lamp currently being edited |

After changing these options, click **„Einstellungen speichern“**. Changing a dropdown or number alone does **not** save these device settings.

**Safety tip:** If you don't know whether a lamp supports proprietary Gradient commands or which endpoint it uses, start with **Einzelfarbe (Mitte)**. A normal Hue bulb can show only one color at a time.

### 4. Create and save the four presets

Every lamp has **Preset 1**, **Preset 2**, **Preset 3** and **Preset 4**. Each has:

- A name
- **„Oben“** — first color
- **„Mitte“** — middle color
- **„Unten“** — third color
- A preview showing the intended arrangement

Set colors using the color pickers or HEX values such as \`#FF5722\`, \`#FFB347\` and \`#6633C8\`.

Each preset offers three different actions:

| Button | What it does |
|---|---|
| **„Speichern“** | Stores this preset's name and colors; **does not change lamp output** |
| **„Auf diese Lampe“** | Saves unsaved changes to this preset (if any), then sends it to the **editing lamp** (even if not checked above) |
| **„Auf Auswahl“** | Applies this **preset number** to all checked lamps, using **each lamp's own saved colors**; does not copy the editing lamp's draft colors |

For example, suppose **Signe A** has blue–cyan–green in **Preset 2**, while **Signe B** has red–orange–yellow in **Preset 2**. Click **„Auf Auswahl“** in the Preset 2 panel with both lamps selected: **A shows its blue gradient; B shows its red gradient**.

**Unsaved edits:** Save a preset before applying it to the group. Group actions use each lamp's previously saved preset data.

### 5. Copy presets between lamps

To make multiple lamps share the same four preset definitions:

1. Set up and **save** the four presets on your source lamp.
2. Select the **target lamps** with the checkboxes under **„1. Lampen auswählen“**.
3. In **„Lampe zum Bearbeiten“**, choose the **source lamp**.
4. Click **„Alle 4 Presets dieser Lampe auf Auswahl kopieren“**.
5. Confirm the overwrite.

This **replaces all four stored presets** on the checked target lamps (excluding the source lamp). It does **not** automatically apply those presets; use **„Auf Auswahl“** or **„Aktuelle anwenden (Auswahl)“** afterwards.

### 6. Enable automatic switching

There are two ways to enable automatic preset cycling:

- **One lamp:** Choose it in **„Lampe zum Bearbeiten“**, set **„Auto-Intervall (Sek.)“** (30–3600), choose **„Automatik“ → „Ein“**, then click **„Einstellungen speichern“**.
- **Selected group:** Use **„Automatik für Auswahl EIN“** or **„Automatik für Auswahl AUS“** at the bottom of the card. Every checked lamp retains its own saved interval.

The integration cycles each enabled lamp independently through Preset 1–4. This runs inside Home Assistant; **the browser/dashboard does not need to remain open**. Cycling settings are persisted and resumed after Home Assistant restarts.

## Actions for scripts, automations and remote buttons

You can call these from **Developer tools → Actions** or a Home Assistant automation/script.

**Important:** When \`entity_id\` is omitted, the integration uses the **saved selection from the dashboard**. Set \`entity_id\` to target particular lamps independently of that selection.

### Next / previous preset

\`\`\`yaml
action: hue_gradient_studio.next
\`\`\`

\`\`\`yaml
action: hue_gradient_studio.previous
\`\`\`

These switch each selected lamp to its next or previous saved preset.

### Apply a specific preset to the selection

\`\`\`yaml
action: hue_gradient_studio.apply
data:
  preset: 2
\`\`\`

This activates Preset 2 on each selected lamp, with its **own** stored colors.

To re-apply the current preset instead, omit \`preset\`:

\`\`\`yaml
action: hue_gradient_studio.apply
\`\`\`

### Target one lamp (or several) explicitly

\`\`\`yaml
action: hue_gradient_studio.apply
data:
  entity_id: light.example_hue_gradient
  preset: 3
\`\`\`

For multiple lamps, provide an entity ID list:

\`\`\`yaml
action: hue_gradient_studio.next
data:
  entity_id:
    - light.example_hue_gradient_1
    - light.example_hue_gradient_2
\`\`\`

Replace the example entity IDs with those shown in **Developer tools → States**.

### Start or stop automatic cycling

\`\`\`yaml
action: hue_gradient_studio.set_auto
data:
  enabled: true
\`\`\`

\`\`\`yaml
action: hue_gradient_studio.set_auto
data:
  enabled: false
\`\`\`

Both act on the saved selection unless you provide \`entity_id\`.

### Philips Hue Dimmer Switch V2 (RWL022)

If you already have a working ZHA automation or blueprint for the dimmer, attach the next-preset action to its **Hue button short press** action:

\`\`\`yaml
- action: hue_gradient_studio.next
\`\`\`

This is an **action inside an existing automation or blueprint configuration**, not a complete standalone automation. How button events are triggered depends on your chosen remote blueprint or ZHA device triggers.

See [more automation examples](docs/example_automations.yaml).

## Storage, upgrades and limitations

- Presets, per-lamp configuration and saved multi-selection are stored in Home Assistant under \`/config/.storage/hue_gradient_studio\`. **Do not edit or commit this storage file.** Back up Home Assistant regularly.
- Install new versions via **HACS → Hue Gradient Studio → Update** and restart Home Assistant.
- The card is delivered with the integration, not as a separate HACS dashboard package.
- Colors are encoded for supported Gradient models using vendor-specific ZHA commands. Correct operation is **model- and endpoint-dependent**.
- The project is **AI-generated/AI-assisted experimental community software**; automated tests and individual successful device tests do not guarantee operation on every Hue lamp or Home Assistant version.

## Troubleshooting

| Problem | Check |
|---|---|
| **Custom element doesn't exist: hue-gradient-studio** | Under **Settings → Dashboards → ⋮ → Resources**, check the module resource \`/hue-gradient-studio/hue-gradient-studio.js?v=0.1.1\`; avoid duplicates, inspect **Settings → System → Logs**, then reload the browser |
| Card opens but no lamps are listed | Make sure the lamps are enabled, connected to **ZHA** and reported as Philips/Signify |
| Pressing a button affects the wrong lamps | Check the **checkbox selection**; the edit-lamp dropdown is separate |
| Changing a color does not change the lamp | Use **„Speichern“** to store the preset, then **„Auf diese Lampe“** or **„Auf Auswahl“** to apply it |
| Only one color appears | Verify the lamp supports Gradient output and is in **3-Farben-Gradient (ZHA)** mode; standard Hue color bulbs use **Einzelfarbe (Mitte)** |
| Gradient is not applied | Verify the Zigbee endpoint, lamp compatibility, availability and ZHA logs; test one lamp first |
| Auto-cycling does not start | Check the lamp's **Automatik** setting, saved interval, selected lamp(s), and **„Einstellungen speichern“** |
| Integration not listed in Integrations | Complete **Settings → Devices & services → Add integration → Hue Gradient Studio** and restart Home Assistant |

If you can reproduce a problem, create a [GitHub issue](https://github.com/derhopp/hue-gradient-studio/issues) with your Home Assistant version, lamp model, ZHA endpoint, reproduction steps and relevant logs (remove personal network details/tokens first).

## Development and release process

The backend is in \`custom_components/hue_gradient_studio/\` and the card in its \`frontend/\` subfolder. See [publishing instructions](docs/PUBLISHING.md).

Available offline tests:

\`\`\`bash
python3 -m compileall -q custom_components tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --check custom_components/hue_gradient_studio/frontend/hue-gradient-studio.js
node tests/test_ui.cjs
\`\`\`

These tests do **not** replace live testing with actual Zigbee devices, security review, or testing across Home Assistant versions.

## License

MIT License — see [LICENSE](LICENSE).
