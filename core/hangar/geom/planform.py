"""Aero outline of generated wings and tails, so tier 3 needs no hand-copied planform."""
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
            return {"lifting_surface": {"span": p["stab_span"], "root_chord": p["stab_root_chord"],
                                        "tip_chord": p["stab_tip_chord"], "sweep_le_deg": p["stab_sweep_le_deg"],
                                        "mirrored": True},
                    "offset": [p["stab_x_le"], 0.0, p["stab_z"]]}
        return None
    except Exception:
        return None
