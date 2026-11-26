// Ray picking: first visible hit that belongs to a named component.
import * as THREE from 'three';

// three's Raycaster does not test `visible`: a hidden component node (or any ancestor) must not be pickable.
function isPickable(o, model) {
  for (let n = o; n && n !== model.parent; n = n.parent) if (n.visible === false) return false;
  return true;
}

export function hitAt(vp, e) {
  if (!vp.model) return null;
  const r = vp.renderer.domElement.getBoundingClientRect();
  vp.ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), vp.camera);
  const hit = vp.ray.intersectObject(vp.model, true).find((i) => i.object.userData.compId && isPickable(i.object, vp.model));
  return hit ? hit.object.userData.compId : null;
}

export function pickAt(vp, e) {
  if (!vp.model) return;
  vp.onPick?.(hitAt(vp, e), vp, e);
}
