"""tail_surfaces generator (PDL 1.2): conventional, T, V and H tails from fin + wing_panel.

Parts are built through the public registry and united into one part. Lengths mm, angles degrees,
component-local frame. part selects the whole surface, the fixed part, the elevator or the rudder;
elevator_fin_gap keeps the elevator clear of the fin.
"""
from __future__ import annotations

from hangar.geom import airfoil, kernel, registry
from hangar.geom.registry import Generator, ParamSpec, register

_FIN_KEYS = ("fin_thickness", "fin_height", "fin_root_chord", "fin_tip_chord")
HINGE_KEYS = ("hinge_gap", "hinge_style", "hinge_throw_deg", "hinge_knuckles", "knuckle_d", "knuckle_len")
_HINGE_DEFAULTS = {"hinge_gap": 0.0, "hinge_style": "none", "hinge_throw_deg": 0.0, "hinge_knuckles": 0,
                   "knuckle_d": 0.0, "knuckle_len": 0.0}


def _make(name: str, params: dict, base_dir) -> list:
    return registry.build_component({"id": "tail", "geometry": {"generator": name, "params": params}}, base_dir)


def _build(p: dict, base_dir) -> list:
    layout = p["layout"]
    stab = {"airfoil_file": p["airfoil_file"], "span": p["stab_span"], "root_chord": p["stab_root_chord"],
            "tip_chord": p["stab_tip_chord"], "sweep_le_deg": p["stab_sweep_le_deg"], "part": "full"}
    part, hf = p["part"], p["hinge_frac"]
    if part in ("fixed", "elevator"):
        stab["hinge_frac"] = hf
        if part == "fixed":
            stab["part"] = "core"
        else:
            half, t, g = p["stab_span"] / 2.0, p["fin_thickness"] if layout != "v" else 0.0, p["elevator_fin_gap"]
            y0, y1 = 0.0, half
            if g > 0 and layout in ("conventional", "t"):
                y0 = t / 2.0 + g
            elif g > 0 and layout == "h":
                y1 = half - t / 2.0 - g
            stab.update(part="elevon", elevon_y=[y0, y1], side="both", **{k: p[k] for k in HINGE_KEYS})
    if layout == "t":
        stab["z_offset"] = p["fin_z_root"] + p["fin_height"]
    else:
        stab["z_offset"] = p["stab_z"]
    if layout == "v":
        stab.update(dihedral_deg=p["v_dihedral_deg"], side="both")
    meshes = []
    if part != "rudder":
        meshes = _make("wing_panel", stab, base_dir)
        for m in meshes:
            m.apply_translation([p["stab_x_le"], 0.0, 0.0])
    if layout != "v" and part != "elevator":
        fin = {"thickness": p["fin_thickness"], "root_chord": p["fin_root_chord"], "tip_chord": p["fin_tip_chord"],
               "height": p["fin_height"], "x_le": p["fin_x_le"], "z_root": p["fin_z_root"],
               "sweep_le_deg": p["fin_sweep_le_deg"]}
        if part != "full":
            fin.update(part="rear" if part == "rudder" else "front", hinge_frac=hf)
            if part == "rudder":
                fin.update({k: p[k] for k in HINGE_KEYS})
        if layout == "h":
            for sgn in (1, -1):
                meshes += _make("fin", {**fin, "plane_y": sgn * p["stab_span"] / 2.0,
                                        "z_root": p["stab_z"] - p["fin_height"] / 2.0}, base_dir)
        else:
            meshes += _make("fin", {**fin, "plane_y": 0.0}, base_dir)
    return [kernel.union(meshes)]


def _check(p: dict) -> list[str]:
    errs = []
    if p["layout"] != "v":
        missing = [k for k in _FIN_KEYS if k not in p]
        if missing:
            errs.append(f"{', '.join(missing)}: required for layout {p['layout']!r}")
    if p["part"] == "rudder" and p["layout"] == "v":
        errs.append("part: rudder needs a layout other than v")
    g = p["elevator_fin_gap"]
    if g > 0 and p["layout"] == "v":
        errs.append("elevator_fin_gap: has no effect on layout v")
    elif g > 0 and "fin_thickness" in p and "stab_span" in p:
        room = p["stab_span"] / 2.0 - p["fin_thickness"] / 2.0 - g
        if room <= 0:
            errs.append("elevator_fin_gap: the gap leaves no elevator (need fin_thickness/2 + gap < stab_span/2)")
    if not 0 < p["hinge_frac"] < 1:
        errs.append("hinge_frac: must be in (0, 1)")
    if not 5 <= p["v_dihedral_deg"] <= 80:
        errs.append(f"v_dihedral_deg: must be within 5..80, got {p['v_dihedral_deg']!r}")
    if p["part"] in ("full", "fixed") and any(p[k] != v for k, v in _HINGE_DEFAULTS.items()):
        errs.append("hinge_gap: only part elevator or rudder use the hinge_* and knuckle_* params")
    return errs


register(Generator(
    "tail_surfaces",
    {"layout": ParamSpec("choice", default="conventional", choices=("conventional", "t", "v", "h"), doc="tail layout: conventional, t, v or h"),
     "part": ParamSpec("choice", default="full", choices=("full", "fixed", "elevator", "rudder"), doc="whole surface, fixed part, elevator or rudder"),
     "hinge_frac": ParamSpec("number", default=0.7, doc="hinge line as a fraction of the local chord, ratio"),
     "airfoil_file": ParamSpec("string", required=True, doc="design-folder-relative airfoil .dat, or a name: nacaXXXX (4-digit, generated) or a file in knowledge/airfoils/ without .dat (e.g. s5010)"),
     "stab_span": ParamSpec("number", required=True, exclusive_minimum=0, doc="tip to tip (horizontal projection for v), mm"),
     "stab_root_chord": ParamSpec("number", required=True, exclusive_minimum=0, doc="stabiliser root chord, mm"),
     "stab_tip_chord": ParamSpec("number", required=True, exclusive_minimum=0, doc="stabiliser tip chord, mm"),
     "stab_sweep_le_deg": ParamSpec("number", default=0.0, doc="stabiliser leading-edge sweep, deg"),
     "stab_x_le": ParamSpec("number", default=0.0, doc="x of the stab root leading edge, mm"),
     "stab_z": ParamSpec("number", default=0.0, doc="z of the stab chord datum (conventional, h, v), mm"),
     "elevator_fin_gap": ParamSpec("number", default=0.0, minimum=0, doc="lateral gap between the elevator and the fin(s), mm; 0 = the elevator spans to the fin plane (default); only part elevator, layouts conventional, t and h"),
     "v_dihedral_deg": ParamSpec("number", default=35.0, doc="5..80, layout v only, deg"),
     "fin_thickness": ParamSpec("number", exclusive_minimum=0, doc="needed unless layout v, mm"),
     "fin_height": ParamSpec("number", doc="needed unless layout v, mm"),
     "fin_root_chord": ParamSpec("number", exclusive_minimum=0, doc="needed unless layout v, mm"),
     "fin_tip_chord": ParamSpec("number", exclusive_minimum=0, doc="needed unless layout v, mm"),
     "fin_sweep_le_deg": ParamSpec("number", default=0.0, doc="fin leading-edge sweep, deg"),
     "fin_x_le": ParamSpec("number", default=0.0, doc="fin root leading-edge x, mm"),
     "fin_z_root": ParamSpec("number", default=0.0, doc="fin root z position, mm"),
     "hinge_gap": ParamSpec("number", default=0.0, minimum=0, doc="elevator and rudder only: gap between the fixed part and the moving part, mm, measured normal to the hinge line; the front face moves aft by it (0 = flush, default)"),
     "hinge_style": ParamSpec("choice", default="none", choices=("none", "bevel"), doc="elevator and rudder only: none = flat front face; bevel = V ridge on the hinge axis with chamfers back to the skins, clearing the fixed part up to hinge_throw_deg"),
     "hinge_throw_deg": ParamSpec("number", default=0.0, minimum=0, doc="elevator and rudder only: the largest deflection the bevel clears, deg; set it at least as large as the articulation range_deg"),
     "hinge_knuckles": ParamSpec("int", default=0, minimum=0, doc="elevator and rudder only: count of round knuckle cylinders along the hinge line, united with the moving part (printed geometry)"),
     "knuckle_d": ParamSpec("number", default=0.0, minimum=0, doc="elevator and rudder only: knuckle diameter, mm; at most 2 * hinge_gap * cos(hinge_throw_deg)"),
     "knuckle_len": ParamSpec("number", default=0.0, minimum=0, doc="elevator and rudder only: knuckle length along the hinge line, mm")},
    _build, files=lambda p: [] if airfoil.is_named(p["airfoil_file"]) else [p["airfoil_file"]], check=_check))
