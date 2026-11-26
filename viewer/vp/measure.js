// Measure tool: two clicks give a point to point distance in body mm, drawn as two markers, a line and a label.
import * as THREE from 'three';
import { h, fmt } from '../lib.js';
import { sceneToMm } from './transforms.js';

const COLOUR = 0xf97316;
const r1 = (n) => Math.round(n * 10) / 10 || 0;

export class Measure {
  constructor(vp) { this.vp = vp; this.a = null; this.b = null; this.objs = []; this.label = null; }
  active() { return !!this.a; }
  click(hit) {
    if (!hit) return;
    if (this.b) this.clear();
    if (!this.a) { this.a = hit.point.clone(); this.mark(this.a); }
    else { this.b = hit.point.clone(); this.mark(this.b); this.line(); this.showLabel(); }
    this.vp.dirty = true;
  }
  mark(p) {
    const r = (this.vp.size?.length() || 1) * 0.006;
    const m = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), new THREE.MeshBasicMaterial({ color: COLOUR, depthTest: false, transparent: true }));
    m.position.copy(p); m.renderOrder = 10; this.vp.root.add(m); this.objs.push(m);
  }
  line() {
    const g = new THREE.BufferGeometry().setFromPoints([this.a, this.b]);
    const l = new THREE.Line(g, new THREE.LineBasicMaterial({ color: COLOUR, depthTest: false, transparent: true }));
    l.renderOrder = 10; this.vp.root.add(l); this.objs.push(l);
  }
  result() {
    if (!this.a || !this.b) return null;
    return { a_mm: sceneToMm(this.a), b_mm: sceneToMm(this.b), distance_mm: r1(this.a.distanceTo(this.b) * 1000) };
  }
  showLabel() {
    const r = this.result(), d = r.b_mm.map((v, i) => r1(v - r.a_mm[i]));
    this.label = h('div', { class: 'measure-label', 'data-testid': 'measure-label' },
      h('b', {}, fmt(r.distance_mm, 1) + ' mm'), h('small', {}, `Δx ${fmt(d[0], 1)} Δy ${fmt(d[1], 1)} Δz ${fmt(d[2], 1)}`));
    this.vp.el.parentElement.append(this.label);
    this.update();
  }
  update() {
    const l = this.label;
    if (!l) return;
    const mid = this.a.clone().add(this.b).multiplyScalar(0.5).project(this.vp.camera);
    const cv = this.vp.renderer.domElement, rc = cv.getBoundingClientRect(), rw = this.vp.el.parentElement.getBoundingClientRect();
    l.hidden = mid.z > 1 || mid.z < -1;
    l.style.left = rc.left - rw.left + ((mid.x + 1) / 2) * rc.width + 'px';
    l.style.top = rc.top - rw.top + ((1 - mid.y) / 2) * rc.height + 'px';
  }
  clear() {
    for (const o of this.objs) { o.removeFromParent(); o.geometry.dispose(); o.material.dispose(); }
    this.objs = []; this.a = this.b = null;
    this.label?.remove(); this.label = null;
    this.vp.dirty = true;
  }
  dispose() { this.clear(); }
}
