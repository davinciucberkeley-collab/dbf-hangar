"""Wires as routed tubes (U16.1 S8): library port lookup, Catmull-Rom curve, tube mesh. Visual only."""
from __future__ import annotations

import numpy as np
import trimesh


class WireError(ValueError):
    pass


def _unit(v):
    n = float(np.linalg.norm(v))
    return np.asarray(v, dtype=float) / n


def port_point(design, cid: str, port: str) -> tuple[np.ndarray, np.ndarray]:
    """Design-frame point (mm) and unit direction of a library-part port on component `cid`."""
    from ..geometry import _transform
    from . import library
    comp = next((c for c in design.components if c["id"] == cid), None)
    if comp is None:
        raise WireError(f"unknown component {cid}")
    g = comp.get("geometry") or {}
    if g.get("generator") != "library_part":
        raise WireError(f"component {cid} is not a library part")
    pid = (g.get("params") or {}).get("part")
    ports = library.load_part(pid).get("ports") or {}
    if not ports:
        raise WireError(f"library part {pid} has no ports")
    if port not in ports:
        raise WireError(f"{port} is not a port of {cid} (ports: {', '.join(ports)})")
    t = _transform(comp)
    p = t[:3, :3] @ np.asarray(ports[port]["point"], dtype=float) + t[:3, 3]
    d = _unit(t[:3, :3] @ np.asarray(ports[port]["direction"], dtype=float))
    return p, d


def curve_points(ctrl, per_segment: int = 8) -> np.ndarray:
    """Uniform Catmull-Rom with reflected end points through the control points: per_segment * (n - 1) + 1 points."""
    c = np.asarray(ctrl, dtype=float)
    n = len(c)
    ext = np.vstack([2 * c[0] - c[1], c, 2 * c[-1] - c[-2]])  # reflected ends: a 2-point curve is a straight line
    out = []
    for i in range(n - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for k in range(per_segment):
            t = k / per_segment
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(c[-1])
    return np.array(out)


def tube_mesh(points, diameter: float, sides: int = 12) -> trimesh.Trimesh:
    pts = np.asarray(points, dtype=float)
    m = len(pts)
    r = diameter / 2
    tang = np.empty_like(pts)
    for i in range(m):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, m - 1)]
        tang[i] = _unit(b - a)
    ref = np.array([0.0, 0.0, 1.0])
    if abs(tang[0] @ ref) > 0.9:
        ref = np.array([1.0, 0.0, 0.0])
    n = _unit(ref - (ref @ tang[0]) * tang[0])
    verts = []
    for i in range(m):
        if i:
            n = _unit(n - (n @ tang[i]) * tang[i])
        b = np.cross(tang[i], n)
        for j in range(sides):
            a = 2 * np.pi * j / sides
            verts.append(pts[i] + r * (np.cos(a) * n + np.sin(a) * b))
    verts.append(pts[0])
    verts.append(pts[-1])
    faces = []
    for i in range(m - 1):
        for j in range(sides):
            j2 = (j + 1) % sides
            a, b, c, d = i * sides + j, i * sides + j2, (i + 1) * sides + j2, (i + 1) * sides + j
            faces += [[a, b, c], [a, c, d]]
    c0, c1 = m * sides, m * sides + 1
    for j in range(sides):
        j2 = (j + 1) % sides
        faces.append([c0, j2, j])
        faces.append([c1, (m - 1) * sides + j, (m - 1) * sides + j2])
    mesh = trimesh.Trimesh(np.array(verts), np.array(faces), process=False)
    trimesh.repair.fix_normals(mesh)
    return mesh


def control_points(design, h: dict) -> np.ndarray:
    """[start] + waypoints + [end] for a routed harness (raises WireError)."""
    from ..mass import component_cg
    from ..geometry import component_parts
    comps = {c["id"]: c for c in design.components}

    def end(cid, port):
        if port:
            return port_point(design, cid, port)[0]
        c = comps[cid]
        return np.asarray(component_cg(c, component_parts(c, design.base_dir)), dtype=float)

    return np.array([end(h["from"], h.get("from_port")), *[list(w) for w in h.get("waypoints", [])],
                     end(h["to"], h.get("to_port"))], dtype=float)


def is_routed(h: dict) -> bool:
    return any(k in h for k in ("waypoints", "from_port", "to_port"))
