"""U16.1 S3: put a library servo in a bay (a box cavity on the host) and pose it from its part frames."""
from __future__ import annotations

import copy
import itertools
from datetime import datetime, timezone
from typing import Literal

import numpy as np
import trimesh

from . import op, OpResult, OpInputError
from .edit import _plane, _text, _write_with_log
from .. import pdledit, yamlfast
from ..design import load_design
from ..geometry import component_parts, rotation_matrix

_ANGLES = (0, 90, 180, 270)


def _clean(x) -> float | int:
    v = round(float(x), 4)
    v = 0.0 if v == 0 else v
    return int(v) if v == int(v) else v


def _vec(raw: str | None, n: int, what: str) -> list[float]:
    try:
        v = [float(t) for t in str(raw).split(",")]
    except ValueError:
        v = []
    if len(v) != n:
        raise OpInputError(f"{what} must be {n} comma-separated numbers (got {raw!r})")
    return v


def _rotation(axis, normal, shaft) -> list[int]:
    """Roll/pitch/yaw in {0,90,180,270} (R = Rz Ry Rx) sending the output axis and the mount normal to `shaft`;
    fewest non-zero angles (a single-axis turn wins), then least angle sum, then largest roll, pitch, yaw."""
    best = None
    for rpy in itertools.product(_ANGLES, repeat=3):
        r = rotation_matrix(list(rpy))
        if np.allclose(r @ axis, shaft, atol=1e-9) and np.allclose(r @ normal, shaft, atol=1e-9):
            key = (sum(1 for a in rpy if a), sum(rpy), -rpy[0], -rpy[1], -rpy[2])
            if best is None or key < best[0]:
                best = (key, list(rpy))
    if best is None:
        raise OpInputError(f"no axis-aligned rotation puts the servo output axis along {list(shaft)}")
    return best[1]


def _vertical_hits(meshes: list[trimesh.Trimesh], x: float, y: float) -> list[float]:
    """z of every crossing of the vertical line through (x, y) with the triangles of `meshes`."""
    zs = []
    eps = 1e-9
    for m in meshes:
        tri = m.triangles
        a, b, c = tri[:, 0, :2], tri[:, 1, :2], tri[:, 2, :2]
        d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
        ok = np.abs(d) > 1e-12
        d = np.where(ok, d, 1.0)
        px, py = x - c[:, 0], y - c[:, 1]
        l1 = ((b[:, 1] - c[:, 1]) * px + (c[:, 0] - b[:, 0]) * py) / d
        l2 = ((c[:, 1] - a[:, 1]) * px + (a[:, 0] - c[:, 0]) * py) / d
        l3 = 1 - l1 - l2
        hit = ok & (l1 >= -eps) & (l2 >= -eps) & (l3 >= -eps)
        zs += (l1[hit] * tri[hit, 0, 2] + l2[hit] * tri[hit, 1, 2] + l3[hit] * tri[hit, 2, 2]).tolist()
    return zs


def _bay_clearance() -> float:
    from ..gates.fidelity import resolve_threshold
    return float(resolve_threshold("gate-thresholds.yaml#bay_clearance_mm")["value"])


@op(name="design.place", summary="Put a library servo in a bay: pose it so its mount face sits on the host skin at X,Y (lower or upper face) with the output shaft along --shaft (default: the outward normal of the face), and cut a box bay (servo size plus --clearance, default gate-thresholds bay_clearance_mm) into the host in one atomic, logged edit; idempotent; the part needs `frames` in its part.yaml. Reports the output shaft frame, the removed volume and the part of the servo body inside the host.",
    mutates=True, render=lambda r: "\n".join(r.messages))
def place_op(path: str, component: str, *, host: str, at: str, face: Literal["lower", "upper"],
             shaft: str = None, clearance: float = None, why: str) -> OpResult:
    from ..checks import _overlap_volume
    from ..geom.library import load_part
    from ..geom.params import expression_errors
    from ..geom.resolve import regeneration_report
    plane = _plane(path)
    text = _text(plane)
    if not why.strip():
        raise OpInputError("why must not be empty")
    design = load_design(plane)
    try:
        comp, hostc = design.component(component), design.component(host)
    except KeyError as e:
        raise OpInputError(f"no component {e.args[0]!r}") from e
    g = comp.get("geometry") or {}
    if g.get("generator") != "library_part":
        raise OpInputError(f"{component}: must be a library_part component to be placed in a bay")
    pid = (g.get("params") or {}).get("part")
    part = load_part(pid)
    frames = part.get("frames")
    if not frames:
        raise OpInputError(f"{component}: library part {pid!r} has no frames (output, mount_face) in its part.yaml")
    if any(abs(v) > 1e-12 for v in (hostc.get("rotation_deg") or [0, 0, 0])):
        raise OpInputError(f"{host}: a host with rotation_deg is not supported (the bay is cut in the body frame)")
    x, y = _vec(at, 2, "--at")
    out_n = (0.0, 0.0, -1.0) if face == "lower" else (0.0, 0.0, 1.0)
    sh = np.array(_vec(shaft, 3, "--shaft") if shaft is not None else out_n)
    if int(np.sum(np.abs(sh) > 1e-12)) != 1 or abs(np.linalg.norm(sh) - 1.0) > 1e-9:
        raise OpInputError(f"--shaft must be an axis-aligned unit vector (got {sh.tolist()})")
    clr = _bay_clearance() if clearance is None else float(clearance)
    out_pt, out_ax = np.array(frames["output"]["point"], float), np.array(frames["output"]["axis"], float)
    mnt_pt, mnt_n = np.array(frames["mount_face"]["point"], float), np.array(frames["mount_face"]["normal"], float)
    rpy = _rotation(out_ax, mnt_n, sh)
    rot = rotation_matrix(rpy)

    uncut = copy.deepcopy(hostc)
    uncut.pop("cavities", None)
    host_parts = component_parts(uncut, design.base_dir)
    zs = _vertical_hits(host_parts, x, y)
    if not zs:
        raise OpInputError(f"no host surface at ({x:g}, {y:g}) on {host}")
    skin_z = min(zs) if face == "lower" else max(zs)
    position = np.array([x, y, skin_z]) - rot @ mnt_pt

    local = copy.deepcopy(comp)
    local["position"], local["rotation_deg"] = [0, 0, 0], [0, 0, 0]
    lb = np.vstack([p.bounds for p in component_parts(local, design.base_dir)])
    lo, hi = lb.min(axis=0), lb.max(axis=0)
    corners = np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])
    wc = corners @ rot.T + position
    bmin, bmax = wc.min(axis=0) - clr, wc.max(axis=0) + clr
    if face == "lower":
        bmin[2], bmax[2] = skin_z - 1.0, max(wc[:, 2].max(), skin_z) + clr
    else:
        bmin[2], bmax[2] = min(wc[:, 2].min(), skin_z) - clr, skin_z + 1.0
    hp = np.array(hostc.get("position") or [0, 0, 0], float)
    size, centre = bmax - bmin, (bmin + bmax) / 2 - hp
    desc = f"bay for {component}"
    cavity = {"geometry": {"box": {"size": [_clean(v) for v in size]}},
              "position": [_clean(v) for v in centre], "description": desc}
    pos_l, rot_l = [_clean(v) for v in position], [int(v) for v in rpy]

    # measurements on the geometry as it will be
    box = trimesh.creation.box(extents=size)
    box.apply_translation((bmin + bmax) / 2)
    removed = _overlap_volume([box], host_parts)
    posed = copy.deepcopy(comp)
    posed["position"], posed["rotation_deg"] = pos_l, rot_l
    body_vol = inside = 0.0
    for sp in component_parts(posed, design.base_dir):
        n_w = -(rot @ mnt_n)                       # points to the body side of the mount plane
        half = trimesh.creation.box(extents=[1e5, 1e5, 1e5])      # the half-space as a big box (no shapely/capping needed)
        half.apply_translation(rot @ mnt_pt + position + n_w * 5e4)
        sliced = trimesh.boolean.intersection([sp, half], engine="manifold")
        if sliced is not None and len(sliced.faces):
            body_vol += abs(sliced.volume)
            inside += _overlap_volume([sliced], host_parts)
    fraction = inside / body_vol if body_vol > 0 else 0.0

    # one atomic text edit: servo position and rotation, host cavity list
    before = yamlfast.safe_load(text)
    working, entries = text, []
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def put(key: str, new: list, *, omit_if_absent: bool = False):
        nonlocal working
        data = yamlfast.safe_load(working)
        if pdledit.exists(data, key):
            old = pdledit.get_value(data, key)
            if old == new:
                return
            working, old, _ = pdledit.replace_list(working, key, new)
            kind = "modify"
        else:
            if omit_if_absent:
                return
            old = None
            working = pdledit.add_value(working, key, new)
            kind = "add"
        entries.append({"date": stamp, "key": key, "old": old, "new": new, "why": why, "kind": kind})

    put(f"components[{component}].position", pos_l)
    put(f"components[{component}].rotation_deg", rot_l, omit_if_absent=rot_l == [0, 0, 0])
    raw_host = next(c for c in before["components"] if c.get("id") == host)
    cavs = copy.deepcopy(raw_host.get("cavities") or [])
    at_i = next((i for i, c in enumerate(cavs) if isinstance(c, dict) and c.get("description") == desc), None)
    if at_i is None:
        cavs.append(cavity)
    else:
        cavs[at_i] = cavity
    put(f"components[{host}].cavities", cavs)

    if not entries:
        return OpResult(True, _data(pos_l, rot_l, skin_z, rot, out_pt, out_ax, position, cavity, removed, fraction, False),
                        [f"{component}: already in its bay in {host}; unchanged"])
    fresh = [e for e in expression_errors(yamlfast.safe_load(working)) if e not in set(expression_errors(before))]
    if fresh:
        raise OpInputError("; ".join(f"{o}: {p}: {m}" for o, p, m in fresh))
    pdledit.check_schema(before, yamlfast.safe_load(working), f"components[{host}].cavities")
    regen = regeneration_report(text, working, plane)
    log = _write_with_log(plane, text, working, entries)
    d = _data(pos_l, rot_l, skin_z, rot, out_pt, out_ax, position, cavity, removed, fraction, True)
    op_ = d["output_point"]
    msgs = [f"{component}: position {pos_l}, rotation_deg {rot_l}; bay '{desc}' in {host} (removed {d['removed_mm3']} mm3)",
            f"output shaft at {op_} along {d['output_axis']}; {d['body_inside_fraction']:.3f} of the servo body is inside {host}"]
    if regen is not None and regen["failing"]:
        msgs += [f"still failing (not caused by this edit): {cid}: {m}" for cid, m in sorted(regen["failing"].items())]
    return OpResult(True, d, msgs, changed_files=[str(plane), str(log)])


def _data(pos_l, rot_l, skin_z, rot, out_pt, out_ax, position, cavity, removed, fraction, changed) -> dict:
    r4 = lambda v: [round(float(t), 4) + 0.0 for t in v]
    return {"position": r4(pos_l), "rotation_deg": list(rot_l), "skin_z": round(float(skin_z), 4),
            "output_point": r4(rot @ out_pt + position), "output_axis": r4(rot @ out_ax), "cavity": cavity,
            "removed_mm3": round(float(removed), 4), "body_inside_fraction": round(float(fraction), 4), "changed": changed}
