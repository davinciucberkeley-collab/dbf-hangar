"""Write the input files (drone.json and airframe.stl) for the external GPL program OpenCAE.

This module only writes data files for OpenCAE to read; it copies none of OpenCAE's code.
Numbers that PDL does not hold (motor kv, prop pitch, ...) come from the optional sidecar
`opencae-inputs.yaml` in the design folder, each with a status and a source; anything else is written as null.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import trimesh
import yaml

from .design import Design
from .gates.discipline import OPS, _crit, _entry
from .geom import overlay
from .geometry import component_parts, is_point_mass
from .mass import mass_properties

INPUTS_FILE = "opencae-inputs.yaml"      # sidecar in the design folder
ROLE_BY_TYPE = {"motor": "motor", "propeller": "prop", "battery": "battery", "wing": "wing", "tail_surface": "fin",
                "landing_gear": "landing", "boom": "arm", "structure": "frame", "fuselage": "frame",
                "flight_controller": "electronics", "receiver": "electronics", "esc": "electronics",
                "servo": "electronics"}          # every other type -> "other"
SIDECAR_KEYS = ("propulsion.motor.kv", "propulsion.motor.r_ohm", "propulsion.motor.i0_a", "propulsion.prop.pitch_in",
                "propulsion.prop.ct", "propulsion.prop.cp", "propulsion.battery.r_int_mohm_per_cell",
                "propulsion.esc.i_cont_a", "propulsion.esc.efficiency")
STATUSES = ("estimate", "datasheet", "measured", "user")
_MASS_STATUS = {"measured": "measured", "datasheet": "datasheet", "cad": "estimate", "estimate": "estimate"}


def _num(value, unit, status, source) -> dict:
    return {"value": value, "unit": unit, "status": status, "source": source}


def load_inputs(design: Design) -> dict:
    """Sidecar design.base_dir/INPUTS_FILE (yaml); absent file -> empty values, materials and role_materials.
    Raises ValueError (message names the key) for an unknown key, a bad status, a missing source or an unknown material."""
    out = {"values": {}, "materials": {}, "role_materials": {}}
    path = design.base_dir / INPUTS_FILE
    if not path.is_file():
        return out
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for key, entry in (doc.get("values") or {}).items():
        if key not in SIDECAR_KEYS:
            raise ValueError(f"{INPUTS_FILE}: unknown key {key!r}")
        if not isinstance(entry, dict) or "value" not in entry:
            raise ValueError(f"{INPUTS_FILE}: {key} needs a mapping with value, unit, status, source")
        if entry.get("status") not in STATUSES:
            raise ValueError(f"{INPUTS_FILE}: {key} has bad status {entry.get('status')!r}")
        if not str(entry.get("source") or "").strip():
            raise ValueError(f"{INPUTS_FILE}: {key} has no source")
        out["values"][key] = {k: entry.get(k) for k in ("value", "unit", "status", "source")}
    out["materials"] = dict(doc.get("materials") or {})
    for role, name in (doc.get("role_materials") or {}).items():
        if name not in out["materials"]:
            raise ValueError(f"{INPUTS_FILE}: role_materials {role} names unknown material {name!r}")
        out["role_materials"][role] = name
    return out


def solid_name(component: dict) -> str:
    if component["type"] == "battery":
        return "battery"
    role = ROLE_BY_TYPE.get(component["type"], "other")
    return role + "_" + re.sub(r"[^a-z0-9]", "_", str(component["id"]).lower())


def _std_status(file: str, key: str) -> str:
    """D98: a standards value whose source is pending is an `estimate`; a sourced one is `user`."""
    return "estimate" if _crit(file, key)[1] else "user"


def mass_status(component: dict) -> str:
    src = (component.get("provenance") or {}).get("mass_source")
    return _MASS_STATUS.get(src, "estimate")


def status_for(design: Design, component_id: str) -> str:
    for item in design.data.get("bom") or []:
        if component_id in (item.get("component_ids") or []):
            method = (item.get("verified") or {}).get("method")
            if method in ("datasheet", "browser", "webfetch"):
                return "datasheet"
            if method == "in-hand":
                return "measured"
    return "estimate"


def write_airframe_stl(design: Design, path: Path) -> dict:
    """One ASCII STL in mm, hangar frame, one solid block per component that has a mesh."""
    solids, point_masses, lines = {}, [], []
    with overlay.forced_off():
        for c in design.components:
            if is_point_mass(c):
                point_masses.append(c["id"])
                continue
            mesh = trimesh.util.concatenate(component_parts(c, design.base_dir))
            name = solid_name(c)
            solids[c["id"]] = name
            lines.append(f"solid {name}")
            for tri, normal in zip(mesh.triangles, mesh.face_normals):
                lines.append("facet normal " + " ".join(repr(float(x)) for x in normal))
                lines.append(" outer loop")
                for v in tri:
                    lines.append("  vertex " + " ".join(repr(float(x)) for x in v))
                lines.append(" endloop")
                lines.append("endfacet")
            lines.append(f"endsolid {name}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    return {"solids": solids, "point_masses": point_masses}


def _drone_type(design: Design) -> str:
    m = design.data.get("morphology") or {}
    if m.get("lift") == "multirotor":
        return "multirotor"
    vm = m.get("vtol_method")
    if vm == "tailsitter":
        return "tailsitter"
    if vm and vm != "none":
        return "vtol"
    return "fixed_wing"


def drone_spec(design: Design, inputs: dict, analyses: tuple[str, ...], solvers: dict, solids: dict[str, str]) -> dict:
    """The drone.json object, format "opencae-drone/1"."""
    with overlay.forced_off():
        per = mass_properties(design)["per_component"]
    comps = {c["id"]: c for c in design.components}
    dtype = _drone_type(design)
    roles: dict[str, list[str]] = {}
    for cid, name in solids.items():
        role = ROLE_BY_TYPE.get(comps[cid]["type"], "other")
        if role != "other":
            roles.setdefault(role, []).append(name)
    parts = {solids[p["id"]]: _num(p["mass_g"], "g", mass_status(comps[p["id"]]), "plane design mass")
             for p in per if p["id"] in solids}

    motors = [c for c in design.components if c["type"] == "motor"]
    motor = motors[0] if motors else None
    motor_i = next((c for c in motors if "max_current_a" in (c.get("propulsion") or {})), None)
    prop_d = next((c for c in motors if "prop_diameter_mm" in (c.get("propulsion") or {})), None)
    battery = next((c for c in design.components if c["type"] == "battery"), None)

    def side(key):
        return inputs["values"].get(key)

    i_max = prop = motor_mass = None
    if motor_i:
        i_max = _num(motor_i["propulsion"]["max_current_a"], "A", status_for(design, motor_i["id"]),
                     f"plane.yaml components[{motor_i['id']}].propulsion.max_current_a")
    if prop_d:
        prop = _num(round(prop_d["propulsion"]["prop_diameter_mm"] / 25.4, 4), "in", status_for(design, prop_d["id"]),
                    f"plane.yaml components[{prop_d['id']}].propulsion.prop_diameter_mm")
    if motor:
        motor_mass = _num(motor["mass_g"], "g", mass_status(motor), f"plane.yaml components[{motor['id']}].mass_g")

    bat = {"cells": None, "capacity_mah": None, "c_rating": None}
    if battery and battery.get("battery"):
        st = status_for(design, battery["id"])
        for key, field, unit in (("cells", "cells_s", ""), ("capacity_mah", "capacity_mah", "mAh"),
                                 ("c_rating", "max_discharge_c", "C")):
            if field in battery["battery"]:
                bat[key] = _num(battery["battery"][field], unit, st,
                                f"plane.yaml components[{battery['id']}].battery.{field}")
    bat["usable_fraction"] = _num(_entry(OPS, "battery_usable_fraction")["value"], "", _std_status(OPS, "battery_usable_fraction"),
                                  "standards/operations.yaml#battery_usable_fraction")
    bat["r_int_mohm_per_cell"] = side("propulsion.battery.r_int_mohm_per_cell")

    cruise = (design.data.get("requirements") or {}).get("cruise_speed_mps")
    flight = design.data.get("flight") or {}
    payload = _num(0, "g", "user", "none")
    uf = _entry("design-standards.yaml", "ultimate_factor")["value"]

    spec = {
        "format": "opencae-drone/1", "name": design.id, "engine": "generic", "type": dtype,
        "geometry": {"file": "airframe.stl", "units": "mm", "forward": "-x", "up": "+z"},
        "roles": roles,
        "mass": {"parts": parts, "payload_g": payload},
        "propulsion": {
            "rotors": "auto",
            "motor": {"kv": side("propulsion.motor.kv"), "r_ohm": side("propulsion.motor.r_ohm"),
                      "i0_a": side("propulsion.motor.i0_a"), "i_max_a": i_max, "mass_g": motor_mass},
            "prop": {"diameter_in": prop, "pitch_in": side("propulsion.prop.pitch_in"),
                     "ct": side("propulsion.prop.ct"), "cp": side("propulsion.prop.cp")},
            "battery": bat,
            "esc": {"i_cont_a": side("propulsion.esc.i_cont_a"), "efficiency": side("propulsion.esc.efficiency")},
        },
        "aero": {"cruise_speed_ms": None if cruise is None else _num(cruise, "m/s", "user",
                                                                     "plane.yaml requirements.cruise_speed_mps"),
                 "alpha_deg": _num(0, "deg", "estimate", "default")},
        "mission": {"hover_s": _num(_entry(OPS, "mission_hover_min")["value"] * 60, "s", _std_status(OPS, "mission_hover_min"),
                                    "standards/operations.yaml#mission_hover_min"),
                    "cruise_s": _num(_entry(OPS, "mission_cruise_min")["value"] * 60, "s", _std_status(OPS, "mission_cruise_min"),
                                     "standards/operations.yaml#mission_cruise_min"),
                    "payload_g": payload},
        "environment": {"rho": _num(flight.get("air_density_kgm3", 1.225), "kg/m3", "user" if "air_density_kgm3" in flight else "estimate",
                                    "plane.yaml flight.air_density_kgm3" if "air_density_kgm3" in flight else "default"),
                        "g": _num(9.80665, "m/s2", "estimate", "default")},
    }
    if inputs["materials"]:
        spec["materials"] = inputs["materials"]
    if inputs["role_materials"]:
        spec["role_materials"] = inputs["role_materials"]
    spec["analyses"] = {
        "structure": {"enabled": "structure" in analyses and bool(solvers["ccx"][0]),
                      "load_factor": _num(uf, "", _std_status("design-standards.yaml", "ultimate_factor"),
                                             "standards/design-standards.yaml#ultimate_factor")},
        "cfd": {"enabled": "cfd" in analyses and bool(solvers["cfd"][0]), "solver": "auto", "preset": "coarse",
                "iterations": 300},
        "flight": {"enabled": "flight" in analyses and dtype != "fixed_wing",
                   "disturbance_deg": _num(15, "deg", "estimate", "default")},
    }
    return spec


def export_project(design: Design, out_dir: Path, analyses: tuple[str, ...], solvers: dict) -> dict:
    """Create out_dir, write airframe.stl and drone.json. Never raises for a missing solver."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    geo = write_airframe_stl(design, out_dir / "airframe.stl")
    spec = drone_spec(design, load_inputs(design), analyses, solvers, geo["solids"])
    (out_dir / "drone.json").write_text(json.dumps(spec, indent=1) + "\n", encoding="utf-8", newline="\n")
    skipped = {}
    if "structure" in analyses and not solvers["ccx"][0]:
        skipped["structure"] = solvers["ccx"][1]
    if "cfd" in analyses and not solvers["cfd"][0]:
        skipped["cfd"] = solvers["cfd"][1]
    return {"dir": out_dir, "spec": spec, **geo, "skipped": skipped}
