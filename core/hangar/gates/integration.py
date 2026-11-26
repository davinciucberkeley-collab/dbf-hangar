"""Gate T7: wiring inside envelopes, transport groups fit the box, assembly order."""
from __future__ import annotations

import numpy as np

from ..design import FAIL, PASS, SKIP, CheckResult, TierReport
from . import gate, load_gate_thresholds

SCHEMA = "schema/plane.schema.json"
WIRE_CRIT = "gate-thresholds.yaml#wire_clearance_mm"
BOX_CRIT = "gate-thresholds.yaml#transport_box_mm"
SAMPLES = 21


def _wiring(design, clr: float) -> list[CheckResult]:
    from ..checks import _point_distance
    from ..geometry import component_parts
    from ..mass import component_cg
    from ..geom.wires import is_routed
    comps = {c["id"]: c for c in design.components}
    cache: dict[str, tuple] = {}

    def info(cid):
        if cid not in cache:
            c = comps[cid]
            parts = component_parts(c, design.base_dir)
            cg = np.asarray(component_cg(c, parts), dtype=float)
            g = c.get("geometry") or {}
            if g.get("generator") == "fuselage_loft" and (g.get("params") or {}).get("wall", 0) > 0:
                # D121: a wire is routed through the cavity, so test it against the closed outer volume (wall 0)
                solid = {**c, "geometry": {**g, "params": {**g["params"], "wall": 0}}}
                parts = component_parts(solid, design.base_dir)
            cache[cid] = (parts, cg)
        return cache[cid]

    res = []
    for h in design.data.get("wiring", {}).get("harnesses", []):
        seq = [h["from"], *h.get("route", []), h["to"]]
        cid, data = f"T7.wiring.{h['id']}", {"parts": seq}
        unknown = [x for x in seq if x not in comps]
        if unknown:
            res.append(CheckResult(cid, FAIL, f"harness {h['id']}: unknown component {unknown[0]}", WIRE_CRIT, data))
            continue
        if is_routed(h):
            res.append(_routed(design, h, seq, comps, info, clr, data))
            continue
        worst = None
        unchecked = 0
        for ca, cb in zip(seq, seq[1:]):
            (pa, a), (pb, b) = info(ca), info(cb)
            if not (pa + pb):  # both ends are point masses: no envelope to test against
                unchecked += 1
                continue
            for s in np.linspace(0.0, 1.0, SAMPLES):
                dist = _point_distance(pa + pb, a + (b - a) * s)
                if dist > clr and (worst is None or dist > worst[0]):
                    worst = (dist, ca, cb)
        if unchecked == len(seq) - 1:
            res.append(CheckResult(cid, SKIP, f"harness {h['id']}: not checked, every segment runs between point masses "
                                   "(no envelope to test)", WIRE_CRIT, data))
        elif worst is None:
            note = f"; {unchecked} segment(s) between point masses not checked" if unchecked else ""
            res.append(CheckResult(cid, PASS, f"harness {h['id']}: all {len(seq) - 1 - unchecked} checked segments lie inside the "
                                   f"envelopes (+{clr:g} mm){note}", WIRE_CRIT, data))
        elif h.get("exposed_ok"):
            res.append(CheckResult(cid, PASS, f"harness {h['id']}: exposed segment accepted: {h['exposed_ok']['reason']}",
                                   WIRE_CRIT, data))
        else:
            res.append(CheckResult(cid, FAIL, f"harness {h['id']}: segment {worst[1]} to {worst[2]} leaves the envelopes by "
                                   f"{worst[0]:.0f} mm (> {clr:g} mm); add exposed_ok with a reason or reroute", WIRE_CRIT, data))
    return res


def _routed(design, h, seq, comps, info, clr, data) -> CheckResult:
    """U16.1 S8: a routed harness is tested along its whole curve against the envelopes of every component on it."""
    from ..checks import _point_distance
    from ..geom.wires import WireError, control_points, curve_points
    cid = f"T7.wiring.{h['id']}"
    if f"wire-{h['id']}" in comps:
        return CheckResult(cid, FAIL, f"harness {h['id']}: the node name wire-{h['id']} is also a component id; "
                           "rename the harness", WIRE_CRIT, data)
    try:
        ctrl = control_points(design, h)
    except WireError as e:
        return CheckResult(cid, FAIL, f"harness {h['id']}: {e}", WIRE_CRIT, data)
    parts = [m for x in seq for m in info(x)[0]]
    if not parts:
        return CheckResult(cid, SKIP, f"harness {h['id']}: not checked, every segment runs between point masses "
                           "(no envelope to test)", WIRE_CRIT, data)
    length = float(np.linalg.norm(np.diff(ctrl, axis=0), axis=1).sum())
    data = {**data, "length_mm": round(length, 1)}
    worst = None
    for q in curve_points(ctrl):
        dist = _point_distance(parts, q)
        if dist > clr and (worst is None or dist > worst[0]):
            worst = (dist, q)
    n = len(h.get("waypoints", []))
    if worst is None:
        return CheckResult(cid, PASS, f"harness {h['id']}: routed wire {length:.0f} mm through {n} waypoint(s); every "
                           f"sample lies within {clr:g} mm of the envelopes of {', '.join(seq)}", WIRE_CRIT, data)
    if h.get("exposed_ok"):
        return CheckResult(cid, PASS, f"harness {h['id']}: exposed segment accepted: {h['exposed_ok']['reason']}",
                           WIRE_CRIT, data)
    x, y, z = worst[1]
    return CheckResult(cid, FAIL, f"harness {h['id']}: the routed wire leaves the envelopes by {worst[0]:.0f} mm "
                       f"(> {clr:g} mm) at {x:.0f}, {y:.0f}, {z:.0f}; add exposed_ok with a reason or reroute",
                       WIRE_CRIT, data)


def _transport(design) -> list[CheckResult]:
    from ..checks import _fits, _obb_extents
    from ..geometry import component_parts
    box = design.data.get("requirements", {}).get("transport_box_mm") or load_gate_thresholds()["transport_box_mm"]["value"]
    comps = {c["id"]: c for c in design.components}
    res = []
    for g in design.data.get("transport", {}).get("disassembly", []):
        data = {"parts": g["component_ids"]}
        unknown = [x for x in g["component_ids"] if x not in comps]
        if unknown:
            res.append(CheckResult(f"T7.transport.{g['group']}", FAIL, f"group {g['group']}: unknown component {unknown[0]}",
                                   BOX_CRIT, data))
            continue
        parts = [p for x in g["component_ids"] for p in component_parts(comps[x], design.base_dir)]
        if not parts:
            res.append(CheckResult(f"T7.transport.{g['group']}", SKIP,
                                   f"group {g['group']}: not checked, every component is a point mass (no geometry to fit)",
                                   BOX_CRIT, data))
            continue
        ext = [round(e) for e in _obb_extents(parts)]
        fits = _fits(_obb_extents(parts), box, False)
        res.append(CheckResult(f"T7.transport.{g['group']}", PASS if fits else FAIL,
                               f"group {g['group']}: {ext} mm fits {box} mm" if fits
                               else f"group {g['group']}: {ext} mm does not fit the {box} mm transport box", BOX_CRIT, data))
    return res


def _assembly(design) -> list[CheckResult]:
    comps = [c["id"] for c in design.components]
    seq = sorted(design.data["assembly"]["sequence"], key=lambda s: s["step"])
    added = [x for s in seq for x in s["add"]]
    missing = [c for c in comps if c not in added]
    dup = sorted({x for x in added if added.count(x) > 1})
    unknown = sorted({x for x in added if x not in comps})
    if missing or dup or unknown:
        msg = "assembly sequence must add every component exactly once: " + "; ".join(
            f"{k} {v}" for k, v in (("missing", missing), ("duplicated", dup), ("unknown", unknown)) if v)
        once = CheckResult("T7.assembly.once", FAIL, msg, SCHEMA, {"parts": missing + dup + unknown})
    else:
        once = CheckResult("T7.assembly.once", PASS, f"all {len(comps)} components are added exactly once", SCHEMA,
                           {"parts": comps})
    nbrs: dict[str, set[str]] = {}
    for a in design.data.get("attachments", []):
        nbrs.setdefault(a["parent"], set()).add(a["child"])
        nbrs.setdefault(a["child"], set()).add(a["parent"])
    bad, present = [], set()
    for i, s in enumerate(seq):
        present |= set(s["add"])
        if i == 0:
            continue
        for x in s["add"]:
            if not (nbrs.get(x, set()) & (present - {x})):
                bad.append(f"{x} (step {s['step']})")
    if bad:
        touch = CheckResult("T7.assembly.touch", FAIL,
                            "added with nothing already assembled to attach to: " + ", ".join(bad), SCHEMA,
                            {"parts": [b.split(" ")[0] for b in bad]})
    else:
        touch = CheckResult("T7.assembly.touch", PASS, "every step attaches to what is already assembled", SCHEMA,
                            {"parts": []})
    return [once, touch]


@gate("T7.integration", 7)
def tier7_integration(ctx) -> TierReport | None:
    d = ctx.design.data
    if not any(k in d for k in ("wiring", "transport", "assembly")):
        return None
    res: list[CheckResult] = []
    if "wiring" in d:
        res += _wiring(ctx.design, load_gate_thresholds()["wire_clearance_mm"]["value"])
    if "transport" in d:
        res += _transport(ctx.design)
    if "assembly" in d:
        res += _assembly(ctx.design)
    return TierReport(7, "integration", res)
