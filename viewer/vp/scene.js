// One 3D viewport = one WebGL renderer, scene, camera and controls.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { h, fmt, getJSON } from '../lib.js';
import { loadGLB, disposeModel } from './loader.js';
import { prepareMesh, highlight } from './materials.js';
import { pickAt } from './pick.js';

const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const mmToScene = ([x, y, z]) => new THREE.Vector3(x / 1000, z / 1000, -y / 1000); // body z-up mm -> glTF y-up m

export class Viewport {
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
    this.ro = new ResizeObserver(() => this.resize()); this.ro.observe(el);
    this.applyTheme(); this.resize();
  }
  applyTheme() {
    this.scene.background = new THREE.Color(cssVar('--vp-bg') || '#e9ecf1'); this.dirty = true;
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
    disposeModel(this.root); this.ids.clear(); this.highlighted.clear(); this.cg = null; this.mass = null;
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
      model.traverse((o) => prepareMesh(o, model, this));
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
  pick(e) { pickAt(this, e); }
  highlight(ids) { highlight(this, ids); }
  info() {
    const i = this.renderer.info;
    return { geometries: i.memory.geometries, textures: i.memory.textures, calls: i.render.calls, triangles: i.render.triangles, canvases: document.querySelectorAll('canvas').length, design: this.mountInfo?.id ?? null };
  }
  dispose() {
    this.dead = true; this.ro.disconnect(); this.token = Symbol();
    disposeModel(this.root);
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
  tick() { if (!this.dead && this.dirty && this.el.clientWidth) { this.renderer.render(this.scene, this.camera); this.dirty = false; } }
}
