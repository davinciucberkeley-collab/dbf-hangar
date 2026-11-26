"""Visual-only scene nodes (no mass, no checks, no STL). One list in a fixed order; later producers append."""
from __future__ import annotations

from dataclasses import dataclass

import trimesh

WIRE_RGBA = (225, 70, 40, 255)
WIRE_DIAMETER_MM = 1.5


@dataclass
class VisualNode:
    name: str
    kind: str
    mesh: trimesh.Trimesh
    rgba: tuple
    point_mm: list


def _wires(design) -> list[VisualNode]:
    from .geom.wires import WireError, control_points, curve_points, is_routed, tube_mesh
    ids = {c["id"] for c in design.components}
    out = []
    for h in design.data.get("wiring", {}).get("harnesses", []):
        if not is_routed(h) or f"wire-{h['id']}" in ids or h["from"] not in ids or h["to"] not in ids:
            continue
        try:
            ctrl = control_points(design, h)
        except WireError:
            continue
        mesh = tube_mesh(curve_points(ctrl), h.get("diameter_mm", WIRE_DIAMETER_MM))
        out.append(VisualNode(f"wire-{h['id']}", "wire", mesh, WIRE_RGBA, [float(x) for x in ctrl[0]]))
    return out


def visual_nodes(design) -> list[VisualNode]:
    return _wires(design)
