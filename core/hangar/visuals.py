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


CLEVIS_BARREL_R = 1.5      # drawing dimensions, 1.5 mm rods at 1:10 (not a standard)
CLEVIS_BARREL_LEN = 8.0
CLEVIS_PIN_R = 0.6
CLEVIS_PIN_LEN = 5.0
CLEVIS_RGBA = (170, 172, 180, 255)


def _clevis_specs(design) -> list[tuple[str, str, str, object, list]]:
    """(node name, source component id, mechanism id, mesh, point_mm) per drawable pushrod end (see clevis docs)."""
    import numpy as np
    from .geom.hinge import cylinder_between
    from .geometry import att_label
    atts = {att_label(a): a for a in design.data.get("attachments", []) or [] if isinstance(a, dict)}

    def unit(v):
        n = float(np.linalg.norm(v))
        return None if n < 1e-9 else np.asarray(v, dtype=float) / n

    out = []
    for mech in design.data.get("mechanisms", []) or []:
        link = mech.get("link")
        driven = mech.get("driven") or []
        if not isinstance(link, dict) or not driven:
            continue
        drv, fol = atts.get(mech.get("driver")), atts.get(driven[0])
        d_att, f_att = atts.get(link.get("driver_end")), atts.get(link.get("follower_end"))
        if not all(isinstance(x, dict) for x in (drv, fol, d_att, f_att)):
            continue
        if not (drv.get("articulation") and fol.get("articulation")):
            continue
        if not (d_att.get("location") and f_att.get("location")):
            continue
        d0 = np.asarray(d_att["location"], dtype=float)
        f0 = np.asarray(f_att["location"], dtype=float)
        u = unit(f0 - d0)
        a_d = unit(drv["articulation"].get("axis") or [])
        a_f = unit(fol["articulation"].get("axis") or [])
        if u is None or a_d is None or a_f is None:
            continue
        mid = mech["id"]
        drv_mesh = trimesh.util.concatenate([
            cylinder_between(d0, d0 + CLEVIS_BARREL_LEN * u, CLEVIS_BARREL_R, 24),
            cylinder_between(d0 - CLEVIS_PIN_LEN / 2 * a_d, d0 + CLEVIS_PIN_LEN / 2 * a_d, CLEVIS_PIN_R, 24)])
        fol_mesh = trimesh.util.concatenate([
            cylinder_between(f0, f0 - CLEVIS_BARREL_LEN * u, CLEVIS_BARREL_R, 24),
            cylinder_between(f0 - CLEVIS_PIN_LEN / 2 * a_f, f0 + CLEVIS_PIN_LEN / 2 * a_f, CLEVIS_PIN_R, 24)])
        out.append((f"clevis-{mid}-driver", d_att["child"], mid, drv_mesh, [float(x) for x in d0]))
        out.append((f"clevis-{mid}-follower", f_att["child"], mid, fol_mesh, [float(x) for x in f0]))
    return out


def _clevis_nodes(design) -> list[VisualNode]:
    return [VisualNode(name, "clevis", mesh, CLEVIS_RGBA, pt) for name, _src, _mid, mesh, pt in _clevis_specs(design)]


def clevis_aliases(design) -> list[tuple[str, str, str]]:
    """(node name, source component id, mechanism id): the clevis follows the transform of its component."""
    if not _clevises_on(design):
        return []
    return [(name, src, mid) for name, src, mid, _mesh, _pt in _clevis_specs(design)]


def _clevises_on(design) -> bool:
    return (design.data.get("display") or {}).get("clevises") is True


def visual_nodes(design) -> list[VisualNode]:
    out = _wires(design)
    if _clevises_on(design):
        out += _clevis_nodes(design)
    return out
