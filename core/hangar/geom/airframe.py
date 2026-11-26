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


def _gear_build(p: dict, base_dir) -> list:
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
                                 "omitted = attach_z")},
    _gear_build, check=_gear_check))
