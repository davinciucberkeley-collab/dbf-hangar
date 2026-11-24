"""fin, plate, fuselage_loft, motor_mount generators (PDL 1.2). Lengths mm, angles degrees, component-local frame.

Shapes re-expressed on the hangar kernel from DBF-Combined redesign/fusion/k09kit.py (fin_plate, half_fin) and
amodel/wing.py (build_fins); fuselage_loft and motor_mount have no source function.
"""
from __future__ import annotations

import math

from hangar.geom import kernel
from hangar.geom.registry import Generator, ParamSpec, register

_N = 48


def _circle(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    return [(cx + r * math.cos(2 * math.pi * k / _N), cy + r * math.sin(2 * math.pi * k / _N)) for k in range(_N)]


def _is_triple(h) -> bool:
    return isinstance(h, (list, tuple)) and len(h) == 3 and all(
        isinstance(x, (int, float)) and not isinstance(x, bool) for x in h)


# ------------------------------------------------------------------ fin
def _fin_build(p: dict, base_dir) -> list:
    h, t = p["height"], p["thickness"]
    xl, zr = p["x_le"], p["z_root"]
    dx = abs(h) * math.tan(math.radians(p["sweep_le_deg"]))
    outline = [(xl, zr), (xl + p["root_chord"], zr), (xl + dx + p["tip_chord"], zr + h), (xl + dx, zr + h)]
    return [kernel.prism(outline, plane="xz", offset=p["plane_y"] - t / 2.0, depth=t)]


def _fin_check(p: dict) -> list[str]:
    return ["height: must be nonzero"] if p["height"] == 0 else []


register(Generator(
    "fin",
    {"plane_y": ParamSpec("number", default=0.0),
     "thickness": ParamSpec("number", required=True, exclusive_minimum=0),
     "root_chord": ParamSpec("number", required=True, exclusive_minimum=0),
     "tip_chord": ParamSpec("number", required=True, exclusive_minimum=0),
     "height": ParamSpec("number", required=True, doc="signed distance from the root along z"),
     "x_le": ParamSpec("number", default=0.0),
     "z_root": ParamSpec("number", default=0.0),
     "sweep_le_deg": ParamSpec("number", default=0.0)},
    _fin_build, check=_fin_check))


# ------------------------------------------------------------------ plate
_PLANE_NORMAL = {"xy": 2, "xz": 1, "yz": 0}
_PLANE_UV = {"xy": (0, 1), "xz": (0, 2), "yz": (1, 2)}


def _plate_build(p: dict, base_dir) -> list:
    iu, iv = _PLANE_UV[p["plane"]]
    cu, cv, cn = p["center"][iu], p["center"][iv], p["center"][_PLANE_NORMAL[p["plane"]]]
    su, sv = p["size"][0] / 2.0, p["size"][1] / 2.0
    outline = [(cu - su, cv - sv), (cu + su, cv - sv), (cu + su, cv + sv), (cu - su, cv + sv)]
    holes = [_circle(cu + u, cv + v, d / 2.0) for u, v, d in p["holes"]]
    return [kernel.prism(outline, holes, plane=p["plane"], offset=cn - p["thickness"] / 2.0, depth=p["thickness"])]


def _plate_check(p: dict) -> list[str]:
    errs = []
    if any(s <= 0 for s in p["size"]):
        errs.append("size: both values must be > 0")
    if not all(_is_triple(h) for h in p["holes"]):
        return errs + ["holes: each hole must be [u, v, d]"]
    su, sv = p["size"][0] / 2.0, p["size"][1] / 2.0
    for i, (u, v, d) in enumerate(p["holes"]):
        r = d / 2.0
        if d <= 0:
            errs.append(f"holes: hole {i} has d <= 0")
        elif abs(u) + r >= su or abs(v) + r >= sv:
            errs.append(f"holes: hole {i} crosses the outline")
    for i, a in enumerate(p["holes"]):
        for j in range(i + 1, len(p["holes"])):
            b = p["holes"][j]
            if math.hypot(a[0] - b[0], a[1] - b[1]) <= (a[2] + b[2]) / 2.0:
                errs.append(f"holes: holes {i} and {j} overlap")
    return errs


register(Generator(
    "plate",
    {"plane": ParamSpec("choice", default="xy", choices=("xy", "xz", "yz")),
     "size": ParamSpec("vec2", required=True),
     "thickness": ParamSpec("number", required=True, exclusive_minimum=0),
     "center": ParamSpec("vec3", default=[0.0, 0.0, 0.0]),
     "holes": ParamSpec("list", default=[], doc="[u, v, d] from the plate centre")},
    _plate_build, check=_plate_check))


# ------------------------------------------------------------------ fuselage_loft
def _fuse_build(p: dict, base_dir) -> list:
    cy, cz = p["center_y"], p["center_z"]
    secs = []
    for x, w, h in p["stations"]:
        if p["shape"] == "ellipse":
            loop = [(cy + w / 2.0 * math.cos(2 * math.pi * k / _N), cz + h / 2.0 * math.sin(2 * math.pi * k / _N))
                    for k in range(_N)]
        else:
            loop = [(cy - w / 2.0, cz - h / 2.0), (cy + w / 2.0, cz - h / 2.0),
                    (cy + w / 2.0, cz + h / 2.0), (cy - w / 2.0, cz + h / 2.0)]
        secs.append((x, loop))
    return [kernel.loft("x", secs)]


def _fuse_check(p: dict) -> list[str]:
    st = p["stations"]
    if len(st) < 2:
        return ["stations: need at least 2"]
    if not all(_is_triple(s) for s in st):
        return ["stations: each station must be [x, width, height]"]
    errs = []
    if any(b[0] <= a[0] for a, b in zip(st, st[1:])):
        errs.append("stations: x must be strictly increasing")
    if any(s[1] <= 0 or s[2] <= 0 for s in st):
        errs.append("stations: width and height must be > 0")
    return errs


register(Generator(
    "fuselage_loft",
    {"stations": ParamSpec("list", required=True, doc="[x, width, height] per station"),
     "shape": ParamSpec("choice", default="ellipse", choices=("ellipse", "rect")),
     "center_y": ParamSpec("number", default=0.0),
     "center_z": ParamSpec("number", default=0.0)},
    _fuse_build, check=_fuse_check))


# ------------------------------------------------------------------ motor_mount
def _bolts(p: dict) -> list[tuple[float, float]]:
    cy, cz = p["center"][1], p["center"][2]
    dy, dz = p["bolt_pattern"][0] / 2.0, p["bolt_pattern"][1] / 2.0
    return [(cy + sy * dy, cz + sz * dz) for sy in (-1, 1) for sz in (-1, 1)]


def _mount_build(p: dict, base_dir) -> list:
    cx, cy, cz = p["center"]
    t, L = p["plate_t"], p["sleeve_len"]
    w, h = p["plate_size"][0] / 2.0, p["plate_size"][1] / 2.0
    outline = [(cy - w, cz - h), (cy + w, cz - h), (cy + w, cz + h), (cy - w, cz + h)]
    holes = [_circle(u, v, p["bolt_d"] / 2.0) for u, v in _bolts(p)]
    plate = kernel.prism(outline, holes, plane="yz", offset=cx, depth=t)
    sleeve = kernel.tube("x", (cx + (t + L) / 2.0, cy, cz), t + L, p["sleeve_od"])
    body = kernel.union([plate, sleeve])
    bore = kernel.tube("x", (cx + (t + L) / 2.0, cy, cz), t + L + 2.0, p["sleeve_id"])
    return [kernel.difference(body, [bore])]


def _mount_check(p: dict) -> list[str]:
    errs = []
    if p["sleeve_id"] >= p["sleeve_od"]:
        errs.append("sleeve_id: must be less than sleeve_od")
    dy, dz = p["bolt_pattern"][0] / 2.0, p["bolt_pattern"][1] / 2.0
    r = p["bolt_d"] / 2.0
    if math.hypot(dy, dz) - r <= p["sleeve_od"] / 2.0:
        errs.append("bolt_pattern: bolt holes must lie outside the sleeve circle")
    if dy + r >= p["plate_size"][0] / 2.0 or dz + r >= p["plate_size"][1] / 2.0:
        errs.append("bolt_pattern: bolt holes must lie inside the plate")
    return errs


register(Generator(
    "motor_mount",
    {"plate_size": ParamSpec("vec2", required=True, doc="along y and z"),
     "plate_t": ParamSpec("number", required=True, exclusive_minimum=0),
     "bolt_pattern": ParamSpec("vec2", required=True, doc="[dy, dz], 4 holes"),
     "bolt_d": ParamSpec("number", required=True, exclusive_minimum=0),
     "sleeve_od": ParamSpec("number", required=True, exclusive_minimum=0),
     "sleeve_id": ParamSpec("number", required=True, exclusive_minimum=0),
     "sleeve_len": ParamSpec("number", required=True, exclusive_minimum=0),
     "center": ParamSpec("vec3", default=[0.0, 0.0, 0.0], doc="centre of the plate back face")},
    _mount_build, check=_mount_check))
