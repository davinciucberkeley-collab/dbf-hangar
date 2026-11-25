"""wing_panel: tapered, swept, twisted wing panel lofted from an airfoil .dat (PDL 1.2 generator).

Adapted from DBF-Combined redesign/fusion/k09kit.py (read_dat, section_loop, elevon) and redesign/qp/A/cad/amodel/
wing.py (build_wing core loft and spar bore). Lengths mm, angles degrees, component-local frame.

Not ported: the `te_min` trailing-edge opening of k09kit.section_loop, the cove, and the explicit pockets and slots of
amodel/wing.py build_wing; only what `cut_files` removes is cut. The cut_files pockets follow each
neighbour's position and rotation_deg (cut_poses, derived by hangar.geom.resolve on load); they do not follow
articulation poses.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import trimesh

from hangar.geom import airfoil, kernel
from hangar.geom.kernel import GeometryError
from hangar.geom.registry import Generator, ParamSpec, register

_NUM = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def read_airfoil(path) -> tuple[np.ndarray, np.ndarray]:
    """Selig or Lednicer .dat -> (upper, lower), each (n, 2) leading edge to trailing edge, x normalised to chord 1."""
    rows: list[tuple[float, float]] = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        nums = _NUM.findall(line)
        if len(nums) >= 2:
            rows.append((float(nums[0]), float(nums[1])))
    if len(rows) < 3:
        raise GeometryError(f"{path}: no airfoil coordinates")
    return split_airfoil(rows, path)


def split_airfoil(rows, path="airfoil") -> tuple[np.ndarray, np.ndarray]:
    if rows[0][0] > 1.5:                                  # Lednicer: counts line, upper LE->TE, lower LE->TE
        nu, nl = int(rows[0][0]), int(rows[0][1])
        up, lo = rows[1:1 + nu], rows[1 + nu:1 + nu + nl]
        rows = list(reversed(up)) + lo[1:]
    xs = [p[0] for p in rows]
    x0, c = min(xs), max(xs) - min(xs)
    if c <= 0:
        raise GeometryError(f"{path}: zero chord")
    pts = np.array([((x - x0) / c, y / c) for x, y in rows])
    le = int(np.argmin(pts[:, 0]))
    return pts[:le + 1][::-1].copy(), pts[le:].copy()


def load_airfoil(ref, base_dir) -> tuple[np.ndarray, np.ndarray]:
    if airfoil.is_named(ref):
        kind, v = airfoil.resolve(ref)
        return split_airfoil(v) if kind == "rows" else read_airfoil(v)
    return read_airfoil(Path(base_dir) / ref)


def _interp(side: np.ndarray, xs: np.ndarray) -> np.ndarray:
    order = np.argsort(side[:, 0], kind="stable")
    return np.interp(xs, side[order, 0], side[order, 1])


def _unit_loop(upper, lower, x0: float, x1: float) -> np.ndarray:
    """Section loop at chord 1 between chord fractions x0 and x1: upper x1 -> x0, then lower x0 -> x1."""
    cosine = x0 + (x1 - x0) * (1 - np.cos(np.pi * np.arange(49) / 48)) / 2
    extra = np.concatenate([upper[:, 0], lower[:, 0]])
    extra = extra[(extra > x0 + 1e-9) & (extra < x1 - 1e-9)]
    xs = np.unique(np.round(np.concatenate([cosine, extra]), 12))
    zu, zl = _interp(upper, xs), _interp(lower, xs)
    up = list(zip(xs[::-1], zu[::-1]))
    lo = list(zip(xs, zl))
    if abs(up[-1][1] - lo[0][1]) < 1e-12:                 # sharp leading edge: drop the repeated point
        lo = lo[1:]
    if abs(lo[-1][1] - up[0][1]) < 1e-12:                 # sharp trailing edge
        lo = lo[:-1]
    return np.array(up + lo)


def _place(unit: np.ndarray, p: dict, y: float) -> list[tuple[float, float]]:
    half = p["span"] / 2.0
    ay = abs(y)
    ib = p.get("inboard_span", 0.0)
    c = p["root_chord"] if ay <= ib else p["root_chord"] + (p["tip_chord"] - p["root_chord"]) * (ay - ib) / (half - ib)
    x, z = unit[:, 0] * c, unit[:, 1] * c
    t = math.radians(p["twist_tip_deg"] * ay / half)
    xq = 0.25 * c
    x2 = xq + (x - xq) * math.cos(t) + z * math.sin(t)
    z2 = z * math.cos(t) - (x - xq) * math.sin(t)
    lead = ay if p.get("sweep_reference", "root") == "root" else max(0.0, ay - ib)
    x2 = x2 + lead * math.tan(math.radians(p["sweep_le_deg"]))
    z2 = z2 + ay * math.tan(math.radians(p["dihedral_deg"])) + p["z_offset"]
    return list(zip(x2.tolist(), z2.tolist()))


def _loft(unit, p, ys) -> trimesh.Trimesh:
    ys = sorted(ys)
    return kernel.loft("y", [(y, _place(unit, p, y)) for y in ys])


def _load_cut(base_dir: Path, name: str) -> trimesh.Trimesh:
    try:
        m = trimesh.load(Path(base_dir) / name, force="mesh")
    except Exception as e:
        raise GeometryError(f"cannot load cut file {name}: {e}") from e
    try:
        return kernel.require_solid(m, name)
    except GeometryError as e:
        raise GeometryError(f"cut file {name}: {e}") from e


def _sides(p) -> list[int]:
    return {"both": [0], "right": [1], "left": [-1]}[p["side"]]


def _placement_z(p) -> float:
    """Extra z of the root datum for placement high (fuselage top), mid (centre) or low (bottom); none adds 0.0."""
    mode = p.get("placement", "none")
    if mode == "high":
        return p["fuselage_center_z"] + p["fuselage_height"] / 2.0
    if mode == "mid":
        return p["fuselage_center_z"]
    if mode == "low":
        return p["fuselage_center_z"] - p["fuselage_height"] / 2.0
    return 0.0


def _build(p: dict, base_dir) -> list:
    p = {**p, "z_offset": p["z_offset"] + _placement_z(p)}
    upper, lower = load_airfoil(p["airfoil_file"], base_dir)
    half = p["span"] / 2.0
    part = p["part"]
    hinge = p["hinge_frac"]
    ib = p.get("inboard_span", 0.0)
    if part == "elevon":
        unit = _unit_loop(upper, lower, hinge, 1.0)
        y0, y1 = p["elevon_y"]
        out = []
        for s in ([1, -1] if p["side"] == "both" else _sides(p)):
            st = [s * y0, s * y1] + ([s * ib] if y0 < ib < y1 else [])
            out.append(_loft(unit, p, st))
        return out
    unit = _unit_loop(upper, lower, 0.0, 1.0 if part == "full" else hinge)
    side = _sides(p)[0]
    if side == 0:
        ys = [-half, -ib, 0.0, ib, half] if ib > 0 else [-half, 0.0, half]
    else:
        ys = [0.0, side * ib, side * half] if ib > 0 else [0.0, side * half]
    core = _loft(unit, p, ys)
    if part == "core" and p["core_fill"] == "outside":
        y0, y1 = p["elevon_y"]
        full_unit = _unit_loop(upper, lower, 0.0, 1.0)
        fills = []
        for s in ([1, -1] if side == 0 else [side]):
            for a, b in [(0.0, y0), (y1, half)]:
                if b - a > 1e-9:
                    st = [s * a, s * b] + ([s * ib] if a < ib < b else [])
                    fills.append(_loft(full_unit, p, st))
        if fills:
            core = kernel.union([core] + fills)
    if "bore_d" in p:
        lo, hi = core.bounds[0][1], core.bounds[1][1]
        cyl = kernel.tube("y", (p["bore_x"], (lo + hi) / 2.0, p["bore_z"]), (hi - lo) + 2.0, p["bore_d"])
        core = kernel.difference(core, [cyl])
    poses = {e["file"]: e["matrix"] for e in p["cut_poses"]}
    cuts = []
    for f in p["cut_files"]:
        m = _load_cut(base_dir, f)
        if f in poses:
            m.apply_transform(np.vstack([np.array(poses[f], dtype=float).reshape(3, 4), [0, 0, 0, 1]]))
        cuts.append(m)
    hit = [m for m in cuts if np.all(m.bounds[0] < core.bounds[1]) and np.all(m.bounds[1] > core.bounds[0])]
    if hit:
        core = kernel.difference(core, hit)
    return [core]


def _check(p: dict) -> list[str]:
    errs = []
    if p.get("inboard_span", 0.0) >= p["span"] / 2.0:
        errs.append("inboard_span: must be < span/2")
    if p.get("sweep_reference", "root") == "outboard_le" and not p.get("inboard_span", 0.0) > 0:
        errs.append("sweep_reference: outboard_le needs inboard_span > 0")
    if not 0 < p["hinge_frac"] < 1:
        errs.append("hinge_frac: must be in (0, 1)")
    given = [k for k in ("bore_x", "bore_z", "bore_d") if k in p]
    if given and len(given) < 3:
        errs.append("bore_x, bore_z and bore_d must be given together; missing "
                    + ", ".join(k for k in ("bore_x", "bore_z", "bore_d") if k not in p))
    if "bore_d" in p and p["bore_d"] <= 0:
        errs.append("bore_d: must be > 0")
    if p["part"] == "elevon":
        y0, y1 = p["elevon_y"]
        if not 0 <= y0 < y1 <= p["span"] / 2.0:
            errs.append("elevon_y: need 0 <= y0 < y1 <= span/2")
    if p["core_fill"] == "outside":
        y0, y1 = p["elevon_y"]
        if p["part"] != "core" or not 0 <= y0 < y1 <= p["span"] / 2.0:
            errs.append("core_fill: outside needs part core and elevon_y with 0 <= y0 < y1 <= span/2")
    if p.get("placement", "none") != "none" and p.get("fuselage_height", 0) <= 0:
        errs.append("fuselage_height: must be > 0 when placement is high, mid or low")
    if not all(isinstance(f, str) for f in p["cut_files"]):
        errs.append("cut_files: must be a list of strings")
    def _bad_pose(e):
        m = e.get("matrix") if isinstance(e, dict) else None
        return (not isinstance(e, dict) or e.get("file") not in p["cut_files"] or not isinstance(m, list)
                or len(m) != 12 or not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in m))
    if any(_bad_pose(e) for e in p["cut_poses"]):
        errs.append("cut_poses: each entry needs a 'file' listed in cut_files and a 'matrix' of 12 numbers")
    return errs


register(Generator(
    "wing_panel",
    {"airfoil_file": ParamSpec("string", required=True, doc="design-folder-relative airfoil .dat, or a name: nacaXXXX (4-digit, generated) or a file in knowledge/airfoils/ without .dat (e.g. s5010)"),
     "span": ParamSpec("number", required=True, exclusive_minimum=0, doc="tip to tip, mm"),
     "root_chord": ParamSpec("number", required=True, exclusive_minimum=0, doc="root chord, mm"),
     "tip_chord": ParamSpec("number", required=True, exclusive_minimum=0, doc="tip chord, mm"),
     "inboard_span": ParamSpec("number", default=0.0, minimum=0, doc="mm per side along |y| over which the chord stays root_chord; the taper to tip_chord runs from there to the tip; 0 = one taper from the root. Sweep starts at the root unless sweep_reference is outboard_le; dihedral and twist always start at the root."),
     "sweep_le_deg": ParamSpec("number", default=0.0, doc="leading-edge sweep angle, deg; measured from the root across the whole half span (the inboard_span rectangle is swept too) unless sweep_reference is outboard_le"),
     "sweep_reference": ParamSpec("choice", default="root", choices=("root", "outboard_le"), doc="where the leading-edge sweep starts: root = from the root chord across the whole half span (default); outboard_le = from the end of the inboard_span rectangle, so the inboard leading edge is straight"),
     "dihedral_deg": ParamSpec("number", default=0.0, doc="dihedral angle, deg"),
     "twist_tip_deg": ParamSpec("number", default=0.0, doc="positive = nose up at the tip, deg"),
     "z_offset": ParamSpec("number", default=0.0, doc="airfoil datum shift, mm"),
     "placement": ParamSpec("choice", default="none", choices=("none", "high", "mid", "low"),
                            doc="root chord datum at the fuselage top (high), centre (mid) or bottom (low)"),
     "fuselage_height": ParamSpec("number", default=0.0, minimum=0, doc="fuselage height, mm (placement)"),
     "fuselage_center_z": ParamSpec("number", default=0.0, doc="fuselage centre z, mm (placement)"),
     "part": ParamSpec("choice", default="full", choices=("full", "core", "elevon"), doc="full chord, core (leading edge to hinge_frac) or elevon (hinge_frac to trailing edge)"),
     "hinge_frac": ParamSpec("number", default=0.75, doc="hinge line as a fraction of the chord"),
     "elevon_y": ParamSpec("vec2", default=[0.0, 0.0], doc="[y0, y1] on |y|, mm"),
     "core_fill": ParamSpec("choice", default="off", choices=("off", "outside"), doc="part core only: outside = full chord outside the elevon_y span, so the elevon pieces over elevon_y complete the wing; off = core to hinge_frac everywhere"),
     "side": ParamSpec("choice", default="both", choices=("both", "right", "left"), doc="half-span to build: both, right or left"),
     "bore_x": ParamSpec("number", doc="bore centre x, mm"), "bore_z": ParamSpec("number", doc="bore centre z, mm"), "bore_d": ParamSpec("number", doc="bore diameter, mm"),
     "cut_files": ParamSpec("list", default=[], doc="design-folder-relative closed-solid meshes subtracted from the core"),
     "cut_poses": ParamSpec("list", default=[], doc="derived by the resolver from the neighbours' positions; do not write")},
    _build, files=lambda p: ([] if airfoil.is_named(p["airfoil_file"]) else [p["airfoil_file"]]) + list(p["cut_files"]), check=_check))


def hinge_line(params: dict, base_dir) -> tuple[list[float], list[float]]:
    """Two points (component-local frame, mm) of the hinge line of a wing_panel elevon, at elevon_y[0] and elevon_y[1] (signed by side)."""
    from hangar.geom.registry import fill_defaults, get
    p = fill_defaults(get("wing_panel"), params)
    if p["part"] != "elevon" or p["side"] == "both":
        raise GeometryError("hinge_from: child must be a wing_panel part elevon with side left or right")
    p = {**p, "z_offset": p["z_offset"] + _placement_z(p)}
    upper, lower = load_airfoil(p["airfoil_file"], base_dir)
    h = p["hinge_frac"]
    zm = float(_interp(upper, np.array([h]))[0] + _interp(lower, np.array([h]))[0]) / 2
    s = -1 if p["side"] == "left" else 1
    y0, y1 = p["elevon_y"]
    pts = []
    for y in (s * y0, s * y1):
        (x, z), = _place(np.array([[h, zm]]), p, y)
        pts.append([x, y, z])
    return pts[0], pts[1]
