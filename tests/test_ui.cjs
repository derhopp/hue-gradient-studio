const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const elements = new Map();
class HTMLElement {
  attachShadow() {
    this.shadowRoot = {innerHTML: '',querySelector:()=>null,querySelectorAll:()=>[]};
  }
}
const context = {
  HTMLElement,
  customElements: {get:(k)=>elements.get(k),define:(k,v)=>elements.set(k,v)},
  window: {customCards: []},
  setInterval:()=>1,
  clearInterval:()=>{},
  confirm:()=>true,
};
vm.runInNewContext(fs.readFileSync(__dirname + '/../custom_components/hue_gradient_studio/frontend/hue-gradient-studio.js','utf8'), context);
const Card = elements.get('hue-gradient-studio');
assert(Card, 'card should register');
const card = new Card();
card.setConfig({title:'Mein Gradient Studio'});
const device = {
  device_id:'dev123',name:'Signe',model:'915005986901',entity_id:'light.philips_hue_schreibtisch',
  online:true, settings:{mode:'gradient',endpoint:11,reverse:true,interval:120,auto:false,active:1,
    presets:[{name:'Sunset', colors:['#FF5722','#FFB347','#B54CE0']},
      {name:'Lagoon',colors:['#1346C1','#19B8C4','#65E8D4']},
      {name:'Galaxy',colors:['#24115A','#6633C8','#F24A9A']},
      {name:'Night',colors:['#F7A34B','#DE6E85','#623B98']}]
  }
};
card._devices=[device];
card._editDeviceId='dev123';
card._selected.add('dev123');
card._render();
assert(card.shadowRoot.innerHTML.includes('Mein Gradient Studio'));
assert(card.shadowRoot.innerHTML.includes('type="color"'));
assert(card.shadowRoot.innerHTML.includes('Automatik für Auswahl'));
assert(card.shadowRoot.innerHTML.includes('Preset 4'));
assert(!card.shadowRoot.innerHTML.includes('data-import'));
card._updateColor(0,0,'#123456');
assert(card._dirty.has('dev123/0'));
assert(card._presets()[0].colors[0] === '#123456');
console.log('JS card syntax/render smoke OK');
