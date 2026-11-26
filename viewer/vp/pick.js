// Ray picking: first visible hit that belongs to a named component.
import * as THREE from 'three';

// three's Raycaster does not test `visible`: a hidden component node (or any ancestor) must not be pickable.
function isPickable(o, model) {
  for (let n = o; n && n !== model.parent; n = n.parent) if (n.visible === false) return false;
  return true;
}

// Ordered ray hits, one per pickable component, nearest first.
export function hitsAlong(vp, raycaster) {
  const out = [], seen = new Set();
  for (const i of raycaster.intersectObject(vp.model, true)) {
    const id = i.object.userData.compId;
    if (!id || i.object.userData.isEdge || seen.has(id) || !isPickable(i.object, vp.model)) continue;
    if (vp.isGhosted(id, i.object.userData.compType)) continue;
    if (vp.sectionState && vp.clipPlane.distanceToPoint(i.point) < 0) continue;
    seen.add(id); out.push({ id, point: i.point, distance: i.distance });
  }
  return out;
}

// Alt-click: the same spot again moves one part further back; a new spot starts at the front.
export function cycleSelect(vp, hits, key) {
  if (!hits.length) { vp.cycle = null; vp.select([]); return null; }
  const index = vp.cycle && vp.cycle.key === key ? (vp.cycle.index + 1) % hits.length : 0;
  vp.cycle = { key, index };
  vp.select([hits[index].id]);
  return hits[index].id;
}

function rayAt(vp, e) {
  const r = vp.renderer.domElement.getBoundingClientRect();
  vp.ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), vp.camera);
  return vp.ray;
}

export function hitAt(vp, e) {
  if (!vp.model) return null;
  return hitsAlong(vp, rayAt(vp, e))[0]?.id ?? null;
}

export function pickAt(vp, e) {
  if (!vp.model) return;
  if (e.altKey) {
    const key = [Math.round(e.clientX / 4) * 4, Math.round(e.clientY / 4) * 4].join(',');
    cycleSelect(vp, hitsAlong(vp, rayAt(vp, e)), key);
    return;
  }
  vp.onPick?.(hitAt(vp, e), vp, e);
}
