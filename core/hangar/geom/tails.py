"""tail_surfaces generator (PDL 1.2): conventional, T, V and H tails from fin + wing_panel.

Parts are built through the public registry and united into one part. Lengths mm, angles degrees,
component-local frame. Separate elevator / rudder surfaces are not modelled.
"""
from __future__ import annotations

from hangar.geom import kernel, registry
from hangar.geom.registry import Generator, ParamSpec, register

_FIN_KEYS = ("fin_thickness", "fin_height", "fin_root_chord", "fin_tip_chord")


def _make(name: str, params: dict, base_dir) -> list:
    return registry.build_component({"id": "tail", "geometry": {"generator": name, "params": params}}, base_dir)


def _build(p: dict, base_dir) -> list:
    layout = p["layout"]
    stab = {"airfoil_file": p["airfoil_file"], "span": p["stab_span"], "root_chord": p["stab_root_chord"],
            "tip_chord": p["stab_tip_chord"], "sweep_le_deg": p["stab_sweep_le_deg"], "part": "full"}
    if layout == "t":
        stab["z_offset"] = p["fin_z_root"] + p["fin_height"]
    else:
        stab["z_offset"] = p["stab_z"]
    if layout == "v":
        stab.update(dihedral_deg=p["v_dihedral_deg"], side="both")
    meshes = _make("wing_panel", stab, base_dir)
    for m in meshes:
        m.apply_translation([p["stab_x_le"], 0.0, 0.0])
    if layout != "v":
        fin = {"thickness": p["fin_thickness"], "root_chord": p["fin_root_chord"], "tip_chord": p["fin_tip_chord"],
               "height": p["fin_height"], "x_le": p["fin_x_le"], "z_root": p["fin_z_root"],
               "sweep_le_deg": p["fin_sweep_le_deg"]}
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
    if not 5 <= p["v_dihedral_deg"] <= 80:
        errs.append(f"v_dihedral_deg: must be within 5..80, got {p['v_dihedral_deg']!r}")
    return errs


register(Generator(
    "tail_surfaces",
    {"layout": ParamSpec("choice", default="conventional", choices=("conventional", "t", "v", "h")),
     "airfoil_file": ParamSpec("string", required=True, doc="design-folder-relative airfoil .dat"),
     "stab_span": ParamSpec("number", required=True, exclusive_minimum=0, doc="tip to tip (horizontal projection for v)"),
     "stab_root_chord": ParamSpec("number", required=True, exclusive_minimum=0),
     "stab_tip_chord": ParamSpec("number", required=True, exclusive_minimum=0),
     "stab_sweep_le_deg": ParamSpec("number", default=0.0),
     "stab_x_le": ParamSpec("number", default=0.0, doc="x of the stab root leading edge"),
     "stab_z": ParamSpec("number", default=0.0, doc="z of the stab chord datum (conventional, h, v)"),
     "v_dihedral_deg": ParamSpec("number", default=35.0, doc="5..80, layout v only"),
     "fin_thickness": ParamSpec("number", exclusive_minimum=0, doc="needed unless layout v"),
     "fin_height": ParamSpec("number", doc="needed unless layout v"),
     "fin_root_chord": ParamSpec("number", exclusive_minimum=0, doc="needed unless layout v"),
     "fin_tip_chord": ParamSpec("number", exclusive_minimum=0, doc="needed unless layout v"),
     "fin_sweep_le_deg": ParamSpec("number", default=0.0),
     "fin_x_le": ParamSpec("number", default=0.0),
     "fin_z_root": ParamSpec("number", default=0.0)},
    _build, files=lambda p: [p["airfoil_file"]], check=_check))
