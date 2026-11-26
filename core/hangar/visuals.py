"""Visual-only scene nodes (no mass, no checks, no STL). One list in a fixed order; later producers append."""
from __future__ import annotations

from dataclasses import dataclass

from ._lazy import trimesh

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


def _clevis_ends(design) -> list[tuple[str, str, str, object, object, object]]:
    """(node name, source component id, mechanism id, end point, direction, pin axis) per drawable pushrod end. No meshes."""
    import numpy as np
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
        out.append((f"clevis-{mid}-driver", d_att["child"], mid, d0, u, a_d))
        out.append((f"clevis-{mid}-follower", f_att["child"], mid, f0, -u, a_f))
    return out


def _clevis_mesh(p0, along, axis):
    from .geom.hinge import cylinder_between
    return trimesh.util.concatenate([
        cylinder_between(p0, p0 + CLEVIS_BARREL_LEN * along, CLEVIS_BARREL_R, 24),
        cylinder_between(p0 - CLEVIS_PIN_LEN / 2 * axis, p0 + CLEVIS_PIN_LEN / 2 * axis, CLEVIS_PIN_R, 24)])


def _clevis_specs(design) -> list[tuple[str, str, str, object, list]]:
    """(node name, source component id, mechanism id, mesh, point_mm) per drawable pushrod end (see clevis docs)."""
    return [(name, src, mid, _clevis_mesh(p, along, ax), [float(x) for x in p])
            for name, src, mid, p, along, ax in _clevis_ends(design)]


def _clevis_nodes(design) -> list[VisualNode]:
    return [VisualNode(name, "clevis", mesh, CLEVIS_RGBA, pt) for name, _src, _mid, mesh, pt in _clevis_specs(design)]


def clevis_aliases(design) -> list[tuple[str, str, str]]:
    """(node name, source component id, mechanism id): the clevis follows the transform of its component."""
    if not _clevises_on(design):
        return []
    return [(name, src, mid) for name, src, mid, *_ in _clevis_ends(design)]


def _clevises_on(design) -> bool:
    return (design.data.get("display") or {}).get("clevises") is True


SCREW_HEAD_R_PER_D = 0.9   # drawing rule: head diameter 1.8 d (not ISO 4762)
SCREW_HEAD_H_PER_D = 1.0   # drawing rule: head height d
SCREW_RGBA = (120, 120, 128, 255)


def _screw_specs(design) -> list[tuple[str, object, list]]:
    """(attachment id, head mesh, point_mm) per drawable screw head: bolted, a connection whose spec names M<d>."""
    import re
    import numpy as np
    from .geom.hinge import cylinder_between
    from .geometry import component_parts
    from .gates.interfaces import load_connection_types
    types = load_connection_types()
    comps = {c["id"]: c for c in design.components}
    out = []
    for a in design.data.get("attachments", []) or []:
        if not isinstance(a, dict) or a.get("method") != "bolted" or not a.get("location"):
            continue
        t = types.get(a.get("connection"))
        m = re.search(r"\bM(\d+(?:\.\d+)?)", (t or {}).get("spec") or "")
        child = comps.get(a.get("child"))
        if m is None or child is None:
            continue
        parts = component_parts(child, design.base_dir)
        if not parts:
            continue
        d = float(m.group(1))
        mesh = trimesh.util.concatenate(parts)
        q, _, tri = trimesh.proximity.closest_point(mesh, [a["location"]])  # a location inside the child snaps to the nearest face
        n = mesh.face_normals[tri[0]]
        q0 = np.asarray(q[0], dtype=float)
        head = cylinder_between(q0, q0 + SCREW_HEAD_H_PER_D * d * n, SCREW_HEAD_R_PER_D * d, 24)
        out.append((a.get("id") or f"{a.get('parent')}->{a.get('child')}", head, [float(x) for x in q0]))
    return out


def _screw_node(design) -> list[VisualNode]:
    """One visual 'screws' node (all heads concatenated); empty when no head qualifies."""
    specs = _screw_specs(design)
    if not specs:
        return []
    mesh = trimesh.util.concatenate([h for _id, h, _pt in specs])
    return [VisualNode("screws", "screw", mesh, SCREW_RGBA, specs[0][2])]


def _screws_on(design) -> bool:
    return (design.data.get("display") or {}).get("screw_heads") is True


def visual_nodes(design) -> list[VisualNode]:
    out = _wires(design)
    if _clevises_on(design):
        out += _clevis_nodes(design)
    if _screws_on(design):
        out += _screw_node(design)
    return out
