"""wing_panel: tapered, swept, twisted wing panel lofted from an airfoil .dat (PDL 1.2 generator).

Adapted from DBF-Combined redesign/fusion/k09kit.py (read_dat, section_loop, elevon) and redesign/qp/A/cad/amodel/
wing.py (build_wing core loft and spar bore). Lengths mm, angles degrees, component-local frame.

Not ported: the `te_min` trailing-edge opening of k09kit.section_loop, the cove, and the explicit pockets and slots of
amodel/wing.py build_wing; only what `cut_files` removes is cut. Known limit: the pockets follow a neighbour only
over the poses the resolver samples (T1 configurations and T6 mechanism steps, see sweeps.py), not over every angle.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import trimesh

from hangar.geom import kernel
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
    c = p["root_chord"] + (p["tip_chord"] - p["root_chord"]) * ay / half
    x, z = unit[:, 0] * c, unit[:, 1] * c
    t = math.radians(p["twist_tip_deg"] * ay / half)
    xq = 0.25 * c
    x2 = xq + (x - xq) * math.cos(t) + z * math.sin(t)
    z2 = z * math.cos(t) - (x - xq) * math.sin(t)
    x2 = x2 + ay * math.tan(math.radians(p["sweep_le_deg"]))
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


def _build(p: dict, base_dir) -> list:
    upper, lower = read_airfoil(Path(base_dir) / p["airfoil_file"])
    half = p["span"] / 2.0
    part = p["part"]
    hinge = p["hinge_frac"]
    if part == "elevon":
        unit = _unit_loop(upper, lower, hinge, 1.0)
        y0, y1 = p["elevon_y"]
        out = []
        for s in ([1, -1] if p["side"] == "both" else _sides(p)):
            out.append(_loft(unit, p, [s * y0, s * y1]))
        return out
    unit = _unit_loop(upper, lower, 0.0, 1.0 if part == "full" else hinge)
    side = _sides(p)[0]
    ys = [-half, 0.0, half] if side == 0 else [0.0, side * half]
    core = _loft(unit, p, ys)
    if "bore_d" in p:
        lo, hi = core.bounds[0][1], core.bounds[1][1]
        cyl = kernel.tube("y", (p["bore_x"], (lo + hi) / 2.0, p["bore_z"]), (hi - lo) + 2.0, p["bore_d"])
        core = kernel.difference(core, [cyl])
    poses = {e["file"]: e["matrices"] for e in p.get("cut_poses", [])}
    cuts = []
    for f in p["cut_files"]:
        m = _load_cut(base_dir, f)
        cuts.append(m)
        for row in poses.get(f, []):
            t = np.eye(4)
            t[:3] = np.array(row, dtype=float).reshape(3, 4)
            moved = m.copy()
            moved.apply_transform(t)
            cuts.append(moved)
    hit = [m for m in cuts if np.all(m.bounds[0] < core.bounds[1]) and np.all(m.bounds[1] > core.bounds[0])]
    if hit:
        core = kernel.difference(core, hit)
    return [core]


def _check(p: dict) -> list[str]:
    errs = []
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
    if not all(isinstance(f, str) for f in p["cut_files"]):
        errs.append("cut_files: must be a list of strings")
    for e in p.get("cut_poses", []):
        ok = isinstance(e, dict) and e.get("file") in p["cut_files"] and isinstance(e.get("matrices"), list) and all(
            isinstance(m, list) and len(m) == 12 and all(isinstance(x, (int, float)) for x in m) for m in e["matrices"])
        if not ok:
            errs.append(f"cut_poses: each entry needs a file from cut_files and matrices of 12 numbers, got {e!r}"[:200])
    return errs


register(Generator(
    "wing_panel",
    {"airfoil_file": ParamSpec("string", required=True, doc="design-folder-relative airfoil .dat"),
     "span": ParamSpec("number", required=True, exclusive_minimum=0, doc="tip to tip, mm"),
     "root_chord": ParamSpec("number", required=True, exclusive_minimum=0),
     "tip_chord": ParamSpec("number", required=True, exclusive_minimum=0),
     "sweep_le_deg": ParamSpec("number", default=0.0),
     "dihedral_deg": ParamSpec("number", default=0.0),
     "twist_tip_deg": ParamSpec("number", default=0.0, doc="positive = nose up at the tip"),
     "z_offset": ParamSpec("number", default=0.0, doc="airfoil datum shift, mm"),
     "part": ParamSpec("choice", default="full", choices=("full", "core", "elevon")),
     "hinge_frac": ParamSpec("number", default=0.75),
     "elevon_y": ParamSpec("vec2", default=[0.0, 0.0], doc="[y0, y1] on |y|"),
     "side": ParamSpec("choice", default="both", choices=("both", "right", "left")),
     "bore_x": ParamSpec("number"), "bore_z": ParamSpec("number"), "bore_d": ParamSpec("number"),
     "cut_files": ParamSpec("list", default=[], doc="design-folder-relative closed-solid meshes subtracted from the core"),
     "cut_sweep": ParamSpec("choice", default="swept", choices=("none", "swept"),
                            doc="swept: pockets also follow the poses of cut meshes that move (resolver fills cut_poses)"),
     "cut_poses": ParamSpec("list", default=[], doc="derived by the resolver from the design's joints when cut_sweep is swept; do not write")},
    _build, files=lambda p: [p["airfoil_file"]] + list(p["cut_files"]), check=_check))
