/* Hue Gradient Studio v0.1.0 — custom Lovelace card, no external JS libraries.
 * Bundled with the HACS integration; no separate /config/www installation required.
 * Four persistent, per-light 3-color presets, multiple light target selection.
 */
(() => {
  const BASE = 'hue_gradient_studio';
  const VALID_HEX = /^#[0-9a-fA-F]{6}$/;
  const html = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  class HueGradientStudio extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({mode: 'open'});
      this._config = {};
      this._hass = null;
      this._devices = [];
      this._selected = new Set();
      this._editDeviceId = null;
      this._drafts = {};
      this._dirty = new Set();
      this._loading = false;
      this._ready = false;
      this._busy = false;
      this._status = '';
      this._lastLoad = 0;
      this._refreshTimer = null;
    }

    setConfig(config) {
      this._config = config || {};
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._loading && (!this._ready || (Date.now() - this._lastLoad > 45000 && !this._dirty.size))) {
        this._load();
      }
    }

    connectedCallback() {
      if (this._hass && !this._ready) this._load();
      if (!this._refreshTimer) this._refreshTimer = setInterval(() => {
        if (this._hass && !this._busy && !this._dirty.size) this._load(true);
      }, 60000);
    }

    disconnectedCallback() {
      if (this._refreshTimer) clearInterval(this._refreshTimer);
      this._refreshTimer = null;
    }

    getCardSize() { return 12; }

    _device() { return this._devices.find(d => d.device_id === this._editDeviceId); }
    _draftKey(i) { return `${this._editDeviceId}/${i}`; }
    _presets() {
      const dev = this._device();
      if (!dev) return [];
      if (!this._drafts[dev.device_id]) this._drafts[dev.device_id] = dev.settings.presets.map(p => ({name: p.name, colors: [...p.colors]}));
      return this._drafts[dev.device_id];
    }

    async _request(type, fields = {}) {
      if (!this._hass) throw new Error('Home Assistant is not connected');
      return this._hass.connection.sendMessagePromise({type: `${BASE}/${type}`, ...fields});
    }

    async _load(silent = false) {
      if (this._loading || !this._hass) return;
      this._loading = true;
      if (!silent && !this._ready) this._status = 'Hue-Lampen werden gesucht …';
      try {
        const result = await this._request('list');
        this._devices = result.devices || [];
        this._selected = new Set(result.selection || []);
        if (!this._devices.some(d => d.device_id === this._editDeviceId)) {
          this._editDeviceId = this._devices[0]?.device_id || null;
        }
        for (const d of this._devices) {
          if (!this._drafts[d.device_id] || !Array.from({length: 4}, (_, i) => `${d.device_id}/${i}`).some(k => this._dirty.has(k))) {
            this._drafts[d.device_id] = d.settings.presets.map(p => ({name: p.name, colors: [...p.colors]}));
          }
        }
        this._ready = true;
        this._lastLoad = Date.now();
      } catch(e) {
        this._status = `Verbindung zur Custom Integration fehlgeschlagen: ${e.message || e}`;
      } finally {
        this._loading = false;
        this._render();
      }
    }

    async _act(task, successText) {
      if (this._busy) return;
      this._busy = true;
      this._message('Aktion läuft …');
      try {
        const result = await task();
        if (result?.errors && Object.keys(result.errors).length) {
          this._message('Fehler: ' + Object.entries(result.errors).map(([k,v]) => `${k}: ${v}`).join('; '));
        } else {
          this._message(successText);
        }
        await this._load(true);
        return result;
      } catch(e) {
        this._message(`Fehler: ${e.message || e}`);
        return null;
      } finally {
        this._busy = false;
      }
    }

    _message(value) {
      this._status = value;
      const el = this.shadowRoot.querySelector('[data-status]');
      if (el) el.textContent = value;
    }

    _render() {
      const dev = this._device();
      const presets = dev ? this._presets() : [];
      const selectedCount = this._selected.size;
      const theme = `
        :host{display:block;color:var(--primary-text-color,#f5f5f5);font:inherit}
        *{box-sizing:border-box}
        .wrap{background:var(--ha-card-background,var(--card-background-color,#242831));border:1px solid var(--divider-color,#4c535d);border-radius:var(--ha-card-border-radius,16px);padding:20px}
        header,.toolbar,.row,.buttons,.selection-head{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
        h2{font-size:22px;margin:0 0 4px}h3{font-size:16px;margin:0}h4{font-size:14px;margin:0}
        small,.muted{color:var(--secondary-text-color,#abb4c2)}small{font-size:12px}
        .spacer{height:18px}.label{font-size:12px;display:block;margin:8px 0 5px;color:var(--secondary-text-color,#abb4c2)}
        .devices{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:8px;margin:12px 0}
        .device{background:var(--secondary-background-color,#343a44);padding:9px;border-radius:9px;border:1px solid var(--divider-color,#525762);display:flex;gap:9px;align-items:center;min-width:0}
        .device input{width:20px;height:20px;accent-color:var(--primary-color,#1999cf)}
        .device-name{min-width:0;overflow-wrap:anywhere}.tag{color:var(--secondary-text-color,#a1acbb);font-size:11px}
        .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#41bc68;margin-right:3px}.dot.off{background:#b86262}
        .panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
        section{border:1px solid var(--divider-color,#58606d);border-radius:12px;padding:12px;min-width:0}
        section.active{outline:1px solid var(--primary-color,#12a2d4)}
        .preview{height:46px;border-radius:9px;margin:12px 0}
        .pickers{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
        input[type=color]{display:block;width:100%;height:42px;border:1px solid var(--divider-color,#555);border-radius:7px;background:transparent;padding:2px;cursor:pointer}
        input[type=text],input[type=number],select{background:var(--secondary-background-color,#2d323d);border:1px solid var(--divider-color,#505866);border-radius:7px;padding:8px;color:var(--primary-text-color,#fff);max-width:100%;min-width:0}
        input.hex{display:block;width:100%;font-size:12px;font-family:monospace;margin-top:5px}
        .name{width:100%;font-size:14px;margin-bottom:2px}
        button{border:1px solid var(--divider-color,#58606d);background:var(--secondary-background-color,#323a45);border-radius:9px;color:var(--primary-text-color,#fff);padding:10px;cursor:pointer;font:inherit;font-size:13px}
        button.primary{background:var(--primary-color,#078fc5);border-color:transparent;color:var(--text-primary-color,#fff)}
        button:disabled{opacity:.5;cursor:wait}
        .buttons{justify-content:flex-start;margin-top:11px}.buttons button{flex:1;min-width:80px}
        .settings{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:10px 0 14px}
        .setting{min-width:100px;flex:1}.setting select,.setting input[type=number]{width:100%}
        .caption{font-size:12px;line-height:1.5;margin:8px 0 0}
        .alert{font-size:12px;color:var(--error-color,#ff8e8e);margin-top:9px}
        .status{font-size:12px;color:var(--secondary-text-color,#adb7c1);margin-top:17px;min-height:1.3em;overflow-wrap:anywhere}
        @media(max-width:500px){.wrap{padding:12px}.panels{grid-template-columns:1fr}}
      `;
      this.shadowRoot.innerHTML = `<style>${theme}</style>
        <div class="wrap">
          <header>
            <div><h2>${html(this._config.title || 'Hue Gradient Studio')}</h2><small>Mehrere ZHA-Lampen · 4 Presets pro Lampe · 3 Farben je Preset</small></div>
            <button data-refresh="1">↻ Refresh</button>
          </header>
          <div class="spacer"></div>
          <div class="selection-head"><h3>1. Lampen auswählen</h3><small>${selectedCount} ausgewählt · Auswahl bleibt in HA gespeichert</small></div>
          <div class="devices">${this._devices.length ? this._devices.map(d => `
            <label class="device">
              <input type="checkbox" data-select="${html(d.device_id)}" ${this._selected.has(d.device_id)?'checked':''} />
              <span class="device-name"><b>${html(d.name)}</b><br><span class="tag"><span class="dot ${d.online?'':'off'}"></span>${html(d.model)} · ${d.settings.mode === 'gradient'?'Gradient':'Einzelfarbe'} · ${html(d.entity_id)}</span></span>
            </label>`).join('') : '<small>Keine Philips-/Signify-Leuchten in ZHA gefunden. Nur ZHA-Geräte werden angeboten.</small>'}</div>
          <div class="buttons">
            <button data-batch="previous">◀ Vorherige (Auswahl)</button>
            <button class="primary" data-batch="apply">Aktuelle anwenden (Auswahl)</button>
            <button data-batch="next">Nächste (Auswahl) ▶</button>
          </div>
          <div class="spacer"></div>
          <h3>2. Presets einer Lampe bearbeiten</h3>
          <label class="label" for="edit-device">Lampe zum Bearbeiten (unabhängig von der Mehrfachauswahl)</label>
          <select id="edit-device" data-edit="1" style="width:100%">${this._devices.map(d=>`<option value="${html(d.device_id)}" ${d.device_id===this._editDeviceId?'selected':''}>${html(d.name)} – ${html(d.entity_id)}</option>`).join('')}</select>
          ${dev ? `
            <div class="settings">
              <div class="setting"><label class="label">Steuermodus</label><select data-mode="1">
                <option value="gradient" ${dev.settings.mode==='gradient'?'selected':''}>3-Farben-Gradient (ZHA)</option>
                <option value="solid" ${dev.settings.mode==='solid'?'selected':''}>Einzelfarbe (Mitte)</option>
              </select></div>
              <div class="setting"><label class="label">Zigbee Endpoint</label><input type="number" data-endpoint="1" min="1" max="240" value="${Number(dev.settings.endpoint)}" /></div>
              <div class="setting"><label class="label">Reihenfolge</label><select data-reverse="1">
                <option value="true" ${dev.settings.reverse?'selected':''}>Umkehren</option><option value="false" ${!dev.settings.reverse?'selected':''}>Normal</option>
              </select></div>
              <div class="setting"><label class="label">Auto-Intervall (Sek.)</label><input type="number" data-interval="1" min="30" max="3600" value="${Number(dev.settings.interval)}" /></div>
              <div class="setting"><label class="label">Automatik</label><select data-auto="1">
                <option value="false" ${!dev.settings.auto?'selected':''}>Aus</option><option value="true" ${dev.settings.auto?'selected':''}>Ein</option>
              </select></div>
            </div>
            <div class="buttons"><button data-save-config="1">Einstellungen speichern</button><button data-import="1">Alte Signe-Presets importieren</button></div>
            <p class="caption">Bei normalen Hue-Lampen nur „Einzelfarbe (Mitte)“ verwenden. Gradient-Cluster 0xFC03 funktioniert ausschließlich auf kompatiblen Hue-Gradient-Modellen. Der Endpoint 11 ist für die getestete Signe bekannt, bei anderen Modellen ggf. anpassen.</p>
            <div class="spacer"></div>
            <div class="panels">${presets.map((p,i) => `
              <section data-panel="${i}" class="${dev.settings.active===i+1?'active':''}">
                <div class="row"><h4>Preset ${i+1}</h4><small>${dev.settings.active===i+1?'● AKTIV':''}${this._dirty.has(this._draftKey(i))?' · Ungespeichert':''}</small></div>
                <label class="label">Name</label><input class="name" maxlength="48" data-name="${i}" type="text" value="${html(p.name)}" />
                <div class="preview" data-preview="${i}" style="background:linear-gradient(180deg,${p.colors.join(',')})"></div>
                <div class="pickers">${p.colors.map((c,j)=>`<div><label class="label">${['Oben','Mitte','Unten'][j]}</label>
                  <input data-color="${i}" data-index="${j}" type="color" value="${html(c)}" />
                  <input class="hex" data-hex="${i}" data-index="${j}" type="text" maxlength="7" value="${html(c)}" /></div>`).join('')}</div>
                <div class="buttons"><button data-save="${i}">Speichern</button><button class="primary" data-apply="${i}">Auf diese Lampe</button><button data-batch-preset="${i}">Auf Auswahl</button></div>
              </section>`).join('')}</div>
            <div class="spacer"></div>
            <div class="buttons"><button data-copy="1">Alle 4 Presets dieser Lampe auf Auswahl kopieren</button></div>
            <p class="caption">„Auf Auswahl“ aktiviert Preset N jeder gewählten Lampe mit <b>deren eigenen</b> Farben. Mit „kopieren“ überträgst du stattdessen diese vier Presets auf alle ausgewählten Lampen (überschreibt deren Presets).</p>
            <div class="buttons"><button data-autos="true">Automatik für Auswahl EIN</button><button data-autos="false">Automatik für Auswahl AUS</button></div>
          ` : '<p class="caption">Sobald ZHA-Leuchten erkannt wurden, erscheinen hier die Colorpicker und Geräteeinstellungen.</p>'}
          <div class="status" data-status role="status">${html(this._status)}</div>
        </div>`;
      this._listeners();
    }

    _listeners() {
      const $ = (selector) => this.shadowRoot.querySelector(selector);
      const $$ = (selector) => Array.from(this.shadowRoot.querySelectorAll(selector));
      $('[data-refresh]')?.addEventListener('click', () => this._load());
      $('[data-edit]')?.addEventListener('change', e => {
        this._editDeviceId = e.target.value;
        this._render();
      });
      $$('[data-select]').forEach(el => el.addEventListener('change', async e => {
        const id = e.target.dataset.select;
        const proposed = new Set(this._selected);
        if (e.target.checked) proposed.add(id); else proposed.delete(id);
        await this._act(() => this._request('select', {device_ids: [...proposed]}), 'Auswahl gespeichert.');
      }));
      $$('[data-color]').forEach(el => el.addEventListener('input', e => {
        this._updateColor(Number(e.target.dataset.color), Number(e.target.dataset.index), e.target.value.toUpperCase());
      }));
      $$('[data-hex]').forEach(el => el.addEventListener('change', e => {
        const val = e.target.value.trim().toUpperCase();
        if (!VALID_HEX.test(val)) return this._message('HEX-Farbe muss #RRGGBB sein.');
        this._updateColor(Number(e.target.dataset.hex), Number(e.target.dataset.index), val);
      }));
      $$('[data-name]').forEach(el => el.addEventListener('input', e => {
        this._presets()[Number(e.target.dataset.name)].name = e.target.value;
        this._dirty.add(this._draftKey(Number(e.target.dataset.name)));
        this._updateBadge(Number(e.target.dataset.name));
      }));
      $$('[data-save]').forEach(el => el.addEventListener('click', () => this._savePreset(Number(el.dataset.save))));
      $$('[data-apply]').forEach(el => el.addEventListener('click', async () => {
        const index = Number(el.dataset.apply);
        if (!(await this._saveIfDirty(index))) return;
        await this._act(() => this._request('control', {action: 'apply', device_ids: [this._editDeviceId], preset: index + 1}), `Preset ${index+1} auf diese Lampe angewendet.`);
      }));
      $$('[data-batch-preset]').forEach(el => el.addEventListener('click', () => this._act(
        () => this._request('control', {action:'apply', preset: Number(el.dataset.batchPreset)+1}),
        'Preset der ausgewählten Lampen aktiviert.'
      )));
      $$('[data-batch]').forEach(el => el.addEventListener('click', () => this._act(
        () => this._request('control', {action: el.dataset.batch}),
        'Aktion für ausgewählte Lampen ausgeführt.'
      )));
      $$('[data-autos]').forEach(el => el.addEventListener('click', () => this._act(
        () => this._request('control', {action:'auto', enabled: el.dataset.autos === 'true'}),
        'Automatik für ausgewählte Lampen aktualisiert.'
      )));
      $('[data-save-config]')?.addEventListener('click', () => this._act(async () => {
        const endpoint = Number($('[data-endpoint]').value);
        const interval = Number($('[data-interval]').value);
        if (!Number.isInteger(endpoint) || endpoint < 1 || endpoint > 240) throw new Error('Endpoint muss 1–240 sein.');
        if (!Number.isInteger(interval) || interval < 30 || interval > 3600) throw new Error('Intervall muss 30–3600 Sekunden sein.');
        return this._request('configure', {
          device_id: this._editDeviceId, mode: $('[data-mode]').value,
          endpoint, interval, reverse: $('[data-reverse]').value === 'true',
          auto: $('[data-auto]').value === 'true'
        });
      }, 'Geräteeinstellungen gespeichert.'));
      $('[data-copy]')?.addEventListener('click', () => {
        if (!confirm('Die 4 Presets auf ALLEN ausgewählten Lampen überschreiben?')) return;
        this._act(() => this._request('copy', {source: this._editDeviceId,
          targets: [...this._selected].filter(i => i !== this._editDeviceId)}),
        'Vier Presets auf die Auswahl kopiert.');
      });
      $('[data-import]')?.addEventListener('click', () => {
        if (!confirm('Die gespeicherten 4 alten Signe-Presets (soweit vorhanden) in diese Lampe importieren?')) return;
        this._act(() => this._request('import_legacy', {device_id: this._editDeviceId}),
          'Import aus alten Signe-Helpern abgeschlossen.');
      });
    }

    _updateBadge(i) {
      const el = this.shadowRoot.querySelector(`[data-panel="${i}"] .row small`);
      if (el) el.textContent = (this._device()?.settings.active===i+1?'● AKTIV · ':'')+'Ungespeichert';
    }

    _updateColor(i,j,color) {
      if (!VALID_HEX.test(color)) return;
      const preset = this._presets()[i];
      if (!preset) return;
      preset.colors[j] = color;
      this._dirty.add(this._draftKey(i));
      const panel = this.shadowRoot.querySelector(`[data-panel="${i}"]`);
      if (panel) {
        panel.querySelector('[data-preview]').style.background = `linear-gradient(180deg,${preset.colors.join(',')})`;
        panel.querySelector(`[data-color="${i}"][data-index="${j}"]`).value = color;
        panel.querySelector(`[data-hex="${i}"][data-index="${j}"]`).value = color;
      }
      this._updateBadge(i);
    }

    async _savePreset(i) {
      const id = this._editDeviceId;
      const preset = this._presets()[i];
      const result = await this._act(() => this._request('save_preset', {
        device_id: id, preset: i+1, colors: [...preset.colors], name: preset.name
      }), `Preset ${i+1} gespeichert.`);
      if (result) {
        this._dirty.delete(`${id}/${i}`);
        this._render();
        return true;
      }
      return false;
    }

    async _saveIfDirty(i) {
      if (!this._dirty.has(this._draftKey(i))) return true;
      return await this._savePreset(i);
    }
  }

  if (!customElements.get('hue-gradient-studio')) customElements.define('hue-gradient-studio', HueGradientStudio);
  window.customCards = window.customCards || [];
  if (!window.customCards.some(c => c.type === 'hue-gradient-studio')) {
    window.customCards.push({type: 'hue-gradient-studio', name: 'Hue Gradient Studio v0.1.0',
      description: 'Multi-light ZHA editor, per-device 4×3 colors, automatic cycling', preview: false});
  }
})();
