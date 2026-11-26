// The only code that writes component node matrices: rest -> edit offset -> explode offset -> mechanism.
// node.matrix = T(explode) * T(edit) * mech. Body mm (z-up) <-> scene m (y-up) conversion lives here too.
import * as THREE from 'three';

export const mmToScene = ([dx, dy, dz]) => new THREE.Vector3(dx / 1000, dz / 1000, -dy / 1000);
const r1 = (n) => Math.round(n * 10) / 10 || 0; // 0.1 mm; also turns -0 into 0
export function sceneToMm(v) {
  const [x, y, z] = Array.isArray(v) ? v : [v.x, v.y, v.z];
  return [r1(x * 1000), r1(-z * 1000), r1(y * 1000)];
}

const EXPLODE_FACTOR = 1.5;
const tmp = new THREE.Matrix4();

export class Transforms {
  constructor(vp) { this.vp = vp; this.edits = new Map(); this.explodes = new Map(); this.mechs = new Map(); }
  setEdit(id, v) { this.#put(this.edits, id, v ? v.clone() : null); }
  setExplode(id, v) { this.#put(this.explodes, id, v ? v.clone() : null); }
  setMech(id, m) { // copies into a matrix this class owns, so callers may reuse theirs every frame
    const had = this.mechs.get(id);
    if (m && had) { had.copy(m); this.recompose(id); } else this.#put(this.mechs, id, m ? m.clone() : null);
  }
  #put(map, id, val) { if (val) map.set(id, val); else map.delete(id); this.recompose(id); }
  clearAll() {
    const ids = new Set([...this.edits.keys(), ...this.explodes.keys(), ...this.mechs.keys()]);
    this.edits.clear(); this.explodes.clear(); this.mechs.clear();
    for (const id of ids) this.recompose(id);
  }
  editOf(id) { return this.edits.get(id) ?? null; }
  offset(id) { const v = this.explodes.get(id); return v ? [v.x, v.y, v.z] : [0, 0, 0]; }
  isMoved(id) {
    const node = this.vp.model?.getObjectByName(id);
    if (!node) return false;
    const e = node.matrix.elements;
    for (let i = 0; i < 16; i++) if (Math.abs(e[i] - (i % 5 === 0 ? 1 : 0)) > 1e-12) return true;
    return false;
  }
  recompose(id) {
    const node = this.vp.model?.getObjectByName(id);
    if (!node) return;
    node.matrixAutoUpdate = false;
    const ex = this.explodes.get(id), ed = this.edits.get(id), me = this.mechs.get(id);
    if (!ex && !ed && !me) node.matrix.identity();
    else {
      if (ex) node.matrix.makeTranslation(ex.x, ex.y, ex.z); else node.matrix.identity();
      if (ed) node.matrix.multiply(tmp.makeTranslation(ed.x, ed.y, ed.z));
      if (me) node.matrix.multiply(me);
    }
    node.matrixWorldNeedsUpdate = true;
    this.vp.dirty = true;
  }
}

// Explode offsets (scene m) per part id. parts = parts.json; centres = Map id -> world Vector3 of drawn parts.
// hierarchy (D109): a whole subassembly moves as one unit: every part takes t * (C(anc) - C(root)) of its ancestor
//   at depth min(level, own depth); level 'all' uses the top-level child of the root (depth 1).
// radial: every part (down to the level) moves t * (C(p) - C(root)) on its own; deeper parts follow their parent.
export function explodeOffsets(parts, centres, fallback, t, level = 'all', strategy = 'hierarchy') {
  const list = [...parts.parts].sort((a, b) => a.depth - b.depth);
  const byId = new Map(list.map((p) => [p.id, p]));
  const rootC = centres.get(parts.root) ?? fallback;
  const C = (p) => { for (let q = p, n = 0; q && n < 256; q = byId.get(q.parent), n++) { const c = centres.get(q.id); if (c) return c; } return rootC; };
  const k = t * EXPLODE_FACTOR, D = new Map(), zero = new THREE.Vector3();
  const up = (p, depth) => { let q = p, n = 0; while (q && q.depth > depth && n++ < 256) q = byId.get(q.parent) ?? q; return q; };
  const L = level === 'all' ? 1 : +level, Lr = level === 'all' ? Math.max(0, ...list.map((p) => p.depth)) : L;
  for (const p of list) {
    const parent = byId.get(p.parent);
    let d;
    if (p.id === parts.root) d = zero;
    else if (strategy === 'radial') d = p.depth <= Lr ? C(p).clone().sub(rootC).multiplyScalar(k) : (parent && D.get(parent.id)) || zero;
    else d = C(up(p, L)).clone().sub(rootC).multiplyScalar(k);
    D.set(p.id, d);
  }
  return D;
}
