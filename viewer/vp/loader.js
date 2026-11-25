// GLB loading (cached) and disposal of GPU resources.
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { cache } from '../lib.js';

const DATA = 'data/';
const TEX = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap', 'aoMap'];

export function loadGLB(file) {
  if (!cache.glb.has(file)) cache.glb.set(file, new GLTFLoader().loadAsync(DATA + file));
  return cache.glb.get(file);
}

export function disposeModel(root) {
  root.traverse((o) => {
    if (!o.geometry) return; // meshes and the GridHelper (LineSegments)
    o.geometry?.dispose();
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      if (!m) continue;
      for (const k of TEX) m[k]?.dispose?.();
      m.dispose();
    }
  });
  root.clear();
}
