"""Geometry kernel: a thin millimetre adapter over the CAD-body builders in importers/dbf_geometry.py.

All lengths mm, angles degrees. The importer works in metres, so every input is divided by 1000 here; its output is mm.
Every function returns a watertight mesh with positive volume or raises GeometryError.
"""
from __future__ import annotations

import math

import trimesh

from hangar.importers.dbf_geometry import GeometryError, _boolean, _clean, body_mesh

__all__ = ["GeometryError", "box", "tube", "prism", "loft", "revolve", "union", "difference",
           "volume_mm3", "require_solid", "ngon_area"]

Mesh = trimesh.Trimesh
_PLANE_AXIS = {"xy": "Z", "xz": "Y", "yz": "X"}


def _m(v) -> float:
    return float(v) / 1000.0


def _axis(axis: str) -> str:
    a = str(axis).upper()
    if a not in ("X", "Y", "Z"):
        raise GeometryError(f"axis must be x, y or z, got {axis!r}")
    return a


def volume_mm3(mesh: Mesh) -> float:
    return abs(float(mesh.volume))


def require_solid(mesh: Mesh, what: str) -> Mesh:
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0 or not (mesh.is_watertight and mesh.is_volume):
        raise GeometryError(f"{what}: not watertight / not a volume / zero volume")
    if abs(float(mesh.volume)) <= 0:
        raise GeometryError(f"{what}: not watertight / not a volume / zero volume")
    return mesh


def ngon_area(radius: float, n: int = 48) -> float:
    return 0.5 * n * radius * radius * math.sin(2 * math.pi / n)


def box(size, center=(0.0, 0.0, 0.0)) -> Mesh:
    if any(float(s) <= 0 for s in size):
        raise GeometryError("box: size must be positive")
    m = trimesh.creation.box(extents=[float(s) for s in size])
    m.apply_translation([float(c) for c in center])
    return require_solid(_clean(m), "box")


def revolve(axis: str, center, profile) -> Mesh:
    shape = {"kind": "revolve", "axis": _axis(axis), "center": [_m(c) for c in center],
             "profile": [(_m(a), _m(r)) for a, r in profile]}
    return require_solid(body_mesh(shape), "revolve")


def tube(axis: str, center, length: float, outer_d: float, inner_d: float = 0.0) -> Mesh:
    if length <= 0 or outer_d <= 0 or inner_d < 0 or inner_d >= outer_d:
        raise GeometryError("tube: need length > 0 and 0 <= inner_d < outer_d")
    a, ro, ri = -length / 2.0, outer_d / 2.0, inner_d / 2.0
    b = length / 2.0
    prof = [(a, ro), (b, ro), (b, ri), (a, ri)] if ri > 0 else [(a, 0.0), (a, ro), (b, ro), (b, 0.0)]
    return revolve(axis, center, prof)


def prism(outline, holes=(), *, plane: str, offset: float, depth: float) -> Mesh:
    p = str(plane).lower()
    if p not in _PLANE_AXIS:
        raise GeometryError(f"plane must be xy, xz or yz, got {plane!r}")
    loops = [[(_m(u), _m(v)) for u, v in outline]] + [[(_m(u), _m(v)) for u, v in h] for h in holes]
    shape = {"kind": "prism", "axis": _PLANE_AXIS[p], "offset": _m(offset), "depth": _m(depth), "loops": loops}
    return require_solid(body_mesh(shape), "prism")


def loft(axis: str, sections) -> Mesh:
    shape = {"kind": "loft", "axis": _axis(axis),
             "sections": [(_m(o), [(_m(u), _m(v)) for u, v in loop]) for o, loop in sections]}
    return require_solid(body_mesh(shape), "loft")


def union(meshes) -> Mesh:
    meshes = list(meshes)
    if not meshes:
        raise GeometryError("union of nothing")
    if len(meshes) == 1:
        return require_solid(meshes[0], "union")
    return require_solid(_boolean("union", meshes), "union")


def difference(base: Mesh, tools, f64: bool = False) -> Mesh:
    tools = list(tools)
    if not tools:
        return require_solid(base, "difference")
    return require_solid(_boolean("difference", [base, *tools], f64=f64), "difference")
