"""Gate T6: mechanisms. Each mechanism is driven through its input range; a follower must not stall at its own range limit (jam), and parts that no attachment or declared link joins must not collide on the way (D15: analytic, no physics engine). The follower angle is the declared ratio x input; T6.ratio checks the ratio against the geometry of mechanisms[].link."""
from __future__ import annotations

import math

import numpy as np

from ..design import FAIL, PASS, SKIP, WARN, CheckResult, Design, TierReport
from . import gate, load_gate_thresholds

CRIT = "gate-thresholds.yaml#mechanism_ratio_tol"
SERVO_CRIT = "gate-thresholds.yaml#servo_must_drive_mechanism"


def _clamp(x: float, rng) -> float:
    return max(min(rng), min(max(rng), x))


def _steps(lo: float, hi: float) -> list[float]:
    a, b = min(lo, hi), max(lo, hi)
    vals = {round(float(lo), 9), round(float(hi), 9)} | {float(k) for k in range(math.floor(a) + 1, math.ceil(b))}
    return sorted(vals, reverse=hi < lo)


def _atts(design: Design) -> dict[str, dict]:
    from ..geometry import att_label
    return {att_label(a): a for a in design.data.get("attachments", [])}


def _input_range(design: Design, mech: dict) -> tuple[float, float]:
    rng = mech.get("input_range_deg") or _atts(design)[mech["driver"]]["articulation"]["range_deg"]
    return float(rng[0]), float(rng[1])


def simulate_mechanism(design: Design, mech: dict) -> dict:
    """Follower angle (deg) at each 1 degree of driver input: clamp(ratio x driver, follower range_deg).
    A follower sitting at its own limit is the jam."""
    atts = _atts(design)
    try:
        drv = atts[mech["driver"]]["articulation"]
        ratios = {e["attachment"]: (float(e["ratio"]), atts[e["attachment"]]["articulation"]["range_deg"])
                  for e in mech.get("expect", [])}
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"mechanism {mech['id']}: could not build model: {e!r}") from e
    lo, hi = _input_range(design, mech)
    steps = []
    for inp in _steps(lo, hi):
        d = _clamp(inp, drv["range_deg"])
        steps.append({"input_deg": float(inp),
                      "followers": {a: _clamp(r * d, rng) for a, (r, rng) in ratios.items()}})
    return {"mechanism": mech["id"], "driver": mech["driver"], "steps": steps}


def _pick_steps(sim: dict, step_deg: float) -> list[dict]:
    """The simulated steps T6 poses the design at: both ends and every step_deg multiple of the input."""
    last = len(sim["steps"]) - 1
    return [s for k, s in enumerate(sim["steps"]) if k in (0, last)
            or abs(s["input_deg"] / step_deg - round(s["input_deg"] / step_deg)) < 1e-9]


def mechanism_pose_angles(design: Design, step_deg: float) -> list[dict[str, float]]:
    """Joint angles (label -> deg) of every pose T6 collision-checks, over all mechanisms. A mechanism that cannot be simulated is skipped (T6 reports it)."""
    atts = _atts(design)
    out = []
    for mech in design.data.get("mechanisms", []):
        try:
            sim = simulate_mechanism(design, mech)
        except (RuntimeError, KeyError):
            continue
        rng = atts[mech["driver"]]["articulation"]["range_deg"]
        out.extend({mech["driver"]: _clamp(s["input_deg"], rng), **s["followers"]} for s in _pick_steps(sim, step_deg))
    return out


def _collision(design: Design, mech: dict, sim: dict, limit: float, step_deg: float, linked: set) -> str | None:
    from ..checks import _overlap_volume
    from ..geometry import downstream_ids, posed_component_parts
    atts = _atts(design)
    moving = set()
    for lbl in (mech["driver"], *sim["steps"][0]["followers"]):
        moving |= downstream_ids(design, atts[lbl])
    joined = {frozenset((a["parent"], a["child"])) for a in atts.values()}
    types = {c["id"]: c["type"] for c in design.components}
    ids = [c["id"] for c in design.components]
    lo = sim["steps"][0]["input_deg"]
    rest = posed_component_parts(design, {})
    ignored: dict[frozenset, bool] = {}
    for s in _pick_steps(sim, step_deg):
        angles = {mech["driver"]: _clamp(s["input_deg"], atts[mech["driver"]]["articulation"]["range_deg"]), **s["followers"]}
        posed = posed_component_parts(design, angles)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                pair = frozenset((a, b))
                if (a not in moving and b not in moving) or pair in joined or pair in linked or "propeller" in (types[a], types[b]):
                    continue
                vol = _overlap_volume(posed[a], posed[b])
                if vol <= limit:
                    continue
                if pair not in ignored:
                    ignored[pair] = _overlap_volume(rest[a], rest[b]) > limit
                if not ignored[pair]:
                    return f"mechanism {mech['id']}: {a} and {b} collide at input {s['input_deg']:.0f} deg ({vol:.1f} mm3 > {limit} mm3)"
    return None


def _link(design: Design, mech: dict, atts: dict) -> tuple[list[list[str]], str | None]:
    """(pairs, error). Pairs: child of link.driver_end x {child of link.follower_end, and its parent unless that parent
    is a driven joint's child}, each pair a sorted 2-list. No link: ([], None)."""
    from ..geometry import downstream_ids
    link = mech.get("link")
    if not link:
        return [], None
    de, fe = atts.get(link["driver_end"]), atts.get(link["follower_end"])
    if de is None:
        return [], f"mechanism {mech['id']}: link.driver_end {link['driver_end']} is not an attachment"
    if fe is None:
        return [], f"mechanism {mech['id']}: link.follower_end {link['follower_end']} is not an attachment"
    drv_side = downstream_ids(design, atts[mech["driver"]])
    children = {atts[j]["child"] for j in mech["driven"]}
    foll_side = set().union(*(downstream_ids(design, atts[j]) for j in mech["driven"]))
    if not (de.get("kinematic_link") and de["parent"] in drv_side and de["child"] in drv_side):
        return [], (f"mechanism {mech['id']}: link.driver_end {link['driver_end']} must be kinematic_link: true "
                    f"with parent and child on the driver side of {mech['driver']}")
    if fe["parent"] not in foll_side or fe["child"] not in foll_side:
        return [], (f"mechanism {mech['id']}: link.follower_end {link['follower_end']} must have parent and child "
                    f"on the side moved by {', '.join(mech['driven'])}")
    ends = {fe["child"]} | ({fe["parent"]} - children)
    return sorted(sorted([de["child"], x]) for x in ends), None


def _ratio_row(design: Design, mech: dict, atts: dict, th: dict) -> CheckResult | None:
    """Small-angle lever ratio from the two link points against each declared expect ratio."""
    from ..geometry import downstream_ids
    mid, cid = mech["id"], f"T6.ratio.{mech['id']}"
    expect = mech.get("expect", [])
    if not expect:
        return None
    link = mech.get("link")
    if not link:
        r = ", ".join(f"{e['ratio']:g}" for e in expect)
        return CheckResult(cid, SKIP, f"mechanism {mid}: ratio {r} is declared, not measured: mechanisms[].link missing", CRIT)
    pd, pf = (np.array(atts[link[k]]["location"], dtype=float) for k in ("driver_end", "follower_end"))
    drv = atts[mech["driver"]]["articulation"]
    lo, hi = _input_range(design, mech)
    tol, floor = th["mechanism_ratio_tol"]["value"], th["mechanism_abs_tol_deg"]["value"]
    span = max(abs(lo), abs(hi)) or 1.0
    side = atts[link["follower_end"]]["child"]
    notes, data = [], {"driver_end": link["driver_end"], "follower_end": link["follower_end"], "ratios": {}}
    d = pf - pd
    if np.linalg.norm(d) < 1e-9:
        return CheckResult(cid, FAIL, f"mechanism {mid}: dead point: link.driver_end and link.follower_end coincide", CRIT, data)
    u = d / np.linalg.norm(d)

    def lever(art, p):
        w = np.array(art["axis"], dtype=float)
        return float(u @ np.cross(w / np.linalg.norm(w), p - np.array(art["pivot"], dtype=float)))

    num = lever(drv, pd)
    for e in expect:
        att = atts[e["attachment"]]
        if side not in downstream_ids(design, att):
            notes.append(f"{e['attachment']} not measured (link.follower_end is not on its side)")
            continue
        den = lever(att["articulation"], pf)
        if abs(den) < 1e-9:
            return CheckResult(cid, FAIL, f"mechanism {mid}: dead point: the follower end of the link lies on the "
                               f"axis of {e['attachment']} (lever 0)", CRIT, data)
        geo, decl = num / den, float(e["ratio"])
        data["ratios"][e["attachment"]] = {"declared": decl, "geometric": round(geo, 4)}
        allowed = max(tol * abs(geo), floor / span)
        if abs(decl - geo) > allowed:
            return CheckResult(cid, FAIL, f"mechanism {mid}: {e['attachment']} declared ratio {decl:g} but the link geometry "
                               f"gives {geo:.3f} (allowed +-{allowed:.3f})", CRIT, data)
        notes.append(f"{e['attachment']} declared {decl:g}, geometry {geo:.3f}")
    if not data["ratios"]:
        return CheckResult(cid, SKIP, f"mechanism {mid}: no expect attachment lies on the side of link.follower_end", CRIT, data)
    return CheckResult(cid, PASS, f"mechanism {mid}: ratio matches the link geometry (small angle): " + "; ".join(notes), CRIT, data)


def _mechanism_row(design: Design, mech: dict, th: dict, limit: float) -> CheckResult:
    atts = _atts(design)
    mid, drv = mech["id"], mech["driver"]
    expect = {e["attachment"]: e["ratio"] for e in mech.get("expect", [])}
    data = {"joint": [drv, *mech["driven"]]}
    for x in {drv, *mech["driven"], *expect}:
        if x not in atts or (x in (drv, *expect) and not atts[x].get("articulation")):
            return CheckResult(f"T6.mechanism.{mid}", FAIL,
                               f"mechanism {mid}: attachment {x} is missing or not articulated", CRIT, data)
    data["link_pairs"], err = _link(design, mech, atts)
    if err:
        return CheckResult(f"T6.mechanism.{mid}", FAIL, err, CRIT, data)
    try:
        sim = simulate_mechanism(design, mech)
    except RuntimeError as e:
        return CheckResult(f"T6.mechanism.{mid}", FAIL, str(e), CRIT, data)
    tol, floor = th["mechanism_ratio_tol"]["value"], th["mechanism_abs_tol_deg"]["value"]
    for s in sim["steps"]:
        for att, ang in s["followers"].items():
            exp = expect[att] * s["input_deg"]
            allowed = max(tol * abs(exp), floor)
            if abs(ang - exp) > allowed:
                return CheckResult(f"T6.mechanism.{mid}", FAIL,
                                   f"mechanism {mid}: follower {att} at {ang:.1f} deg when input is {s['input_deg']:.0f} deg "
                                   f"(expected {exp:.1f} deg, tolerance {allowed:.1f} deg); first stalls at input "
                                   f"{s['input_deg']:.0f} deg", CRIT, data)
    msg = _collision(design, mech, sim, limit, th["mechanism_contact_step_deg"]["value"],
                     {frozenset(p) for p in data["link_pairs"]})
    if msg:
        return CheckResult(f"T6.mechanism.{mid}", FAIL, msg, CRIT, data)
    lo, hi = sim["steps"][0]["input_deg"], sim["steps"][-1]["input_deg"]
    step = th["mechanism_contact_step_deg"]["value"]
    msg = (f"mechanism {mid}: no jam over {lo:.0f} to {hi:.0f} deg; follower angle(s) are the declared ratio x input; "
           f"no collision at every {step:g} deg")
    unchecked = [a for a in mech["driven"] if a not in expect]
    if unchecked:
        msg += "; not checked (no expect ratio): " + ", ".join(unchecked)
    return CheckResult(f"T6.mechanism.{mid}", PASS, msg, CRIT, data)


def _undriven_servos(design) -> list[str]:
    from .applicability import NEEDS
    if not NEEDS["conventional"](design.data["morphology"]):
        return []
    atts = {a["id"]: a for a in design.data.get("attachments", [])}
    driven = {atts[m["driver"]]["parent"] for m in design.data.get("mechanisms", []) if m["driver"] in atts}
    return [c["id"] for c in design.data["components"] if c.get("type") == "servo" and c["id"] not in driven]


@gate("T6.mechanisms", 6)
def tier6_mechanisms(ctx) -> TierReport | None:
    from ..geometry import articulated_attachments, att_label
    design = ctx.design
    mechs = design.data.get("mechanisms", [])
    arts = articulated_attachments(design)
    idle = _undriven_servos(design)
    if not mechs and not arts and not idle:
        return None
    th = load_gate_thresholds()
    limit = ctx.std["geometry"]["interference_max_mm3"]["value"]
    used = {m["driver"] for m in mechs} | {a for m in mechs for a in m["driven"]} \
        | {e["attachment"] for m in mechs for e in m.get("expect", [])}
    res = [CheckResult(f"T6.undriven.{att_label(a)}", WARN,
                       f"undriven joint: {att_label(a)} is articulated but no mechanism drives or follows it", CRIT,
                       {"joint": [att_label(a)]})
           for a in arts if att_label(a) not in used]
    atts = _atts(design)
    for m in mechs:
        row = _mechanism_row(design, m, th, limit)
        res.append(row)
        if row.data.get("link_pairs"):
            res.append(CheckResult(f"T6.link.{m['id']}", WARN, f"mechanism {m['id']}: not checked (pinned by declared link): "
                                   + ", ".join(f"{a} & {b}" for a, b in row.data["link_pairs"]), CRIT, {"link_pairs": row.data["link_pairs"], "parts": sorted({i for p in row.data["link_pairs"] for i in p})}))
        if row.data.get("link_pairs") or not m.get("link"):
            ratio = _ratio_row(design, m, atts, th)
            if ratio:
                res.append(ratio)
    res += [CheckResult(f"T6.servo_undriven.{c}", WARN,
                        f"servo {c} is not the driver of any mechanism (no mechanisms[] entry has a driver attachment whose parent is {c}); see docs/mechanisms.md",
                        SERVO_CRIT, {"servo": c}) for c in idle]
    return TierReport(6, "mechanisms", res)
