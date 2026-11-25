// Per-mesh material setup and component highlight.
import * as THREE from 'three';

export function prepareMesh(o, model, vp) {
  if (!o.isMesh) return;
  o.material = o.material.clone();
  o.material.side = THREE.DoubleSide;
  const type = o.userData.type ?? o.parent?.userData?.type;
  o.userData.compType = type;
  const a = o.geometry.getAttribute('color');
  if (type === 'propeller' || (a && a.itemSize === 4)) { o.material.transparent = type === 'propeller'; }
  o.userData.baseOpacity = o.material.opacity;
  const comp = vp.componentOf(o, model);
  if (comp) { o.userData.compId = comp.name; vp.ids.add(comp.name); }
}

export function highlight(vp, ids) {
  vp.highlighted = new Set([...ids].filter((i) => vp.ids.has(i)));
  const any = vp.highlighted.size > 0;
  vp.model?.traverse((o) => {
    if (!o.isMesh) return;
    const on = vp.highlighted.has(o.userData.compId);
    o.material.emissive?.set(on ? 0xffb020 : 0x000000);
    if (o.material.emissiveIntensity != null) o.material.emissiveIntensity = on ? 0.55 : 1;
    const base = o.userData.baseOpacity ?? 1;
    o.material.transparent = o.userData.compType === 'propeller' || (any && !on);
    o.material.opacity = any && !on ? Math.min(base, 0.28) : base;
    o.material.needsUpdate = true;
  });
  vp.updateOverlay(); vp.dirty = true;
}
