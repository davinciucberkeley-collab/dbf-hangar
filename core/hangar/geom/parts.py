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
def _sgnpow(v: float, e: float) -> float:
    return math.copysign(abs(v) ** e, v)


def _fuse_loop(shape: str, exponent: float, cy: float, cz: float, w: float, h: float) -> list[tuple[float, float]]:
    if shape == "ellipse":
        return [(cy + w / 2.0 * math.cos(2 * math.pi * k / _N), cz + h / 2.0 * math.sin(2 * math.pi * k / _N))
                for k in range(_N)]
    if shape == "superellipse":
        e = 2.0 / exponent
        return [(cy + w / 2.0 * _sgnpow(math.cos(2 * math.pi * k / _N), e),
                 cz + h / 2.0 * _sgnpow(math.sin(2 * math.pi * k / _N), e)) for k in range(_N)]
    return [(cy - w / 2.0, cz - h / 2.0), (cy + w / 2.0, cz - h / 2.0),
            (cy + w / 2.0, cz + h / 2.0), (cy - w / 2.0, cz + h / 2.0)]


def _cap_scale(shape: str, t: float, tip: float) -> float:
    if shape == "cone":
        return tip + (1 - tip) * t
    f = math.sqrt(1 - (1 - t) ** 2) if shape == "ellipsoid" else math.sin(math.pi * t / 2)
    return max(tip, f)


def _fuse_build(p: dict, base_dir) -> list:
    cy, cz = p["center_y"], p["center_z"]
    shape, ex = p["shape"], p["exponent"]
    st = p["stations"]
    n, tip = p["cap_rings"], p["tip_frac"]
    secs = []
    if p["nose_length"] > 0:
        x0, w0, h0 = st[0]
        for k in range(n):
            s = _cap_scale(p["nose_shape"], k / n, tip)
            secs.append((x0 - p["nose_length"] * (1 - k / n), _fuse_loop(shape, ex, cy, cz, w0 * s, h0 * s)))
    for x, w, h in st:
        secs.append((x, _fuse_loop(shape, ex, cy, cz, w, h)))
    if p["tail_length"] > 0:
        xl, wl, hl = st[-1]
        tn = math.tan(math.radians(p["tail_upsweep_deg"]))
        for k in range(1, n + 1):
            s = _cap_scale(p["tail_shape"], 1 - k / n, tip)
            x = xl + p["tail_length"] * k / n
            secs.append((x, _fuse_loop(shape, ex, cy, cz + (x - xl) * tn, wl * s, hl * s)))
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
    if not 0 < p["tip_frac"] < 0.5:
        errs.append("tip_frac: must be > 0 and < 0.5")
    if p["tail_upsweep_deg"] >= 60:
        errs.append("tail_upsweep_deg: must be < 60")
    if p["exponent"] <= 1:
        errs.append("exponent: must be > 1")
    return errs


register(Generator(
    "fuselage_loft",
    {"stations": ParamSpec("list", required=True, doc="[x, width, height] per station"),
     "shape": ParamSpec("choice", default="ellipse", choices=("ellipse", "rect", "superellipse")),
     "center_y": ParamSpec("number", default=0.0),
     "center_z": ParamSpec("number", default=0.0),
     "nose_length": ParamSpec("number", default=0, minimum=0),
     "tail_length": ParamSpec("number", default=0, minimum=0),
     "nose_shape": ParamSpec("choice", default="cone", choices=("cone", "ellipsoid", "ogive")),
     "tail_shape": ParamSpec("choice", default="cone", choices=("cone", "ellipsoid", "ogive")),
     "tail_upsweep_deg": ParamSpec("number", default=0, minimum=0),
     "tip_frac": ParamSpec("number", default=0.02),
     "cap_rings": ParamSpec("int", default=8, minimum=2),
     "exponent": ParamSpec("number", default=2.5)},
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
