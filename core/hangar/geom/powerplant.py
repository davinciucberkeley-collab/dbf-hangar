"""nacelle and propeller generators (PDL 1.2). Lengths mm, angles degrees, component-local frame.

Both are bodies of revolution about the x axis, nose toward -x. The propeller is scale-look: straight tapered
blades with constant pitch, no airfoil section.
"""
from __future__ import annotations

import math

import numpy as np
import trimesh

from hangar.geom import kernel
from hangar.geom.registry import Generator, ParamSpec, register

_SHAPES = ("cone", "ellipsoid", "ogive")


def _s(shape: str, t: float, tip_frac: float) -> float:
    if shape == "cone":
        return tip_frac + (1 - tip_frac) * t
    if shape == "ellipsoid":
        return max(tip_frac, math.sqrt(max(0.0, 1 - (1 - t) ** 2)))
    return max(tip_frac, math.sin(math.pi * t / 2))


# ------------------------------------------------------------------ nacelle
def _nacelle_build(p: dict, base_dir) -> list:
    L, R = p["length"], p["diameter"] / 2.0
    nl, tl, n, tip = p["nose_length"], p["tail_length"], p["cap_rings"], p["tip_frac"]
    x0, x1 = -L / 2.0, L / 2.0
    prof = [(x0, 0.0)]
    if nl > 0:
        prof += [(x0 + nl * k / n, R * _s(p["nose_shape"], k / n, tip)) for k in range(n + 1)]
    else:
        prof.append((x0, R))
    xt = x1 - tl
    if tl > 0:
        if xt > x0 + nl:
            prof.append((xt, R))
        prof += [(xt + tl * k / n, R * (1 - (1 - p["tail_end_frac"]) * k / n)) for k in range(1, n + 1)]
        prof.append((x1, 0.0))
    else:
        prof += [(x1, R), (x1, 0.0)]
    m = kernel.revolve("x", (0.0, 0.0, 0.0), prof)
    if p["inlet_d"] > 0:
        d = p["inlet_depth"]
        bore = kernel.tube("x", (x0 + d / 2.0 - 0.5, 0.0, 0.0), d + 1.0, p["inlet_d"])
        m = kernel.difference(m, [bore])
    m.apply_translation(p["center"])
    return [m]


def _nacelle_check(p: dict) -> list[str]:
    errs = []
    if p["nose_length"] + p["tail_length"] > p["length"]:
        errs.append("nose_length: nose_length + tail_length must be <= length")
    if not 0 < p["tail_end_frac"] <= 1:
        errs.append("tail_end_frac: must be > 0 and <= 1")
    if not 0 < p["tip_frac"] < 0.5:
        errs.append("tip_frac: must be > 0 and < 0.5")
    if p["inlet_d"] >= p["diameter"]:
        errs.append("inlet_d: must be < diameter")
    if p["inlet_depth"] > p["length"] - p["tail_length"]:
        errs.append("inlet_depth: must be <= length - tail_length")
    if (p["inlet_d"] > 0) != (p["inlet_depth"] > 0):
        errs.append("inlet: inlet_d and inlet_depth must both be > 0 or both 0")
    return errs


register(Generator(
    "nacelle",
    {"length": ParamSpec("number", required=True, exclusive_minimum=0, doc="overall length along x, mm"),
     "diameter": ParamSpec("number", required=True, exclusive_minimum=0, doc="maximum outer diameter, mm"),
     "nose_length": ParamSpec("number", default=0.0, minimum=0, doc="nose cap length within the overall length, mm"),
     "tail_length": ParamSpec("number", default=0.0, minimum=0, doc="tail cap length within the overall length, mm"),
     "nose_shape": ParamSpec("choice", default="ellipsoid", choices=_SHAPES, doc="nose cap profile"),
     "tail_end_frac": ParamSpec("number", default=0.3, doc="end radius as a fraction of diameter/2"),
     "tip_frac": ParamSpec("number", default=0.02, doc="cap tip radius as a fraction of the radius"),
     "cap_rings": ParamSpec("int", default=8, minimum=2, doc="rings per cap, count"),
     "inlet_d": ParamSpec("number", default=0.0, minimum=0, doc="inlet bore diameter, mm; 0 = no inlet"),
     "inlet_depth": ParamSpec("number", default=0.0, minimum=0, doc="inlet bore depth from the nose, mm; 0 = no inlet"),
     "center": ParamSpec("vec3", default=[0.0, 0.0, 0.0], doc="centre of the full length, mm")},
    _nacelle_build, check=_nacelle_check))


# ------------------------------------------------------------------ propeller
def _loop(c: float, tf: float, pitch_rad: float) -> list[tuple[float, float]]:
    cs, sn = math.cos(pitch_rad), math.sin(pitch_rad)
    pts = [(-tf * c / 2, -c / 2), (tf * c / 2, -c / 2), (tf * c / 2, c / 2), (-tf * c / 2, c / 2)]
    return [(x * cs + z * sn, z * cs - x * sn) for x, z in pts]


def _prop_build(p: dict, base_dir) -> list:
    R, hd, hl = p["diameter"] / 2.0, p["hub_d"], p["hub_length"]
    r0 = hd / 2.0 - 1.0
    t = math.radians(p["pitch_deg"]) * (-1.0 if p["handed"] == "ccw" else 1.0)
    tf = p["thickness_frac"]
    blade = kernel.loft("y", [(r0, _loop(p["root_chord"], tf, t)), (R, _loop(p["tip_chord"], tf, t))])
    parts = [kernel.tube("x", (0.0, 0.0, 0.0), hl, hd)]
    if p["spinner_length"] > 0:
        xa, sl = -hl / 2.0, p["spinner_length"]
        parts.append(kernel.revolve("x", (0.0, 0.0, 0.0), [
            (xa + 1.0, 0.0), (xa + 1.0, hd / 2.0), (xa - sl, 0.02 * hd / 2.0), (xa - sl, 0.0)]))
    for k in range(p["blades"]):
        b = blade.copy()
        b.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(360.0 * k / p["blades"]), [1, 0, 0]))
        parts.append(b)
    m = kernel.union(parts)
    m.apply_translation(p["center"])
    return [m]


def _prop_check(p: dict) -> list[str]:
    errs = []
    if p["hub_d"] >= p["diameter"]:
        errs.append("hub_d: must be < diameter")
    # chord runs along z (tangential), so it must fit the hub diameter, not the axial hub length (brief value
    # root_chord 14 > hub_length 12 contradicts its own tests; root_chord 20 still fails against hub_d 16)
    if p["root_chord"] > p["hub_d"]:
        errs.append("root_chord: must be <= hub_d")
    if not 0 < p["thickness_frac"] < 0.5:
        errs.append("thickness_frac: must be > 0 and < 0.5")
    if abs(p["pitch_deg"]) >= 60:
        errs.append("pitch_deg: abs must be < 60")
    return errs


register(Generator(
    "propeller",
    {"blades": ParamSpec("int", required=True, minimum=2, doc="number of blades, count"),
     "diameter": ParamSpec("number", required=True, exclusive_minimum=0, doc="propeller diameter, mm"),
     "hub_d": ParamSpec("number", required=True, exclusive_minimum=0, doc="hub diameter, mm"),
     "hub_length": ParamSpec("number", required=True, exclusive_minimum=0, doc="hub length along x, mm"),
     "root_chord": ParamSpec("number", required=True, exclusive_minimum=0, doc="blade chord at the root, mm"),
     "tip_chord": ParamSpec("number", required=True, exclusive_minimum=0, doc="blade chord at the tip, mm"),
     "thickness_frac": ParamSpec("number", default=0.08, doc="blade thickness as a fraction of the chord"),
     "pitch_deg": ParamSpec("number", default=0.0, doc="blade pitch angle, deg"),
     "spinner_length": ParamSpec("number", default=0.0, minimum=0, doc="spinner cone length, mm"),
     "handed": ParamSpec("choice", default="cw", choices=("cw", "ccw"), doc="rotation sense, cw or ccw"),
     "center": ParamSpec("vec3", default=[0.0, 0.0, 0.0], doc="hub centre, mm")},
    _prop_build, check=_prop_check))
