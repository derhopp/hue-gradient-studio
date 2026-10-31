import { TRANSLATIONS, languageFromHass } from './i18n.js?v=0.1.2';

/* Hue Gradient Studio v0.1.2 — custom Lovelace card, no external JS libraries.
 * Installed and updated with the HACS integration.
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
      this._language = 'en';
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
      const language = languageFromHass(hass);
      const languageChanged = this._language !== language;
      this._hass = hass;
      this._language = language;
      if (languageChanged) {
        // The user may change their Home Assistant language without reloading.
        this._status = '';
        this._render();
      }
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

    _t(key, ...values) {
      const message = TRANSLATIONS[this._language]?.[key] ?? TRANSLATIONS.en[key] ?? key;
      return message.replace(/\{(\d+)\}/g, (_, index) => String(values[Number(index)] ?? ''));
    }

    _device() { return this._devices.find(d => d.device_id === this._editDeviceId); }
    _draftKey(i) { return `${this._editDeviceId}/${i}`; }
    _presets() {
      const dev = this._device();
      if (!dev) return [];
      if (!this._drafts[dev.device_id]) this._drafts[dev.device_id] = dev.settings.presets.map(p => ({name: p.name, colors: [...p.colors]}));
      return this._drafts[dev.device_id];
    }

    async _request(type, fields = {}) {
      if (!this._hass) throw new Error(this._t('noConnection'));
      return this._hass.connection.sendMessagePromise({type: `${BASE}/${type}`, ...fields});
    }

    async _load(silent = false) {
      if (this._loading || !this._hass) return;
      this._loading = true;
      if (!silent && !this._ready) this._status = this._t('searching');
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
        this._status = this._t('connectionFailed', e.message || e);
      } finally {
        this._loading = false;
        this._render();
      }
    }

    async _act(task, successText) {
      if (this._busy) return;
      this._busy = true;
      this._message(this._t('working'));
      try {
        const result = await task();
        if (result?.errors && Object.keys(result.errors).length) {
          this._message(this._t('errors', Object.entries(result.errors).map(([k,v]) => `${k}: ${v}`).join('; ')));
        } else {
          this._message(successText);
        }
        await this._load(true);
        return result;
      } catch(e) {
        this._message(this._t('error', e.message || e));
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
            <div><h2>${html(this._config.title || 'Hue Gradient Studio')}</h2><small>${html(this._t("subtitle"))}</small></div>
            <button data-refresh="1">${html(this._t("refresh"))}</button>
          </header>
          <div class="spacer"></div>
          <div class="selection-head"><h3>${html(this._t("selectLights"))}</h3><small>${html(this._t("selectedCount", selectedCount))}</small></div>
          <div class="devices">${this._devices.length ? this._devices.map(d => `
            <label class="device">
              <input type="checkbox" data-select="${html(d.device_id)}" ${this._selected.has(d.device_id)?'checked':''} />
              <span class="device-name"><b>${html(d.name)}</b><br><span class="tag"><span class="dot ${d.online?'':'off'}"></span>${html(d.model)} · ${html(this._t(d.settings.mode === "gradient" ? "modeGradientShort" : "modeSolidShort"))} · ${html(d.entity_id)}</span></span>
            </label>`).join('') : '<small>' + html(this._t('noLights')) + '</small>'}</div>
          <div class="buttons">
            <button data-batch="previous">${html(this._t("previousSelection"))}</button>
            <button class="primary" data-batch="apply">${html(this._t("applyCurrentSelection"))}</button>
            <button data-batch="next">${html(this._t("nextSelection"))}</button>
          </div>
          <div class="spacer"></div>
          <h3>${html(this._t("editPresets"))}</h3>
          <label class="label" for="edit-device">${html(this._t("editLamp"))}</label>
          <select id="edit-device" data-edit="1" style="width:100%">${this._devices.map(d=>`<option value="${html(d.device_id)}" ${d.device_id===this._editDeviceId?'selected':''}>${html(d.name)} – ${html(d.entity_id)}</option>`).join('')}</select>
          ${dev ? `
            <div class="settings">
              <div class="setting"><label class="label">${html(this._t("controlMode"))}</label><select data-mode="1">
                <option value="gradient" ${dev.settings.mode==='gradient'?'selected':''}>${html(this._t("gradientMode"))}</option>
                <option value="solid" ${dev.settings.mode==='solid'?'selected':''}>${html(this._t("solidMode"))}</option>
              </select></div>
              <div class="setting"><label class="label">${html(this._t("endpoint"))}</label><input type="number" data-endpoint="1" min="1" max="240" value="${Number(dev.settings.endpoint)}" /></div>
              <div class="setting"><label class="label">${html(this._t("colorOrder"))}</label><select data-reverse="1">
                <option value="true" ${dev.settings.reverse?'selected':''}>${html(this._t("reverse"))}</option><option value="false" ${!dev.settings.reverse?'selected':''}>${html(this._t("normal"))}</option>
              </select></div>
              <div class="setting"><label class="label">${html(this._t("autoInterval"))}</label><input type="number" data-interval="1" min="30" max="3600" value="${Number(dev.settings.interval)}" /></div>
              <div class="setting"><label class="label">${html(this._t("automatic"))}</label><select data-auto="1">
                <option value="false" ${!dev.settings.auto?'selected':''}>${html(this._t("off"))}</option><option value="true" ${dev.settings.auto?'selected':''}>${html(this._t("on"))}</option>
              </select></div>
            </div>
            <div class="buttons"><button data-save-config="1">${html(this._t("saveSettings"))}</button></div>
            <p class="caption">${html(this._t("modeNote"))}</p>
            <div class="spacer"></div>
            <div class="panels">${presets.map((p,i) => `
              <section data-panel="${i}" class="${dev.settings.active===i+1?'active':''}">
                <div class="row"><h4>Preset ${i+1}</h4><small>${dev.settings.active===i+1?html(this._t("active")):""}${this._dirty.has(this._draftKey(i))?" · "+html(this._t("unsaved")):""}</small></div>
                <label class="label">${html(this._t("name"))}</label><input class="name" maxlength="48" data-name="${i}" type="text" value="${html(p.name)}" />
                <div class="preview" data-preview="${i}" style="background:linear-gradient(180deg,${p.colors.join(',')})"></div>
                <div class="pickers">${p.colors.map((c,j)=>`<div><label class="label">${html(this._t(["top","middle","bottom"][j]))}</label>
                  <input data-color="${i}" data-index="${j}" type="color" value="${html(c)}" />
                  <input class="hex" data-hex="${i}" data-index="${j}" type="text" maxlength="7" value="${html(c)}" /></div>`).join('')}</div>
                <div class="buttons"><button data-save="${i}">${html(this._t("save"))}</button><button class="primary" data-apply="${i}">${html(this._t("applyThisLamp"))}</button><button data-batch-preset="${i}">${html(this._t("applySelection"))}</button></div>
              </section>`).join('')}</div>
            <div class="spacer"></div>
            <div class="buttons"><button data-copy="1">${html(this._t("copyPresets"))}</button></div>
            <p class="caption">${html(this._t("applyHelp"))}</p>
            <div class="buttons"><button data-autos="true">${html(this._t("autoSelectionOn"))}</button><button data-autos="false">${html(this._t("autoSelectionOff"))}</button></div>
          ` : '<p class="caption">' + html(this._t('noDevices')) + '</p>'}
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
        await this._act(() => this._request('select', {device_ids: [...proposed]}), this._t('selectionSaved'));
      }));
      $$('[data-color]').forEach(el => el.addEventListener('input', e => {
        this._updateColor(Number(e.target.dataset.color), Number(e.target.dataset.index), e.target.value.toUpperCase());
      }));
      $$('[data-hex]').forEach(el => el.addEventListener('change', e => {
        const val = e.target.value.trim().toUpperCase();
        if (!VALID_HEX.test(val)) return this._message(this._t('hexInvalid'));
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
        await this._act(() => this._request('control', {action: 'apply', device_ids: [this._editDeviceId], preset: index + 1}), this._t('appliedThisLight', index + 1));
      }));
      $$('[data-batch-preset]').forEach(el => el.addEventListener('click', () => this._act(
        () => this._request('control', {action:'apply', preset: Number(el.dataset.batchPreset)+1}),
        this._t('selectedPresetApplied')
      )));
      $$('[data-batch]').forEach(el => el.addEventListener('click', () => this._act(
        () => this._request('control', {action: el.dataset.batch}),
        this._t('selectionActionDone')
      )));
      $$('[data-autos]').forEach(el => el.addEventListener('click', () => this._act(
        () => this._request('control', {action:'auto', enabled: el.dataset.autos === 'true'}),
        this._t('autoUpdated')
      )));
      $('[data-save-config]')?.addEventListener('click', () => this._act(async () => {
        const endpoint = Number($('[data-endpoint]').value);
        const interval = Number($('[data-interval]').value);
        if (!Number.isInteger(endpoint) || endpoint < 1 || endpoint > 240) throw new Error(this._t('endpointInvalid'));
        if (!Number.isInteger(interval) || interval < 30 || interval > 3600) throw new Error(this._t('intervalInvalid'));
        return this._request('configure', {
          device_id: this._editDeviceId, mode: $('[data-mode]').value,
          endpoint, interval, reverse: $('[data-reverse]').value === 'true',
          auto: $('[data-auto]').value === 'true'
        });
      }, this._t('settingsSaved')));
      $('[data-copy]')?.addEventListener('click', () => {
        if (!confirm(this._t('copyConfirm'))) return;
        this._act(() => this._request('copy', {source: this._editDeviceId,
          targets: [...this._selected].filter(i => i !== this._editDeviceId)}),
        this._t('presetsCopied'));
      });
    }

    _updateBadge(i) {
      const el = this.shadowRoot.querySelector(`[data-panel="${i}"] .row small`);
      if (el) el.textContent = (this._device()?.settings.active===i+1?this._t('active')+' · ':'') + this._t('unsaved');
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
      }), this._t('presetSaved', i + 1));
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
    window.customCards.push({type: 'hue-gradient-studio', name: 'Hue Gradient Studio v0.1.2',
      description: 'Multi-light ZHA editor, per-device 4×3 colors, automatic cycling', preview: false});
  }
})();
