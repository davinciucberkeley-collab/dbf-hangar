// View cube: six faces that turn with the camera; a click on a face jumps to that standard view.
// Scene axes: Front = +x, Back = -x, Top = +y, Bottom = -y, Left = +z, Right = -z.

// CSS y points down, so the camera rotation is conjugated by diag(1, -1, 1): matrix3d(e0, -e1, e2, 0, -e4, e5, -e6, 0, e8, -e9, e10, 0, 0, 0, 0, 1).
// The faces are laid out as scene axes with y flipped (top = rotateX(90deg), front = rotateY(90deg)); the tests decide this sign pattern.
export function updateCube(camera, inner) {
  if (!inner) return;
  camera.updateMatrixWorld();
  const e = camera.matrixWorldInverse.elements;
  inner.style.transform = `matrix3d(${e[0]}, ${-e[1]}, ${e[2]}, 0, ${-e[4]}, ${e[5]}, ${-e[6]}, 0, ${e[8]}, ${-e[9]}, ${e[10]}, 0, 0, 0, 0, 1)`;
}

export function bindCube(vp, cube) {
  for (const b of cube.querySelectorAll('.cube-face')) b.addEventListener('click', () => vp.view(b.dataset.view));
}
