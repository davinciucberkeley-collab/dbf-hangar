// Viewer: one app (Plane Studio). Reads only generated data (data/index.json + per-design files).
// Each mode is modes/<id>.js; modes/edit.js is loaded only when index.json has "studio": true.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { h, $, fmt, getJSON, cache, TIERS } from './lib.js';

const DATA = 'data/';
const MODES = ['designs', 'compare', 'physics', 'stress', 'updates', 'ledger'];
const LABELS = { designs: 'Designs', compare: 'Compare', physics: 'Physics', stress: 'Stress', updates: 'Updates', ledger: 'Ledger' };
const HINTS = { designs: 'Click a part to highlight it. Drag to orbit, scroll to zoom.', compare: 'Click designs in the list to fill slots A and B alternately.' };

const state = { index: null, selected: null, mode: 'designs', slotA: null, slotB: null, nextSlot: 'a', text: '', vtol: '' };
const byId = (id) => state.index?.designs.find((d) => d.id === id);
const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const mmToScene = ([x, y, z]) => new THREE.Vector3(x / 1000, z / 1000, -y / 1000); // body z-up mm -> glTF y-up m

// ---------- 3D viewport ----------
class Viewport {
  constructor(el, { onPick } = {}) {
    this.el = el; this.onPick = onPick; this.ids = new Set(); this.highlighted = new Set(); this.dirty = true;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    el.append(this.renderer.domElement);
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.01, 50);
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x556070, 1.6));
    const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(2, 3, 1.5); this.scene.add(sun);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = false;
    this.controls.addEventListener('change', () => (this.dirty = true));
    this.root = new THREE.Group(); this.scene.add(this.root);
    this.ray = new THREE.Raycaster();
    this.overlay = h('div', { class: 'vp-overlay', hidden: true });
    this.msg = h('div', { class: 'vp-msg' });
    this.legend = h('div', { class: 'vp-legend', hidden: true }, h('span', { class: 'dot' }), 'CG');
    el.append(this.overlay, this.msg, this.legend);
    let down = null;
    const cv = this.renderer.domElement;
    cv.addEventListener('pointerdown', (e) => (down = [e.clientX, e.clientY]));
    cv.addEventListener('pointerup', (e) => {
      if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;
      this.pick(e);
    });
    new ResizeObserver(() => this.resize()).observe(el);
    this.applyTheme(); this.resize();
  }
  applyTheme() {
    this.scene.background = new THREE.Color(cssVar('--vp-bg') || '#e9ecf1'); this.dirty = true;
  }
  resize() {
    const w = this.el.clientWidth, hgt = this.el.clientHeight;
    if (!w || !hgt) return;
    this.renderer.setSize(w, hgt, false);
    this.camera.aspect = w / hgt; this.camera.updateProjectionMatrix(); this.dirty = true;
  }
  message(text, err = false) {
    this.msg.textContent = text || ''; this.msg.className = 'vp-msg' + (err ? ' err' : ''); this.msg.hidden = !text;
  }
  clear() {
    this.root.clear(); this.ids.clear(); this.highlighted.clear(); this.cg = null; this.mass = null;
    this.overlay.hidden = true; this.legend.hidden = true; this.dirty = true;
  }
  async show(design) {
    const token = (this.token = Symbol());
    this.clear();
    if (!design) return this.message('Select a design');
    if (design.pending) return this.message('Checking this design… the model appears when it is done.');
    if (design.error) return this.message('No model: ' + design.error, true);
    if (!design.glb) return this.message('No GLB for this design', true);
    this.message('Loading…');
    try {
      const [gltf, mass] = await Promise.all([loadGLB(design.glb), design.mass ? getJSON(design.mass).catch(() => null) : null]);
      if (token !== this.token) return;
      const model = gltf.scene.clone(true);
      this.mass = new Map((mass?.per_component || []).map((c) => [c.id, c]));
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = o.material.clone();
        o.material.side = THREE.DoubleSide;
        const type = o.userData.type ?? o.parent?.userData?.type;
        o.userData.compType = type;
        const a = o.geometry.getAttribute('color');
        if (type === 'propeller' || (a && a.itemSize === 4)) { o.material.transparent = type === 'propeller'; }
        o.userData.baseOpacity = o.material.opacity;
        const comp = this.componentOf(o, model);
        if (comp) { o.userData.compId = comp.name; this.ids.add(comp.name); }
      });
      this.root.add(model);
      this.model = model;
      const box = new THREE.Box3().setFromObject(model);
      this.size = box.getSize(new THREE.Vector3()); this.center = box.getCenter(new THREE.Vector3());
      const diag = this.size.length() || 1;
      this.root.add(this.makeGrid(box, diag));
      const cgmm = design.cg_mm || mass?.cg_mm;
      if (cgmm) this.addCG(mmToScene(cgmm), diag);
      this.mountInfo = design;
      this.fit(diag);
      this.message('');
    } catch (e) {
      console.warn(e); this.message('Could not load model: ' + e.message, true);
    }
  }
  componentOf(mesh, model) { // nearest named ancestor (or the mesh itself) is the component node
    let o = mesh;
    while (o && o !== model) { if (o.name) return o; o = o.parent; }
    return mesh.name ? mesh : null;
  }
  makeGrid(box, diag) {
    const g = new THREE.GridHelper(diag * 2.4, 24, 0x8a94a6, 0x8a94a6);
    g.material.opacity = 0.35; g.material.transparent = true;
    g.position.set(this.center.x, box.min.y - diag * 0.02, this.center.z);
    return g;
  }
  addCG(p, diag) {
    const r = diag * 0.018;
    const mat = new THREE.MeshBasicMaterial({ color: 0xf97316, depthTest: false, transparent: true });
    const s = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 14), mat); s.position.copy(p); s.renderOrder = 10;
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r * 1.8, r * 0.18, 8, 32), mat); ring.position.copy(p); ring.renderOrder = 10;
    ring.rotation.x = Math.PI / 2;
    this.root.add(s, ring); this.legend.hidden = false;
  }
  fit(diag) {
    const d = diag * 1.9;
    this.camera.position.copy(this.center).add(new THREE.Vector3(0.9, 0.55, 1.1).normalize().multiplyScalar(d));
    this.controls.target.copy(this.center); this.camera.near = d / 100; this.camera.far = d * 20;
    this.camera.updateProjectionMatrix(); this.controls.update(); this.dirty = true;
  }
  pick(e) {
    if (!this.model) return;
    const r = this.renderer.domElement.getBoundingClientRect();
    this.ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), this.camera);
    const hit = this.ray.intersectObject(this.model, true).find((i) => i.object.userData.compId);
    this.onPick?.(hit ? hit.object.userData.compId : null, this);
  }
  highlight(ids) {
    this.highlighted = new Set([...ids].filter((i) => this.ids.has(i)));
    const any = this.highlighted.size > 0;
    this.model?.traverse((o) => {
      if (!o.isMesh) return;
      const on = this.highlighted.has(o.userData.compId);
      o.material.emissive?.set(on ? 0xffb020 : 0x000000);
      if (o.material.emissiveIntensity != null) o.material.emissiveIntensity = on ? 0.55 : 1;
      const base = o.userData.baseOpacity ?? 1;
      o.material.transparent = o.userData.compType === 'propeller' || (any && !on);
      o.material.opacity = any && !on ? Math.min(base, 0.28) : base;
      o.material.needsUpdate = true;
    });
    this.updateOverlay(); this.dirty = true;
  }
  updateOverlay() {
    this.overlay.replaceChildren();
    const ids = [...this.highlighted];
    this.overlay.hidden = !ids.length;
    for (const id of ids) {
      const node = this.model.getObjectByName(id);
      const type = node?.userData?.type ?? node?.children?.[0]?.userData?.compType ?? '–';
      const m = this.mass?.get(id);
      this.overlay.append(h('div', {}, h('b', {}, id)), h('dl', {},
        h('dt', {}, 'type'), h('dd', {}, type),
        h('dt', {}, 'mass'), h('dd', {}, m ? `${fmt(m.mass_g, 1)} g` : (node?.userData?.mass_g != null ? `${node.userData.mass_g} g` : '–')),
        m?.cg_mm ? [h('dt', {}, 'cg (mm)'), h('dd', {}, m.cg_mm.map((v) => fmt(v, 0)).join(', '))] : null));
    }
  }
  tick() { if (this.dirty && this.el.clientWidth) { this.renderer.render(this.scene, this.camera); this.dirty = false; } }
}
function loadGLB(file) {
  if (!cache.glb.has(file)) cache.glb.set(file, new GLTFLoader().loadAsync(DATA + file));
  return cache.glb.get(file);
}


// ---------- views ----------
let vpMain, vpA, vpB, vpPhys;
let highlightIds = new Set();
const allVps = () => [vpMain, vpA, vpB, vpPhys];

function setHighlight(ids) {
  highlightIds = new Set(ids);
  (state.mode === 'designs' ? [vpMain] : state.mode === 'compare' ? [vpA, vpB] : []).forEach((v) => v?.highlight(highlightIds));
  document.querySelectorAll('.result.has-pair').forEach((r) => {
    const pair = r.dataset.pair.split('|');
    r.classList.toggle('active', pair.length === highlightIds.size && pair.every((p) => highlightIds.has(p)));
  });
}
function onPick(id) {
  if (!id) return setHighlight([]);
  setHighlight(highlightIds.size === 1 && highlightIds.has(id) ? [] : [id]);
}

function renderSidebar() {
  const list = $('design-list'); list.replaceChildren();
  const q = state.text.toLowerCase();
  const all = state.index.designs;
  const shown = all.filter((d) => {
    if (state.vtol && (d.morphology?.vtol_method ?? '') !== state.vtol) return false;
    if (!q) return true;
    const hay = [d.id, d.name, d.status, ...Object.values(d.morphology || {})].join(' ').toLowerCase();
    return q.split(/\s+/).every((t) => hay.includes(t));
  });
  $('count').textContent = `${shown.length} of ${all.length}`;
  if (!shown.length) list.append(h('li', { class: 'empty' }, 'No designs match.'));
  for (const d of shown) {
    const sel = state.mode !== 'compare' ? state.selected === d.id : (state.slotA === d.id || state.slotB === d.id);
    const badge = d.pending ? h('span', { class: 'badge pending' }, 'checking…') : d.error ? h('span', { class: 'badge error' }, 'error')
      : h('span', { class: 'badge ' + (d.accepted ? 'accepted' : 'rejected') }, d.accepted ? 'accepted' : 'rejected');
    const tags = Object.entries(d.morphology || {}).map(([k, v]) => h('span', { class: 'tag', title: k }, String(v)));
    const pills = TIERS.map((t) => { const s = d.tiers?.[t] ?? 'NONE'; return h('span', { class: 'pill ' + s, title: `Tier ${t}: ${s}` }, 'T' + t); });
    const li = h('li', { class: 'design-item' + (sel ? ' selected' : ''), tabindex: 0, 'data-id': d.id, onclick: () => choose(d.id), onkeydown: (e) => { if (e.key === 'Enter') choose(d.id); } },
      h('div', { class: 'row1' }, h('div', {}, h('div', { class: 'name' }, d.name || d.id), h('div', { class: 'id' }, d.id)), badge),
      h('div', { class: 'tags' }, h('span', { class: 'tag status' }, d.status), tags),
      h('div', { class: 'pills' }, pills),
      h('div', { class: 'ab' }, ['a', 'b'].map((s) => h('button', { class: state['slot' + s.toUpperCase()] === d.id ? 'on' : '', onclick: (e) => { e.stopPropagation(); assign(s, d.id); } }, s.toUpperCase()))));
    list.append(li);
  }
}


function choose(id) {
  if (state.mode === 'compare') { assign(state.nextSlot, id); return; }
  state.selected = id; syncHash(); renderSidebar(); renderMode();
}
function assign(slot, id) {
  state['slot' + slot.toUpperCase()] = id; state.nextSlot = slot === 'a' ? 'b' : 'a';
  syncHash(); renderSidebar(); renderMode();
}

// ---------- modes / hash / init ----------
async function renderMode() {
  const id = state.mode, el = $('mode-' + id);
  delete el.dataset.ready;
  try {
    const ctx = { state, el, h, fmt, getJSON, byId, vp: { main: vpMain, a: vpA, b: vpB, phys: vpPhys }, setHighlight, studio: state.index.studio === true };
    await (await import('./modes/' + id + '.js')).default(ctx);
  } catch (e) {
    console.warn(e);
    el.append(h('div', { class: 'errbox' }, `${id}: ${e.message}`)); el.dataset.ready = 'error';
  }
}
function setMode(id) {
  state.mode = id; document.body.dataset.mode = id;
  for (const m of MODES) $('mode-' + m).hidden = m !== id;
  document.querySelectorAll('#modes button').forEach((b) => b.classList.toggle('active', b.dataset.mode === id));
  $('mode-hint').textContent = HINTS[id] || '';
  if (id === 'compare') {
    if (!state.slotA) state.slotA = state.selected || state.index.designs[0]?.id;
    if (!state.slotB) state.slotB = state.index.designs.find((d) => d.id !== state.slotA)?.id ?? null;
  }
  syncHash(); renderSidebar();
  requestAnimationFrame(() => allVps().forEach((v) => v.resize()));
  renderMode();
}
function syncHash() {
  const p = new URLSearchParams({ m: state.mode });
  if (state.mode === 'compare') { p.set('a', state.slotA || ''); p.set('b', state.slotB || ''); } else if (state.selected) p.set('d', state.selected);
  try { history.replaceState(null, '', '#' + p.toString()); } catch { /* ignore */ }
}

async function init() {
  vpMain = new Viewport($('vp-main'), { onPick });
  vpA = new Viewport($('vp-a'), { onPick }); vpB = new Viewport($('vp-b'), { onPick }); vpPhys = new Viewport($('vp-phys'));
  (function loop() { requestAnimationFrame(loop); allVps().forEach((v) => v.tick()); })();
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => setTimeout(() => allVps().forEach((v) => v.applyTheme()), 0));
  $('modes').append(...MODES.map((m) => h('button', { 'data-mode': m, role: 'tab', onclick: () => setMode(m) }, LABELS[m])));
  $('filter-text').oninput = (e) => { state.text = e.target.value.trim(); renderSidebar(); };
  $('filter-vtol').onchange = (e) => { state.vtol = e.target.value; renderSidebar(); };
  $('sel-a').onchange = (e) => assign('a', e.target.value); $('sel-b').onchange = (e) => assign('b', e.target.value);

  try {
    const r = await fetch(DATA + 'index.json');
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    state.index = await r.json();
    if (!Array.isArray(state.index.designs)) throw new Error('index.json has no "designs" array');
  } catch (e) {
    $('design-list').append(h('li', { class: 'empty' }, `Could not load data/index.json (${e.message}). Run: plane build-index --out viewer/data`));
    vpMain.message('No data loaded', true);
    return;
  }
  const methods = [...new Set(state.index.designs.map((d) => d.morphology?.vtol_method).filter(Boolean))].sort();
  $('filter-vtol').append(...methods.map((m) => h('option', { value: m }, m)));
  $('generated').textContent = state.index.generated_at ? 'Data generated ' + state.index.generated_at : '';
  for (const sel of [$('sel-a'), $('sel-b')]) sel.append(h('option', { value: '' }, '— none —'), ...state.index.designs.map((d) => h('option', { value: d.id }, d.name || d.id)));

  const p = new URLSearchParams(location.hash.slice(1));
  state.selected = byId(p.get('d')) ? p.get('d') : state.index.designs.find((d) => !d.error)?.id ?? state.index.designs[0]?.id ?? null;
  state.slotA = byId(p.get('a'))?.id ?? null; state.slotB = byId(p.get('b'))?.id ?? null;
  setMode(MODES.includes(p.get('m')) ? p.get('m') : p.has('a') || p.has('b') ? 'compare' : 'designs');
  if (state.index.studio) import('./modes/edit.js').then((m) => m.default(window.planeViewer)).catch((e) => console.warn('studio UI failed to load', e));
}

// Hooks for the local studio app (modes/edit.js). The Pages build never calls these.
async function reload(selectId) {
  const r = await fetch(DATA + 'index.json', { cache: 'no-store' });
  if (!r.ok) return;
  const prev = state.index;
  state.index = await r.json();
  cache.json.clear(); cache.glb.clear();
  for (const sel of [$('sel-a'), $('sel-b')]) sel.replaceChildren(h('option', { value: '' }, '— none —'), ...state.index.designs.map((d) => h('option', { value: d.id }, d.name || d.id)));
  if (selectId && byId(selectId)) { state.selected = selectId; if (state.mode === 'compare') return setMode('designs'); }
  if (!byId(state.selected)) state.selected = state.index.designs[0]?.id ?? null;
  renderSidebar();
  const was = prev?.designs.find((d) => d.id === state.selected), now = byId(state.selected);
  if (state.mode === 'compare' || !was || JSON.stringify(was) !== JSON.stringify(now) || selectId) { syncHash(); renderMode(); }
}
window.planeViewer = { reload, selected: () => state.selected, designs: () => state.index?.designs || [], refresh: () => state.mode === 'designs' && renderMode() };
init();
