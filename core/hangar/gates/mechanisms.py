"""Gate T6: mechanisms. Each mechanism is driven through its input range; every follower must reach ratio x input,
and parts that are not attached to each other must not collide on the way (D15: analytic, no physics engine)."""
from __future__ import annotations

from ..design import FAIL, PASS, WARN, CheckResult, Design, TierReport
from . import gate, load_gate_thresholds

CRIT = "gate-thresholds.yaml#mechanism_ratio_tol"


def _clamp(x: float, rng) -> float:
    return max(min(rng), min(max(rng), x))


def _steps(lo: float, hi: float) -> list[float]:
    n = int(abs(hi - lo) // 1)
    out = [lo + (1 if hi >= lo else -1) * k for k in range(n + 1)]
    if out[-1] != hi:
        out.append(hi)
    return out


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


def _collision(design: Design, mech: dict, sim: dict, limit: float, step_deg: float) -> str | None:
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
    picks = [s for s in sim["steps"] if abs(s["input_deg"] - lo) % step_deg < 1e-9]
    if picks[-1] is not sim["steps"][-1]:
        picks.append(sim["steps"][-1])
    for s in picks:
        angles = {mech["driver"]: _clamp(s["input_deg"], atts[mech["driver"]]["articulation"]["range_deg"]), **s["followers"]}
        posed = posed_component_parts(design, angles)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                pair = frozenset((a, b))
                if (a not in moving and b not in moving) or pair in joined or "propeller" in (types[a], types[b]):
                    continue
                vol = _overlap_volume(posed[a], posed[b])
                if vol <= limit:
                    continue
                if pair not in ignored:
                    ignored[pair] = _overlap_volume(rest[a], rest[b]) > limit
                if not ignored[pair]:
                    return f"mechanism {mech['id']}: {a} and {b} collide at input {s['input_deg']:.0f} deg ({vol:.1f} mm3 > {limit} mm3)"
    return None


def _mechanism_row(design: Design, mech: dict, th: dict, limit: float) -> CheckResult:
    atts = _atts(design)
    mid, drv = mech["id"], mech["driver"]
    expect = {e["attachment"]: e["ratio"] for e in mech.get("expect", [])}
    data = {"joint": [drv, *mech["driven"]]}
    for x in {drv, *mech["driven"], *expect}:
        if x not in atts or (x in (drv, *expect) and not atts[x].get("articulation")):
            return CheckResult(f"T6.mechanism.{mid}", FAIL,
                               f"mechanism {mid}: attachment {x} is missing or not articulated", CRIT, data)
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
    msg = _collision(design, mech, sim, limit, th["mechanism_contact_step_deg"]["value"])
    if msg:
        return CheckResult(f"T6.mechanism.{mid}", FAIL, msg, CRIT, data)
    lo, hi = sim["steps"][0]["input_deg"], sim["steps"][-1]["input_deg"]
    msg = f"mechanism {mid}: {len(expect)} follower(s) track ratio x input over {lo:.0f} to {hi:.0f} deg"
    unchecked = [a for a in mech["driven"] if a not in expect]
    if unchecked:
        msg += "; not checked (no expect ratio): " + ", ".join(unchecked)
    return CheckResult(f"T6.mechanism.{mid}", PASS, msg, CRIT, data)


@gate("T6.mechanisms", 6)
def tier6_mechanisms(ctx) -> TierReport | None:
    from ..geometry import articulated_attachments, att_label
    design = ctx.design
    mechs = design.data.get("mechanisms", [])
    arts = articulated_attachments(design)
    if not mechs and not arts:
        return None
    th = load_gate_thresholds()
    limit = ctx.std["geometry"]["interference_max_mm3"]["value"]
    used = {m["driver"] for m in mechs} | {a for m in mechs for a in m["driven"]} \
        | {e["attachment"] for m in mechs for e in m.get("expect", [])}
    res = [CheckResult(f"T6.undriven.{att_label(a)}", WARN,
                       f"undriven joint: {att_label(a)} is articulated but no mechanism drives or follows it", CRIT,
                       {"joint": [att_label(a)]})
           for a in arts if att_label(a) not in used]
    res += [_mechanism_row(design, m, th, limit) for m in mechs]
    return TierReport(6, "mechanisms", res)
