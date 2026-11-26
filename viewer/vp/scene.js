// One 3D viewport = one WebGL renderer, scene, camera and controls.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { h, fmt, getJSON } from '../lib.js';
import { loadGLB, disposeModel } from './loader.js';
import { prepareMesh, applyAppearance, INTERNAL_TYPES, STATUS_COLOUR, NEUTRAL, MASS_LO, MASS_HI, maxMass } from './materials.js';
import { pickAt, hitAt, hitsAlong, cycleSelect } from './pick.js';
import { Transforms, mmToScene, explodeOffsets } from './transforms.js';
import { Mover } from './move.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

export class Viewport {
  constructor(el, { onPick, onSelect, onModel, onDiscard } = {}) {
    this.el = el; this.onPick = onPick; this.onSelect = onSelect; this.onModel = onModel; this.onDiscard = onDiscard; this.subs = new Set(); this.keepNext = null; this.parts = null; this.centres = null; this.transforms = null; this.explodeState = null; this.hidden = new Set(); this.ids = new Set(); this.highlighted = new Set(); this.ghost = new Set(); this.types = new Map(); this.xrayOn = false; this.colourMode = 'type'; this.statusMap = new Map(); this.focusSaved = null; this.focusKey = null; this.sectionState = null; this.cycle = null; this.dirty = true;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    this.renderer.localClippingEnabled = true; this.clipPlane = new THREE.Plane();
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    el.append(this.renderer.domElement);
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.01, 50);
    this.renderer.toneMapping = THREE.NeutralToneMapping ?? THREE.ACESFilmicToneMapping; this.renderer.toneMappingExposure = 1.0;
    this.renderer.shadowMap.enabled = true; this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    const pm = new THREE.PMREMGenerator(this.renderer), room = new RoomEnvironment();
    this.scene.environment = pm.fromScene(room, 0.04).texture; this.scene.environmentIntensity = 0.8; room.dispose(); pm.dispose();
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x556070, 0.35));
    const sun = this.sun = new THREE.DirectionalLight(0xffffff, 1.8); sun.position.set(2, 3, 1.5); this.scene.add(sun);
    sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.002;
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true; this.controls.dampingFactor = 0.12;
    this.controls.addEventListener('change', () => (this.dirty = true));
    this.root = new THREE.Group(); this.scene.add(this.root);
    this.mover = new Mover(this);
    this.ray = new THREE.Raycaster();
    this.overlay = h('div', { class: 'vp-overlay', hidden: true });
    this.msg = h('div', { class: 'vp-msg' });
    this.legend = h('div', { class: 'vp-legend', hidden: true }, h('span', { class: 'dot' }), 'CG');
    this.legend2 = h('div', { class: 'vp-legend2', 'data-testid': 'legend', hidden: true });
    el.append(this.overlay, this.msg, this.legend, this.legend2);
    let down = null;
    const cv = this.renderer.domElement;
    cv.addEventListener('pointerdown', (e) => (down = [e.clientX, e.clientY]));
    cv.addEventListener('pointerup', (e) => {
      if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4 || this.mover.busy()) return;
      this.pickEvent(e);
    });
    cv.addEventListener('dblclick', (e) => { this.model?.updateMatrixWorld(true); const id = hitAt(this, e); if (id) { this.select([id]); this.fitTo([id]); } });
    this.ro = new ResizeObserver(() => this.resize()); this.ro.observe(el);
    this.applyTheme(); this.resize();
  }
  applyTheme() {
    this.scene.background = new THREE.Color(cssVar('--vp-bg') || '#e9ecf1');
    const ec = this.edgeColor();
    this.root.traverse((o) => { if (o.userData.isEdge && !o.userData.orange) o.material.color.set(ec); });
    this.dirty = true;
  }
  edgeColor() { return cssVar('--edge') || '#27303f';
  }
  resize() {
    if (this.dead) return;
    const w = this.el.clientWidth, hgt = this.el.clientHeight;
    if (!w || !hgt) return;
    this.renderer.setSize(w, hgt, false);
    this.camera.aspect = w / hgt; this.camera.updateProjectionMatrix(); this.dirty = true;
  }
  message(text, err = false) {
    this.msg.textContent = text || ''; this.msg.className = 'vp-msg' + (err ? ' err' : ''); this.msg.hidden = !text;
  }
  clear() {
    this.cancelAnim?.(); disposeModel(this.root); this.ids.clear(); this.highlighted.clear(); this.hidden.clear(); this.ghost.clear(); this.types.clear(); this.cycle = null; this.cg = null; this.mass = null; this.statusMap = new Map(); this.focusSaved = null; this.focusKey = null;
    this.transforms = null; this.centres = null; this.parts = null; this.explodeState = null;
    this.overlay.hidden = true; this.legend.hidden = true; this.dirty = true;
    this.mover.sync(); this.emit();
  }
  subscribe(fn) { this.subs.add(fn); return () => this.subs.delete(fn); } // called on pending moves, tool and explode changes
  emit() { for (const fn of [...this.subs]) fn(this); }
  // what a reload of the same design keeps: selection, hidden and ghost sets, pending moves
  snapshot() {
    const tr = this.transforms;
    return { selection: [...this.highlighted], hidden: [...this.hidden], ghost: [...this.ghost], ids: [...this.ids].sort().join(), edits: tr ? [...tr.edits].map(([id, v]) => [id, v.clone()]) : [] };
  }
  restore(k) {
    this.setHidden(k.hidden, true); this.ghost = new Set(k.ghost.filter((i) => this.ids.has(i)));
    if (k.edits.length) {
      if (k.ids === [...this.ids].sort().join()) for (const [id, v] of k.edits) this.transforms.setEdit(id, v);
      else this.onDiscard?.('Unsaved moves were discarded because the design changed on disk.');
    }
    applyAppearance(this);
    if (k.selection.length) this.select(k.selection);
  }
  move(id, dMm) { return this.moveBy(id, dMm, { attached: this.mover.attached }); }
  moveBy(id, dMm, opts) { return this.mover.moveBy(id, dMm, opts); }
  pending() { return this.mover.pending(); }
  revertMoves() { this.mover.revert(); }
  clearMovesAfterSave() { this.mover.clearAfterSave(); } // drops the edits without redrawing: the reload that follows replaces the model
  setTool(t) { return this.mover.setTool(t); }
  setAttached(on) { this.mover.attached = !!on; }
  lockAxis(a) { this.mover.lockAxis(a); }
  axisLocked() { return !!this.mover.axis; }
  async show(design) {
    const token = (this.token = Symbol());
    this.clear();
    if (!design) return this.message('Select a design');
    if (design.pending) return this.message('Checking this design… the model appears when it is done.');
    if (design.error) return this.message('No model: ' + design.error, true);
    if (!design.glb) return this.message('No GLB for this design', true);
    this.message('Loading…');
    const same = this.mountInfo?.id === design.id; // a reload of the open design keeps the camera and what the person had set
    if (!same) { this.keepNext = null; this.colourMode = 'type'; }
    try {
      const [gltf, mass, parts] = await Promise.all([loadGLB(design.glb), design.mass ? getJSON(design.mass).catch(() => null) : null, design.parts ? getJSON(design.parts).catch(() => null) : null]);
      if (token !== this.token) return;
      const model = gltf.scene.clone(true);
      this.mass = new Map((mass?.per_component || []).map((c) => [c.id, c]));
      model.traverse((o) => prepareMesh(o, model, this));
      this.root.add(model);
      this.model = model;
      const box = new THREE.Box3().setFromObject(model);
      this.box0 = box.clone();
      this.size = box.getSize(new THREE.Vector3()); this.center = box.getCenter(new THREE.Vector3());
      const diag = this.size.length() || 1;
      const grid = this.makeGrid(box, diag); this.root.add(grid, this.makeGround(grid.position, diag));
      this.setupSun(diag);
      const cgmm = design.cg_mm || mass?.cg_mm;
      if (cgmm) this.addCG(mmToScene(cgmm), diag);
      this.mountInfo = design;
      model.updateMatrixWorld(true);
      this.centres = new Map();
      for (const id of this.ids) { const b = new THREE.Box3().setFromObject(model.getObjectByName(id)); if (!b.isEmpty()) this.centres.set(id, b.getCenter(new THREE.Vector3())); }
      this.parts = parts?.parts ? parts : null;
      this.transforms = new Transforms(this);
      if (this.parts) this.explodeState = { t: 0, level: 'all', strategy: 'hierarchy' };
      if (!same) this.fit(diag);
      applyAppearance(this); this.applySection();
      this.message('');
      this.onModel?.(this);
      const keep = this.keepNext; this.keepNext = null;
      if (keep) this.restore(keep);
      this.updateLegend(); this.mover.sync(); this.emit();
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
  makeGround(pos, diag) {
    const g = new THREE.Mesh(new THREE.PlaneGeometry(diag * 2.4, diag * 2.4), new THREE.ShadowMaterial({ opacity: 0.22 }));
    g.rotation.x = -Math.PI / 2; g.position.copy(pos); g.receiveShadow = true; g.renderOrder = -1;
    return g;
  }
  setupSun(diag) {
    const s = this.sun, c = s.shadow.camera;
    c.left = c.bottom = -diag; c.right = c.top = diag; c.near = 0.01; c.far = diag * 6;
    s.position.copy(this.center).add(new THREE.Vector3(0.4, 1, 0.3).normalize().multiplyScalar(diag * 2));
    s.target.position.copy(this.center); s.target.updateMatrixWorld(); c.updateProjectionMatrix();
  }
  addCG(p, diag) {
    const r = diag * 0.018;
    const mat = new THREE.MeshBasicMaterial({ color: 0xd6119b, depthTest: false, transparent: true });
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
  pickEvent(e) { this.model?.updateMatrixWorld(true); pickAt(this, e); }
  pick(id) { this.onPick?.(id, this, null); } // same call as a plain click on that part
  highlight(ids) { this.highlighted = new Set([...ids].filter((i) => this.ids.has(i))); applyAppearance(this); this.mover.sync(); }
  // The single selection setter: the selection is the highlighted set.
  select(ids, { add = false } = {}) {
    this.highlight(add ? [...this.highlighted, ...ids] : ids);
    this.onSelect?.(this.highlighted);
  }
  setHidden(ids, hidden) {
    for (const id of ids) {
      const node = this.model?.getObjectByName(id);
      if (!node || !this.ids.has(id)) continue;
      node.visible = !hidden;
      if (hidden) this.hidden.add(id); else this.hidden.delete(id);
    }
    this.dirty = true; this.onSelect?.(this.highlighted);
  }
  isGhosted(id, type) { return this.ghost.has(id) || (this.xrayOn && !INTERNAL_TYPES.includes(type ?? this.types.get(id))); }
  setGhost(ids, on) {
    for (const id of ids) if (this.ids.has(id)) { if (on) this.ghost.add(id); else this.ghost.delete(id); }
    applyAppearance(this); this.onSelect?.(this.highlighted);
  }
  // Colour by type | status | mass (U19.1 B6b); the status map comes from the scorecard (designs.js).
  colourBy(mode) {
    this.colourMode = ['status', 'mass'].includes(mode) ? mode : 'type';
    applyAppearance(this); this.updateLegend(); this.onSelect?.(this.highlighted); this.emit();
  }
  setStatus(map) {
    this.statusMap = map instanceof Map ? map : new Map();
    applyAppearance(this); this.updateLegend(); this.onSelect?.(this.highlighted);
  }
  coloured() {
    const all = [...this.ids];
    if (this.colourMode === 'status') return all.filter((i) => this.statusMap.has(i));
    if (this.colourMode === 'mass') return all.filter((i) => this.mass?.get(i)?.mass_g != null);
    return [];
  }
  updateLegend() {
    const L = this.legend2, m = this.colourMode, hex = (n) => '#' + n.toString(16).padStart(6, '0');
    L.hidden = m === 'type' || !this.model; L.replaceChildren();
    if (L.hidden) return;
    const sw = (c, t) => h('span', { class: 'lg-item' }, h('i', { class: 'lg-sw', style: `background:${hex(c)}` }), t);
    if (m === 'status') {
      const n = (s) => this.coloured().filter((i) => this.statusMap.get(i).status === s).length;
      L.append(sw(STATUS_COLOUR.FAIL, `FAIL ${n('FAIL')}`), sw(STATUS_COLOUR.WARN, `WARN ${n('WARN')}`), sw(NEUTRAL, `no finding ${this.ids.size - this.coloured().length}`), sw(NEUTRAL, `design-level ${this.statusMap.designLevel || 0}`));
    } else {
      L.append(h('span', {}, '0 g'), h('i', { class: 'lg-ramp', style: `background:linear-gradient(90deg,${hex(MASS_LO)},${hex(MASS_HI)})` }), h('span', {}, fmt(maxMass(this), 0) + ' g'));
    }
  }
  // Select parts, frame them and ghost the rest; the previous ghost set comes back on clearFocus.
  focusParts(ids) {
    ids = [...ids].filter((i) => this.ids.has(i));
    if (!ids.length) return;
    if (!this.focusSaved) this.focusSaved = new Set(this.ghost);
    this.focusKey = ids.join('|');
    this.ghost = new Set(this.focusSaved);
    for (const i of this.ids) if (!ids.includes(i)) this.ghost.add(i);
    this.select(ids); this.fitTo(ids);
  }
  clearFocus() {
    if (!this.focusSaved) return;
    this.ghost = new Set(this.focusSaved); this.focusSaved = null; this.focusKey = null;
    this.select([]);
  }
  xray(on) { this.xrayOn = !!on; applyAppearance(this); this.onSelect?.(this.highlighted); }
  // Section plane across the model box along a BODY axis (x, y, z) or null; one shared plane, uncapped.
  section(axis, value = 0.5, flip = false) {
    this.sectionState = axis ? { axis, value, flip: !!flip } : null;
    this.applySection(); this.onSelect?.(this.highlighted);
  }
  applySection() {
    const s = this.sectionState, b = this.box0;
    if (s && b) {
      const sz = b.getSize(new THREE.Vector3()), n = new THREE.Vector3(), p = new THREE.Vector3();
      if (s.axis === 'x') { n.set(1, 0, 0); p.x = b.min.x + s.value * sz.x; }
      else if (s.axis === 'y') { n.set(0, 0, -1); p.z = b.max.z - s.value * sz.z; }
      else { n.set(0, 1, 0); p.y = b.min.y + s.value * sz.y; }
      if (s.flip) n.negate();
      this.clipPlane.setFromNormalAndCoplanarPoint(n, p);
    }
    const planes = s && b ? [this.clipPlane] : null;
    this.model?.traverse((o) => {
      if (!o.isMesh && !o.isLineSegments) return;
      o.material.clippingPlanes = planes; o.material.needsUpdate = true;
    });
    this.dirty = true;
  }
  hits(origin, dir) {
    if (!this.model) return [];
    this.root.updateMatrixWorld(true);
    return hitsAlong(this, new THREE.Raycaster(origin, dir.clone().normalize()));
  }
  pickRay(o, d) { return this.hits(mmToScene(o), mmToScene(d)).map((x) => x.id); }
  cyclePick(o, d) { return cycleSelect(this, this.hits(mmToScene(o), mmToScene(d)), JSON.stringify([o, d])); }
  isolate(ids) {
    const keep = new Set(ids);
    if (!keep.size) return;
    this.setHidden([...this.ids].filter((i) => !keep.has(i)), true);
    this.setHidden([...keep], false);
  }
  showAll() { this.setHidden([...this.hidden], false); }
  // Explode view: t 0..1, level 'all' or 1..max depth, strategy 'hierarchy' | 'radial'. t = 0 restores every part exactly.
  explode(t, level = 'all', strategy = 'hierarchy') {
    if (!this.parts || !this.transforms) return;
    t = Math.min(1, Math.max(0, +t || 0));
    this.explodeState = { t, level, strategy };
    const D = t === 0 ? null : explodeOffsets(this.parts, this.centres, this.center, t, level, strategy);
    for (const id of this.ids) this.transforms.setExplode(id, D?.get(id) ?? null);
    this.mover.sync(); this.emit();
  }
  state() {
    const all = [...this.ids], tr = this.transforms, r6 = (n) => Math.round(n * 1e6) / 1e6 || 0;
    const offsets = {};
    if (tr) for (const id of all) offsets[id] = tr.offset(id).map(r6);
    return { explode: this.explodeState ? { ...this.explodeState } : null, offsets, moved: tr ? all.filter((i) => tr.isMoved(i)) : [], selection: [...this.highlighted], hidden: [...this.hidden], all, visible: all.filter((i) => !this.hidden.has(i)), ghosted: all.filter((i) => this.isGhosted(i)), coloured: this.coloured(), colourBy: this.colourMode, status: Object.fromEntries([...this.statusMap].map(([i, e]) => [i, e.status])), focus: this.focusKey, xray: this.xrayOn, section: this.sectionState ? { ...this.sectionState } : null, tool: this.mover.tool, gizmo: this.mover.target(), pending: this.pending().length };
  }
  fitTo(ids) {
    if (!this.model) return;
    const box = new THREE.Box3();
    for (const id of ids || []) {
      const node = this.hidden.has(id) ? null : this.model.getObjectByName(id);
      if (node) box.expandByObject(node);
    }
    if (box.isEmpty()) box.setFromObject(this.model);
    const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
    const dist = (Math.max(size.x, size.y, size.z, 1e-3) / (2 * Math.tan(THREE.MathUtils.degToRad(this.camera.fov) / 2))) * 1.4;
    const dir = this.camera.position.clone().sub(this.controls.target).normalize();
    this.flyTo(c.clone().add(dir.multiplyScalar(dist)), c, dist);
  }
  view(name) {
    const dirs = { iso: [0.9, 0.55, 1.1], front: [1, 0, 0], back: [-1, 0, 0], top: [0, 1, 0], side: [0, 0, 1] };
    const d = dirs[name];
    if (!d || !this.model) return;
    this.camera.up.set(...(name === 'top' ? [1, 0, 0] : [0, 1, 0]));
    const c = this.controls; // OrbitControls caches the up-axis rotation at construction
    if (c._quat) { c._quat.setFromUnitVectors(this.camera.up, new THREE.Vector3(0, 1, 0)); c._quatInverse.copy(c._quat).invert(); }
    const dir = new THREE.Vector3(...d).normalize();
    this.camera.position.copy(c.target).add(dir.multiplyScalar(this.camera.position.distanceTo(c.target) || 1));
    this.fitTo(this.ids);
  }
  cancelAnim() { if (this.animId) cancelAnimationFrame(this.animId); clearTimeout(this.animTimer); this.animId = 0; }
  flyTo(pos, target, dist) {
    this.cancelAnim();
    this.camera.near = dist / 100; this.camera.far = Math.max(this.camera.far, dist * 20); this.camera.updateProjectionMatrix();
    const p0 = this.camera.position.clone(), t0 = this.controls.target.clone(), start = performance.now();
    const apply = (k) => {
      const e = k * (2 - k);
      this.camera.position.lerpVectors(p0, pos, e); this.controls.target.lerpVectors(t0, target, e);
      this.controls.update(); this.dirty = true;
    };
    const step = (now) => { const k = Math.min(1, (now - start) / 250); apply(k); this.animId = k < 1 ? requestAnimationFrame(step) : 0; };
    this.animId = requestAnimationFrame(step);
    // a browser that withholds animation frames (hidden tab, busy GPU) must still land on the final pose
    this.animTimer = setTimeout(() => { if (this.animId) cancelAnimationFrame(this.animId); this.animId = 0; apply(1); }, 270);
  }
  info() {
    const i = this.renderer.info;
    let edgeSegments = 0;
    this.root.traverse((o) => { if (o.userData.isEdge) edgeSegments += o.geometry.getAttribute('position').count / 2; });
    return { edgeSegments, geometries: i.memory.geometries, textures: i.memory.textures, calls: i.render.calls, triangles: i.render.triangles, canvases: document.querySelectorAll('canvas').length, design: this.mountInfo?.id ?? null };
  }
  dispose() {
    this.dead = true; this.cancelAnim(); this.ro.disconnect(); this.token = Symbol(); this.subs.clear(); this.mover.dispose();
    disposeModel(this.root);
    this.scene.environment?.dispose();
    this.renderer.dispose(); this.renderer.forceContextLoss(); this.renderer.domElement.remove();
    this.overlay.remove(); this.msg.remove(); this.legend.remove();
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
  tick() { if (!this.dead && this.controls.update()) this.dirty = true; if (!this.dead && this.dirty && this.el.clientWidth) { this.renderer.render(this.scene, this.camera); this.dirty = false; } }
}
