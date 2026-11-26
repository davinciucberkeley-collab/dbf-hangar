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
  const m = o.material;
  if (type !== 'propeller') {
    m.metalness = 0.15; m.roughness = 0.55; o.castShadow = true;
    m.polygonOffset = true; m.polygonOffsetFactor = 1; m.polygonOffsetUnits = 1;
  }
  o.userData.baseOpacity = o.material.opacity;
  if (o.geometry.getAttribute('position').count / 3 <= 40000) {
    const line = new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 30), new THREE.LineBasicMaterial({ color: vp.edgeColor(), transparent: true, opacity: 0.6 }));
    line.userData.isEdge = true; line.raycast = () => {}; line.renderOrder = 1; o.add(line);
  }
  const comp = vp.componentOf(o, model);
  if (comp) { o.userData.compId = comp.name; vp.ids.add(comp.name); }
}

export const SKIN_TYPES = ['fuselage', 'wing', 'tail_surface'];

// The one appearance function: selection tint, dimming of the rest, ghosting. Precedence: ghost, dim, base.
export function applyAppearance(vp) {
  const any = vp.highlighted.size > 0;
  vp.model?.traverse((o) => {
    if (!o.isMesh) return;
    const cid = o.userData.compId, on = vp.highlighted.has(cid), m = o.material;
    const ghost = vp.isGhosted(cid, o.userData.compType), base = o.userData.baseOpacity ?? 1, prop = o.userData.compType === 'propeller';
    const wasT = m.transparent, wasD = m.depthWrite;
    let edge = 0.6;
    if (ghost) { m.transparent = true; m.opacity = 0.15; m.depthWrite = false; o.renderOrder = 5; o.castShadow = false; edge = 0.12; }
    else if (any && !on) { m.transparent = true; m.opacity = Math.min(base, 0.28); m.depthWrite = true; o.renderOrder = 0; o.castShadow = !prop; edge = 0.15; }
    else { m.transparent = prop; m.opacity = base; m.depthWrite = true; o.renderOrder = 0; o.castShadow = !prop; }
    m.emissive?.set(on ? 0xffb020 : 0x000000);
    if (m.emissiveIntensity != null) m.emissiveIntensity = on ? 0.55 : 1;
    if (m.transparent !== wasT || m.depthWrite !== wasD) m.needsUpdate = true;
    for (const e of o.children) if (e.userData.isEdge) { e.material.opacity = edge; e.renderOrder = ghost ? 5 : 1; }
  });
  vp.updateOverlay(); vp.dirty = true;
}
