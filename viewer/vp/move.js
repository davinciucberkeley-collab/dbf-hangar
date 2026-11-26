// Move tool: the pending-moves model (edit offsets in vp.transforms) and the translate gizmo.
// Units: PDL positions are body mm; scene is metres, y-up. Every conversion goes through transforms.js.
import * as THREE from 'three';
import { mmToScene, sceneToMm } from './transforms.js';
import { applyAppearance } from './materials.js';

const r1 = (n) => Math.round(n * 10) / 10 || 0;
const mm3 = (v) => Math.round(v * 1000) / 1000; // 1 mm grid in metres
const SCENE_AXIS = { x: 'showX', y: 'showZ', z: 'showY' }; // body axis -> scene axis (y -> -z, z -> y)

export class Mover {
  constructor(vp) {
    this.vp = vp; this.tool = 'select'; this.attached = true; this.axis = null;
    this.tc = null; this.helper = null; this.loading = null; this.dragging = false;
    this.proxy = new THREE.Object3D(); this.last = new THREE.Vector3();
    vp.scene.add(this.proxy);
    this.onKey = (e) => { if (e.key === 'Shift') this.tc?.setTranslationSnap(e.type === 'keydown' ? 0.0001 : 0.001); };
  }
  // ---- model ----
  kids(id) { // id plus every descendant in parts.json (parent links), visual-only parts excluded
    const out = [id], by = new Map();
    for (const p of this.vp.parts?.parts || []) { if (!by.has(p.parent)) by.set(p.parent, []); by.get(p.parent).push(p); }
    for (let i = 0; i < out.length && i < 4096; i++) for (const k of by.get(out[i]) || []) if (!k.visual_only && !out.includes(k.id)) out.push(k.id);
    return out;
  }
  moveBy(id, dMm, { attached = this.attached } = {}) {
    const vp = this.vp, tr = vp.transforms, p = vp.parts?.parts.find((x) => x.id === id);
    if (!tr || !p || p.visual_only || vp.explodeState?.t > 0) return false;
    const d = mmToScene(dMm), had = [...tr.edits.keys()].join();
    for (const t of attached ? this.kids(id) : [id]) {
      const next = (tr.editOf(t) ?? new THREE.Vector3()).add(d);
      tr.setEdit(t, sceneToMm(next).some((v) => v !== 0) ? next : null);
    }
    if ([...tr.edits.keys()].join() !== had) applyAppearance(vp); // the outline set changed
    vp.dirty = true;
    this.sync(); vp.emit();
    return true;
  }
  pending() {
    const tr = this.vp.transforms, out = [];
    if (!tr || !this.vp.parts) return out;
    for (const p of this.vp.parts.parts) {
      const e = tr.editOf(p.id);
      if (!e) continue;
      const delta = sceneToMm(e);
      if (delta.every((v) => v === 0)) continue;
      out.push({ id: p.id, from_mm: [...p.position_mm], to_mm: p.position_mm.map((v, i) => r1(v + delta[i])), delta_mm: delta });
    }
    return out;
  }
  revert() {
    const tr = this.vp.transforms;
    if (tr) for (const id of [...tr.edits.keys()]) tr.setEdit(id, null);
    applyAppearance(this.vp); this.sync(); this.vp.emit();
  }
  clearAfterSave() { this.vp.transforms?.edits.clear(); this.sync(); this.vp.emit(); }
  // ---- tool state ----
  setTool(t) {
    if (t !== 'select' && t !== 'move') return false;
    if (t === 'move' && this.vp.explodeState?.t > 0) return false;
    this.tool = t;
    if (t === 'move') this.ensure();
    this.sync(); this.vp.emit();
    return true;
  }
  lockAxis(a) { this.axis = SCENE_AXIS[a] ? a : null; this.applyAxes(); this.vp.emit(); }
  applyAxes() {
    if (!this.tc) return;
    for (const k of ['showX', 'showY', 'showZ']) this.tc[k] = !this.axis || SCENE_AXIS[this.axis] === k;
    this.vp.dirty = true;
  }
  busy() { return this.dragging || (!!this.tc?.object && this.tc.axis != null); }
  // selected parts the gizmo moves: movable, drawn, not hidden, and (when attached) not below another selected part
  primaries() {
    const vp = this.vp, sel = [...vp.highlighted], by = new Map((vp.parts?.parts || []).map((p) => [p.id, p]));
    const ok = sel.filter((id) => by.has(id) && !by.get(id).visual_only && vp.ids.has(id) && !vp.hidden.has(id));
    if (!this.attached) return ok;
    return ok.filter((id) => { for (let q = by.get(by.get(id).parent), n = 0; q && n < 256; q = by.get(q.parent), n++) if (ok.includes(q.id)) return false; return true; });
  }
  target() { return this.tool === 'move' && !(this.vp.explodeState?.t > 0) ? this.primaries()[0] ?? null : null; }
  place() {
    const ids = this.primaries().filter((id) => this.vp.centres?.get(id));
    if (!ids.length) return;
    const c = new THREE.Vector3();
    for (const id of ids) c.add(this.vp.centres.get(id)).add(this.vp.transforms.editOf(id) ?? new THREE.Vector3());
    c.divideScalar(ids.length);
    this.proxy.position.set(mm3(c.x), mm3(c.y), mm3(c.z)); // on the mm grid so the first snapped step is a whole millimetre
    this.proxy.updateMatrixWorld(true);
    this.last.copy(this.proxy.position);
  }
  sync() {
    const vp = this.vp;
    if (!this.tc) { if (this.tool === 'move') this.ensure(); return; }
    if (!this.target()) { this.tc.detach(); vp.dirty = true; return; }
    if (!this.dragging) this.place();
    this.tc.attach(this.proxy); this.applyAxes(); vp.dirty = true;
  }
  ensure() {
    if (this.tc || this.loading) return this.loading;
    const vp = this.vp;
    this.loading = import('three/addons/controls/TransformControls.js').then(({ TransformControls }) => {
      if (vp.dead) return;
      const tc = new TransformControls(vp.camera, vp.renderer.domElement);
      tc.setMode('translate'); tc.setTranslationSnap(0.001); tc.setSize(0.8);
      this.helper = tc.getHelper(); vp.scene.add(this.helper);
      tc.addEventListener('change', () => { vp.dirty = true; });
      tc.addEventListener('dragging-changed', (e) => { this.dragging = !!e.value; vp.controls.enabled = !e.value; if (e.value) this.last.copy(this.proxy.position); else this.sync(); });
      tc.addEventListener('objectChange', () => this.drag());
      document.addEventListener('keydown', this.onKey); document.addEventListener('keyup', this.onKey);
      this.tc = tc; this.sync();
    });
    return this.loading;
  }
  drag() {
    const inc = sceneToMm(this.proxy.position.clone().sub(this.last));
    this.last.copy(this.proxy.position);
    if (!inc.some((v) => v !== 0)) return;
    for (const id of this.primaries()) this.vp.moveBy(id, inc, { attached: this.attached });
  }
  dispose() {
    document.removeEventListener('keydown', this.onKey); document.removeEventListener('keyup', this.onKey);
    if (this.tc) { this.tc.detach(); this.vp.scene.remove(this.helper); this.tc.dispose(); this.helper = null; this.tc = null; }
    this.vp.scene.remove(this.proxy);
  }
}
