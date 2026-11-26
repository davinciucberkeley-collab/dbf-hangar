// Timeline under the Designs view (replaces Physics mode): plays the T6 mechanism sweep on the real parts.
// Mechanism matrices go to the mech layer of vp.transforms, so they compose with explode.
import * as THREE from 'three';
import { h, fmt, getJSON } from '../lib.js';

const T = new THREE.Matrix4().set(1e-3, 0, 0, 0, 0, 0, 1e-3, 0, 0, -1e-3, 0, 0, 0, 0, 0, 1); // body mm (z-up) -> scene m (y-up)
const TI = T.clone().invert();
const M = new THREE.Matrix4(); // scratch: nothing is allocated per frame
let live = null; // { stop, clear, unsub } of the rendered timeline

export async function renderTimeline(ctx, d) {
  live?.stop(); live?.clear(); live?.unsub?.(); live = null;
  const box = ctx.el.querySelector('#timeline');
  box.replaceChildren(); box.classList.remove('open'); box.hidden = true;
  if (!d?.mechanisms || !d.glb) return;
  const vp = ctx.vp.main; // taken before the await: a stale mode throws here, not later
  const sw = await getJSON(d.mechanisms);
  if (vp.dead || vp.mountInfo?.id !== d.id || !vp.transforms) return;
  let mech, touched = new Set(), i = 0, raf = 0, last = 0, acc = 0;
  const sel = h('select', { 'data-testid': 'tl-mech', onchange: () => load() }, sw.mechanisms.map((m) => h('option', { value: m.id }, m.id)));
  const scrub = h('input', { type: 'range', 'data-testid': 'tl-scrub', min: 0, max: 0, value: 0, oninput: () => { i = +scrub.value; apply(i); } });
  const speed = h('select', { 'data-testid': 'tl-speed' }, ['0.5', '1', '2'].map((v) => h('option', { value: v }, v)));
  speed.value = '1';
  const loop = h('input', { type: 'checkbox', 'data-testid': 'tl-loop' });
  const input = h('span', { 'data-testid': 'tl-input' }), drv = h('span', { 'data-driver': true });
  const fol = h('div', { class: 'kv' });
  const play = h('button', { class: 'btn', 'data-testid': 'tl-play', type: 'button', onclick: () => (raf ? stop() : start()) }, 'Play');
  const clear = () => { if (!vp.dead && vp.transforms) for (const id of touched) vp.transforms.setMech(id, null); };
  const stop = () => { if (raf) cancelAnimationFrame(raf); raf = 0; play.textContent = 'Play'; };
  const frame = (now) => {
    raf = 0;
    if (vp.dead) return stop();
    acc += Math.min(now - last, 250); last = now;
    const per = 60 / +speed.value;
    while (acc >= per) {
      acc -= per;
      if (i >= +scrub.max) i = 0; else i++;
      apply(i);
      if (i >= +scrub.max && !loop.checked) return stop();
    }
    raf = requestAnimationFrame(frame);
  };
  function start() {
    if (i >= +scrub.max) { i = 0; apply(0); }
    acc = 0; last = performance.now(); play.textContent = 'Pause';
    raf = requestAnimationFrame(frame);
  }
  function load() {
    stop(); clear();
    mech = sw.mechanisms.find((m) => m.id === sel.value);
    touched = new Set(mech.steps.flatMap((s) => Object.keys(s.transforms)));
    scrub.max = mech.steps.length - 1;
    i = mech.steps.reduce((best, s, k) => (Math.abs(s.input_deg) < Math.abs(mech.steps[best].input_deg) ? k : best), 0); // open at input 0: nothing deflected
    fol.replaceChildren(...Object.keys(mech.steps[0].followers).map((l) => h('span', {}, h('b', {}, l + ' '), h('span', { 'data-follower': l }))));
    apply(i);
  }
  function apply(k) {
    const s = mech.steps[k], tr = vp.transforms;
    scrub.value = k; input.textContent = drv.textContent = fmt(s.input_deg, 0);
    for (const [l, deg] of Object.entries(s.followers)) fol.querySelector(`[data-follower="${l}"]`).textContent = fmt(deg, 1);
    if (!tr) return;
    for (const id of touched) if (!(id in s.transforms)) tr.setMech(id, null);
    for (const [id, m] of Object.entries(s.transforms)) tr.setMech(id, M.set(...m).premultiply(T).multiply(TI));
  }
  box.append(h('label', {}, 'Mechanism ', sel), play, scrub,
    h('label', {}, 'speed ', speed), h('label', {}, loop, ' loop'),
    h('div', { class: 'kv' }, h('span', {}, h('b', {}, 'input (deg) '), input), h('span', {}, h('b', {}, 'driver '), drv)), fol);
  const blocked = h('span', { 'data-testid': 'tl-blocked', class: 'muted', hidden: true }, 'Apply or revert moves to play');
  box.append(blocked);
  // pending moves are about rest pivots, so the mechanism sweep is off until they are applied or reverted
  const gate = () => {
    const on = vp.pending().length > 0;
    if (on) stop();
    for (const el of [play, scrub, sel]) el.disabled = on;
    box.classList.toggle('blocked', on); blocked.hidden = !on;
  };
  const unsub = vp.subscribe(gate);
  box.hidden = false;
  live = { stop, clear, unsub };
  load(); gate();
  if (ctx.state.timelineOpen) { box.classList.add('open'); box.scrollIntoView?.({ block: 'nearest' }); }
}
