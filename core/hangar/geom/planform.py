"""Aero outline of generated wings and tails, so tier 3 needs no hand-copied planform."""
import json

import hangar.geom  # noqa: F401  (registers the generators)
from hangar.geom.registry import fill_defaults, get


def generated_planform(component: dict) -> dict | None:
    """Aero outline of a generated wing or tail, or None when the component is not one that tier 3 can read."""
    try:
        g = component.get("geometry") or {}
        name = g.get("generator")
        if not name:
            return None
        p = fill_defaults(get(name), g.get("params") or {})
        ctype = component.get("type")
        if name == "wing_panel" and ctype == "wing":
            if p["part"] in ("full", "core") and p["side"] == "both":
                return {"measured": True}
            return None
        if name == "tail_surfaces" and ctype == "tail_surface":
            if p["part"] == "rudder":  # a rudder is not a lifting stabiliser
                return None
            return {"lifting_surface": {"span": p["stab_span"], "root_chord": p["stab_root_chord"],
                                        "tip_chord": p["stab_tip_chord"], "sweep_le_deg": p["stab_sweep_le_deg"],
                                        "mirrored": True},
                    "offset": [p["stab_x_le"], 0.0, p["stab_z"]]}
        return None
    except Exception:
        return None


_PART_PRIORITY = {"full": 0, "fixed": 1, "elevator": 2}


def counted_tail_ids(components: list[dict]) -> set[str]:
    """Ids of the tail components tier 3 counts: components of one stabiliser (same outline, position and rotation,
    e.g. fixed + elevator parts) are counted once, by part priority full, fixed, elevator, then component order."""
    groups: dict[str, list[tuple[int, int, str]]] = {}
    for i, c in enumerate(components):
        gp = generated_planform(c)
        if not gp or "lifting_surface" not in gp:
            continue
        g = c["geometry"]
        p = fill_defaults(get(g["generator"]), g.get("params") or {})
        sig = json.dumps([sorted((k, v) for k, v in p.items() if k.startswith("stab_") or k in ("layout", "airfoil_file")),
                          c.get("position"), c.get("rotation_deg")], sort_keys=True, default=str)
        groups.setdefault(sig, []).append((_PART_PRIORITY.get(p["part"], 3), i, c["id"]))
    return {min(members)[2] for members in groups.values()}


def analytic_wing_area(component: dict) -> float | None:
    """Planform area the wing_panel params give (both sides) for a core wing, else None."""
    try:
        g = component.get("geometry") or {}
        if g.get("generator") != "wing_panel" or component.get("type") != "wing":
            return None
        p = fill_defaults(get("wing_panel"), g.get("params") or {})
        if p["side"] != "both" or p["part"] != "core":
            return None
        ib = p.get("inboard_span") or 0.0
        root, tip, half = p["root_chord"], p["tip_chord"], p["span"] / 2
        return 2 * (root * ib + (root + tip) / 2 * (half - ib))
    except Exception:
        return None
