// Physics mode (R11): replays the analytic T6 mechanism sweep with the real part motion.
import * as THREE from 'three';

let timer = null;
const T = new THREE.Matrix4().set(1e-3, 0, 0, 0, 0, 0, 1e-3, 0, 0, -1e-3, 0, 0, 0, 0, 0, 1); // body mm (z-up) -> scene m (y-up)
const TI = T.clone().invert();
let warned = false;

export default async function render({ state, el, h, fmt, getJSON, byId, vp }) {
  clearInterval(timer); timer = null;
  const box = el.querySelector('#phys-controls'); box.replaceChildren();
  const d = byId(state.selected);
  if (!d?.mechanisms || !d.glb) {
    vp.phys.clear(); vp.phys.message('');
    box.append(h('p', { class: 'muted' }, 'This design has no mechanisms.'));
    el.dataset.ready = '1'; return;
  }
  const sw = await getJSON(d.mechanisms);
  await vp.phys.show(d);
  const sel = h('select', { 'data-testid': 'phys-mech', onchange: () => load() }, sw.mechanisms.map((m) => h('option', { value: m.id }, m.id)));
  const slider = h('input', { type: 'range', 'data-testid': 'phys-slider', min: 0, max: 0, value: 0, oninput: () => apply(+slider.value) });
  const input = h('span', { 'data-testid': 'phys-input' }), drv = h('span', { 'data-driver': true });
  const fol = h('div', { class: 'kv' });
  const play = h('button', { class: 'btn', 'data-testid': 'play', onclick: () => {
    if (timer) return stop();
    let i = +slider.value >= +slider.max ? 0 : +slider.value;
    play.textContent = 'Pause';
    timer = setInterval(() => { apply(i); if (i++ >= +slider.max) stop(); }, 60);
  } }, 'Play');
  const stop = () => { clearInterval(timer); timer = null; play.textContent = 'Play'; };
  let mech, touched;
  function load() {
    stop();
    mech = sw.mechanisms.find((m) => m.id === sel.value);
    touched = new Set(mech.steps.flatMap((s) => Object.keys(s.transforms)));
    slider.max = mech.steps.length - 1;
    fol.replaceChildren(...Object.keys(mech.steps[0].followers).map((l) => h('span', {}, h('b', {}, l + ' '), h('span', { 'data-follower': l }))));
    apply(0);
  }
  function apply(i) {
    const s = mech.steps[i];
    slider.value = i; input.textContent = drv.textContent = fmt(s.input_deg, 0);
    for (const [l, deg] of Object.entries(s.followers)) fol.querySelector(`[data-follower="${l}"]`).textContent = fmt(deg, 1);
    const node = (id) => {
      const n = vp.phys.model.getObjectByName(id);
      if (n && n.position.lengthSq() === 0) return n;
      if (!warned) { warned = true; console.warn(`physics: node ${id} missing or not at rest origin; showing readouts only`); }
      return null;
    };
    for (const id of touched) { const n = node(id); if (n) { n.matrixAutoUpdate = false; n.matrix.identity(); n.matrixWorldNeedsUpdate = true; } }
    for (const [id, m] of Object.entries(s.transforms)) {
      const n = node(id);
      if (n) { n.matrix.copy(new THREE.Matrix4().set(...m).premultiply(T).multiply(TI)); n.matrixWorldNeedsUpdate = true; }
    }
    vp.phys.dirty = true;
  }
  box.append(h('label', {}, 'Mechanism ', sel), play, slider,
    h('div', { class: 'kv' }, h('span', {}, h('b', {}, 'input (deg) '), input), h('span', {}, h('b', {}, 'driver '), drv)), fol);
  load();
  el.dataset.ready = '1';
}
