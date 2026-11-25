// Ray picking: first hit that belongs to a named component.
import * as THREE from 'three';

export function pickAt(vp, e) {
  if (!vp.model) return;
  const r = vp.renderer.domElement.getBoundingClientRect();
  vp.ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), vp.camera);
  const hit = vp.ray.intersectObject(vp.model, true).find((i) => i.object.userData.compId);
  vp.onPick?.(hit ? hit.object.userData.compId : null, vp);
}
