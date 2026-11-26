"""strut and landing_gear generators (PDL 1.2). Lengths mm, angles degrees, component-local frame.

Legs and struts are 48-sided prisms (round, or elliptical when a chord is given). Oleo detail, wheel pants and
retraction are not modelled.
"""
from __future__ import annotations

import math

import numpy as np
from .._lazy import trimesh

from hangar.geom import kernel
from hangar.geom.registry import Generator, ParamSpec, register


def _segment(a, b, thickness: float, chord: float) -> trimesh.Trimesh:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    length = float(np.linalg.norm(b - a))
    d = (b - a) / length
    c = np.array([1.0, 0.0, 0.0]) - d[0] * d
    if np.linalg.norm(c) < 1e-6:
        c = np.array([0.0, 1.0, 0.0])
    c = c / np.linalg.norm(c)
    ch = chord or thickness
    m = np.eye(4)
    m[:3, :3] = np.column_stack([c, np.cross(d, c), d]) @ np.diag([ch / 2.0, thickness / 2.0, length])
    m[:3, 3] = (a + b) / 2.0
    mesh = trimesh.creation.cylinder(radius=1.0, height=1.0, sections=48)
    mesh.apply_transform(m)
    return kernel.require_solid(mesh, "strut")


# ------------------------------------------------------------------ strut
def _strut_build(p: dict, base_dir) -> list:
    return [_segment(p["start"], p["end"], p["diameter"], p["chord"])]


def _strut_check(p: dict) -> list[str]:
    errs = []
    if np.allclose(p["start"], p["end"]):
        errs.append("start: start and end must differ")
    if p["chord"] != 0 and p["chord"] < p["diameter"]:
        errs.append("chord: must be 0 (round) or >= diameter")
    return errs


register(Generator(
    "strut",
    {"start": ParamSpec("vec3", required=True, doc="start point x, y, z, mm"),
     "end": ParamSpec("vec3", required=True, doc="end point x, y, z, mm"),
     "diameter": ParamSpec("number", required=True, exclusive_minimum=0, doc="thickness, mm"),
     "chord": ParamSpec("number", default=0.0, minimum=0, doc="0 = round, else elliptical section chord, mm")},
    _strut_build, check=_strut_check))


# ------------------------------------------------------------------ landing_gear
def _tyre_profile(d: float, w: float) -> list:
    R, h = d / 2.0, w / 2.0
    rec, rh = 0.2 * w, 0.5 * R
    rc = min(0.35 * w, 0.5 * (R - rh))
    pts = [(-h + rec, 0.0), (-h + rec, rh), (-h, rh), (-h, R - rc)]
    for k in range(1, 7):
        t = math.radians(180 - 15 * k)
        pts.append((-h + rc + rc * math.cos(t), R - rc + rc * math.sin(t)))
    pts.append((h - rc, R))
    for k in range(1, 7):
        t = math.radians(90 - 15 * k)
        pts.append((h - rc + rc * math.cos(t), R - rc + rc * math.sin(t)))
    pts += [(h, rh), (h - rec, rh), (h - rec, 0.0)]
    return pts


def _gear_wheel(p: dict, axle, w: float, d: float):
    if p["wheel_shape"] == "tyre":
        return kernel.revolve("y", axle, _tyre_profile(d, w))
    return kernel.tube("y", axle, w, d)


def _gear_build_separate(p: dict, base_dir) -> list:
    """Legs, axle stubs and the nose or tail fork only; the wheels are `wheel` components (U16.1 S2)."""
    wd, ww, ld = p["wheel_d"], p["wheel_w"], p["leg_d"]
    gz, az = p["ground_z"], p["attach_z"]
    axle_d = p["axle_d"] or 0.5 * ld
    axle_z = gz + wd / 2.0
    off = (az - axle_z) * math.tan(math.radians(p["leg_splay_deg"]))
    yb = p["track"] / 2.0 - ww / 2.0 - ld / 2.0 - 0.5
    parts = []
    for s in (-1, 1):
        parts.append(_segment((p["main_x"], s * (yb - off), az), (p["main_x"], s * yb, axle_z), ld, 0.0))
        y_in, y_out = s * yb, s * (p["track"] / 2.0 + ww / 2.0 + 1.0)
        parts.append(kernel.tube("y", (p["main_x"], (y_in + y_out) / 2.0, axle_z), abs(y_out - y_in), axle_d))
    fw = p["front_wheel_d"] or wd
    fld = p["front_leg_d"] or ld
    fx = p["front_x"]
    axle_z_f = gz + fw / 2.0
    crown_z = axle_z_f + fw / 2.0 + 1.0
    yp = ww / 2.0 + fld / 2.0 + 0.5
    parts.append(_segment((fx, 0.0, p.get("front_attach_z", az)), (fx, 0.0, crown_z), fld, 0.0))
    parts.append(kernel.tube("y", (fx, 0.0, crown_z), 2 * yp, fld))
    for s in (-1, 1):
        parts.append(_segment((fx, s * yp, crown_z), (fx, s * yp, axle_z_f), fld, 0.0))
    parts.append(kernel.tube("y", (fx, 0.0, axle_z_f), 2 * yp, axle_d))
    return [kernel.union(parts)]


def _gear_build(p: dict, base_dir) -> list:
    if p.get("wheels", "merged") == "separate":
        return _gear_build_separate(p, base_dir)
    wd, ww, ld = p["wheel_d"], p["wheel_w"], p["leg_d"]
    gz, az = p["ground_z"], p["attach_z"]
    parts = []
    axle_z = gz + wd / 2.0
    off = (az - axle_z) * math.tan(math.radians(p["leg_splay_deg"]))
    n, pitch = p["main_wheels"], p["wheel_pitch"]
    for s in (-1, 1):
        axle = (p["main_x"], s * p["track"] / 2.0, axle_z)
        top = (p["main_x"], s * (p["track"] / 2.0 - off), az)
        parts.append(_segment(top, axle, ld, 0.0))
        if n == 1:
            parts.append(_gear_wheel(p, axle, ww, wd))
        else:
            for i in range(n):
                ax = (p["main_x"] + (i - (n - 1) / 2.0) * pitch, axle[1], axle_z)
                parts.append(_gear_wheel(p, ax, ww, wd))
            parts.append(kernel.tube("x", axle, (n - 1) * pitch, ld))
    fw = p["front_wheel_d"] or wd
    axle = (p["front_x"], 0.0, gz + fw / 2.0)
    parts.append(_segment((p["front_x"], 0.0, p.get("front_attach_z", az)), axle, p["front_leg_d"] or ld, 0.0))
    parts.append(_gear_wheel(p, axle, ww, fw))
    return [kernel.union(parts)]


def _gear_check(p: dict) -> list[str]:
    errs = []
    lay = p["layout"]
    if lay == "tricycle" and not p["front_x"] < p["main_x"]:
        errs.append("front_x: must be < main_x for the tricycle layout")
    if lay == "taildragger" and not p["front_x"] > p["main_x"]:
        errs.append("front_x: must be > main_x for the taildragger layout")
    fw = p["front_wheel_d"] or p["wheel_d"]
    if not p["attach_z"] - p["ground_z"] > max(p["wheel_d"], fw):
        errs.append("wheel_d: attach_z - ground_z must exceed the wheel diameters")
    if p["leg_d"] > p["wheel_w"]:
        errs.append("leg_d: must be <= wheel_w")
    if (p["front_leg_d"] or p["leg_d"]) > fw:
        errs.append("front_leg_d: must be <= the front wheel diameter")
    if not p["leg_splay_deg"] < 45:
        errs.append("leg_splay_deg: must be < 45")
    if p["main_wheels"] > 1 and not p["wheel_pitch"] > p["wheel_d"]:
        errs.append("wheel_pitch: must be > wheel_d when main_wheels > 1")
    if "front_attach_z" in p and not p["front_attach_z"] - p["ground_z"] > fw:
        errs.append("front_attach_z: must exceed ground_z by more than the front wheel diameter")
    if p.get("wheels", "merged") == "separate" and p["main_wheels"] > 1:
        errs.append("wheels: separate needs main_wheels 1")
    if p.get("axle_d"):
        if not p["axle_d"] < p["wheel_w"]:
            errs.append("axle_d: must be < wheel_w")
        if not p["axle_d"] <= p["leg_d"]:
            errs.append("axle_d: must be <= leg_d")
    return errs


register(Generator(
    "landing_gear",
    {"layout": ParamSpec("choice", default="tricycle", choices=("tricycle", "taildragger"), doc="gear layout"),
     "main_x": ParamSpec("number", required=True, doc="main wheel axle x, mm"),
     "track": ParamSpec("number", required=True, exclusive_minimum=0, doc="distance between main wheel centres, mm"),
     "attach_z": ParamSpec("number", required=True, doc="z where the leg tops meet the airframe, mm"),
     "ground_z": ParamSpec("number", required=True, doc="ground contact z, mm"),
     "wheel_d": ParamSpec("number", required=True, exclusive_minimum=0, doc="wheel diameter, mm"),
     "wheel_w": ParamSpec("number", required=True, exclusive_minimum=0, doc="wheel width, mm"),
     "leg_d": ParamSpec("number", required=True, exclusive_minimum=0, doc="leg diameter, mm"),
     "leg_splay_deg": ParamSpec("number", default=0.0, minimum=0, doc="outward leg splay from vertical, deg"),
     "front_x": ParamSpec("number", required=True, doc="nose wheel x (tricycle) or tail wheel x (taildragger), mm"),
     "front_wheel_d": ParamSpec("number", default=0.0, minimum=0, doc="0 = wheel_d, mm"),
     "front_leg_d": ParamSpec("number", default=0.0, minimum=0, doc="0 = leg_d, mm"),
     "main_wheels": ParamSpec("int", default=1, minimum=1, doc="main wheels in line per side, count"),
     "wheel_pitch": ParamSpec("number", default=0.0, minimum=0,
                              doc="x distance between neighbouring main wheel centres, mm"),
     "wheel_shape": ParamSpec("choice", default="disc", choices=("disc", "tyre"),
                              doc="disc = plain cylinder wheel; tyre = rounded tyre with recessed hub"),
     "front_attach_z": ParamSpec("number", doc="z where the nose or tail leg top meets the airframe, mm; "
                                 "omitted = attach_z"),
     "wheels": ParamSpec("choice", default="merged", choices=("merged", "separate"),
                         doc="merged = legs, axles and wheels in one mesh (default); separate = legs, axle stubs and "
                             "the fork only: add one wheel generator component per wheel"),
     "axle_d": ParamSpec("number", default=0.0, minimum=0,
                         doc="axle stub diameter, mm; 0 = half the leg diameter; only used with wheels separate")},
    _gear_build, check=_gear_check))


# ------------------------------------------------------------------ wheel
def _wheel_build(p: dict, base_dir) -> list:
    mesh = _gear_wheel({"wheel_shape": p["shape"]}, (0, 0, 0), p["wheel_w"], p["wheel_d"])
    if p["bore_d"] > 0:
        mesh = kernel.difference(mesh, [kernel.tube("y", (0, 0, 0), 2 * p["wheel_w"], p["bore_d"])])
    return [mesh]


def _wheel_check(p: dict) -> list[str]:
    errs = []
    if not p["bore_d"] < 0.5 * p["wheel_d"]:
        errs.append("bore_d: must be < half the wheel diameter")
    if not p["bore_d"] < p["wheel_w"] * 4:
        errs.append("bore_d: must be < 4 x wheel_w")
    return errs


register(Generator(
    "wheel",
    {"wheel_d": ParamSpec("number", required=True, exclusive_minimum=0, doc="wheel diameter, mm"),
     "wheel_w": ParamSpec("number", required=True, exclusive_minimum=0, doc="wheel width, mm"),
     "shape": ParamSpec("choice", default="tyre", choices=("disc", "tyre"),
                        doc="disc = plain cylinder wheel; tyre = rounded tyre with recessed hub"),
     "bore_d": ParamSpec("number", default=0.0, minimum=0,
                         doc="axle bore diameter, mm; 0 = solid; keep it within 4 mm (2 x attach_tolerance_mm) of "
                             "the axle so the joint point at the axle centre stays on the wheel")},
    _wheel_build, check=_wheel_check))
