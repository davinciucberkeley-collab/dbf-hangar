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


def _continuous_refusal(design: Design, mech: dict) -> str | None:
    """FAIL text when the driver, a driven joint or an expect target is a continuous joint (a wheel spins freely), else None."""
    atts = _atts(design)
    for x in (mech["driver"], *mech["driven"], *(e["attachment"] for e in mech.get("expect", []))):
        if (atts.get(x, {}).get("articulation") or {}).get("type") == "continuous":
            return f"mechanism {mech['id']}: continuous joint {x} cannot be a driver or follower"
    return None


def _input_range(design: Design, mech: dict) -> tuple[float, float]:
    rng = mech.get("input_range_deg") or _atts(design)[mech["driver"]]["articulation"]["range_deg"]
    return float(rng[0]), float(rng[1])


def _rot_point(art: dict, angle_deg: float, p) -> np.ndarray:
    from ..geometry import joint_rotation
    return (joint_rotation(art, angle_deg) @ np.append(np.asarray(p, dtype=float), 1.0))[:3]


def solve_four_bar(tip0, pin0, driver_art: dict, follower_art: dict, input_deg: float,
                   follower_range: tuple[float, float], prev_deg: float = 0.0, scan_deg: float = 0.05) -> float | None:
    """Follower angle (deg) that keeps |pin - tip| = L = |pin0 - tip0| when the driver turns the tip by input_deg and the
    follower turns the pin: every sign change of the distance error over the follower range is bisected to a root; the root
    nearest prev_deg is returned, None when there is none (D96: scan then bisect, simplest robust choice)."""
    tip0, pin0 = np.asarray(tip0, dtype=float), np.asarray(pin0, dtype=float)
    length = float(np.linalg.norm(pin0 - tip0))
    if abs(input_deg) < 1e-12:
        return 0.0
    tip = _rot_point(driver_art, input_deg, tip0)

    def g(t: float) -> float:
        return float(np.linalg.norm(_rot_point(follower_art, t, pin0) - tip)) - length

    lo, hi = float(min(follower_range)), float(max(follower_range))
    n = max(1, math.ceil((hi - lo) / scan_deg - 1e-9))
    ts = [lo + k * scan_deg for k in range(n)] + [hi]
    gs = [g(t) for t in ts]
    roots = []
    for k, (t, gt) in enumerate(zip(ts, gs)):
        if abs(gt) < 1e-9:
            roots.append(t)
        if k and gs[k - 1] * gt <= 0 and abs(gt) >= 1e-9 and abs(gs[k - 1]) >= 1e-9:
            a, b, ga = ts[k - 1], t, gs[k - 1]
            for _ in range(80):
                m = (a + b) / 2
                gm = g(m)
                if ga * gm <= 0:
                    b = m
                else:
                    a, ga = m, gm
            roots.append((a + b) / 2)
    return min(roots, key=lambda r: abs(r - prev_deg)) if roots else None


def transmission_angle_deg(rod_vec, follower_art: dict, pin) -> float:
    """Angle (0..90) between the rod and the horn arm r (pin - follower pivot, minus its part along the follower axis).
    90 = rod tangent to the horn arc; 0 = dead point."""
    rod = np.asarray(rod_vec, dtype=float)
    w = np.asarray(follower_art["axis"], dtype=float)
    w = w / np.linalg.norm(w)
    r = np.asarray(pin, dtype=float) - np.asarray(follower_art["pivot"], dtype=float)
    r = r - (r @ w) * w
    nr, nd = float(np.linalg.norm(r)), float(np.linalg.norm(rod))
    if nr < 1e-9 or nd < 1e-12:
        return 0.0
    return math.degrees(math.acos(min(1.0, abs(float(rod @ r)) / (nd * nr))))


def rod_transform(tip0, pin0, tip, pin) -> np.ndarray:
    """4x4 rigid transform taking tip0 to tip and turning the rod direction (pin0 - tip0) to (pin - tip) by the minimum rotation."""
    tip0, pin0, tip, pin = (np.asarray(x, dtype=float) for x in (tip0, pin0, tip, pin))
    u0 = (pin0 - tip0) / np.linalg.norm(pin0 - tip0)
    u1 = (pin - tip) / np.linalg.norm(pin - tip)
    c = np.cross(u0, u1)
    s = float(np.linalg.norm(c))
    rot = np.eye(4)
    if s > 1e-12:
        k = c / s
        kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        ang = math.atan2(s, float(u0 @ u1))
        rot[:3, :3] = np.eye(3) + math.sin(ang) * kx + (1 - math.cos(ang)) * (kx @ kx)
    to0, to1 = np.eye(4), np.eye(4)
    to0[:3, 3], to1[:3, 3] = -tip0, tip
    return to1 @ rot @ to0


def _four_bar_geometry(design: Design, mech: dict):
    atts = _atts(design)
    link = mech["link"]
    return (np.array(atts[link["driver_end"]]["location"], dtype=float), np.array(atts[link["follower_end"]]["location"], dtype=float),
            atts[mech["driver"]]["articulation"], atts[mech["driven"][0]]["articulation"])


def link_overrides(design: Design, mech: dict, input_deg: float, follower_deg: float) -> dict[str, np.ndarray]:
    """Four-bar only: the rod pose (component id -> 4x4) for the rod and everything downstream of link.driver_end."""
    from ..geometry import downstream_ids
    if mech.get("kinematics") != "four_bar":
        return {}
    tip0, pin0, drv, fol = _four_bar_geometry(design, mech)
    tip = _rot_point(drv, _clamp(input_deg, drv["range_deg"]), tip0)
    pin = _rot_point(fol, follower_deg, pin0)
    t = rod_transform(tip0, pin0, tip, pin)
    return {cid: t for cid in downstream_ids(design, _atts(design)[mech["link"]["driver_end"]])}


def consistent_four_bar_pose(design: Design, angles: dict[str, float]) -> tuple[dict[str, float], dict[str, np.ndarray]]:
    """T1: complete a configuration in which a four_bar mechanism has exactly one of its driver and driven joints off 0
    by solving the other from the rod length. Returns (angles, rod overrides: component id -> 4x4); a mechanism with no
    solution within the ranges, or with both or neither joint off 0, is left as given (no override)."""
    out, ov = dict(angles), {}
    for mech in design.data.get("mechanisms", []) or []:
        if mech.get("kinematics") != "four_bar" or not mech.get("link"):
            continue
        try:
            tip0, pin0, drv, fol = _four_bar_geometry(design, mech)
        except (KeyError, TypeError, IndexError):
            continue
        dl, fl = mech["driver"], mech["driven"][0]
        d, f = out.get(dl, 0.0), out.get(fl, 0.0)
        if (abs(d) > 1e-12) == (abs(f) > 1e-12):
            continue
        d_rng = (float(drv["range_deg"][0]), float(drv["range_deg"][1]))
        f_rng = (float(fol["range_deg"][0]), float(fol["range_deg"][1]))
        if abs(f) <= 1e-12:
            t = solve_four_bar(tip0, pin0, drv, fol, _clamp(d, d_rng), f_rng)
            if t is None:
                continue
            f = t
        else:
            t = solve_four_bar(pin0, tip0, fol, drv, f, d_rng)
            if t is None:
                continue
            d = t
        out[dl], out[fl] = d, f
        ov.update(link_overrides(design, mech, d, f))
    return out, ov


def _simulate_four_bar(design: Design, mech: dict) -> dict:
    th = load_gate_thresholds()
    min_mu, max_step = th["four_bar_min_transmission_deg"]["value"], th["four_bar_max_follower_step_deg"]["value"]
    try:
        tip0, pin0, drv, fol = _four_bar_geometry(design, mech)
    except (KeyError, TypeError, IndexError) as e:
        raise RuntimeError(f"mechanism {mech['id']}: could not build model: {e!r}") from e
    name = mech["driven"][0]
    lo, hi = _input_range(design, mech)
    rng = (float(fol["range_deg"][0]), float(fol["range_deg"][1]))
    inputs = _steps(lo, hi)
    order = [x for x in sorted(inputs) if x >= 0] + [x for x in sorted(inputs, reverse=True) if x < 0]
    done: dict[float, dict] = {}
    jam, neg = None, False
    prev_in, prev_t = 0.0, 0.0
    for x in order:
        if x < 0 and not neg:
            neg = True
            prev_in, prev_t = 0.0, 0.0
        d = _clamp(x, drv["range_deg"])
        t = solve_four_bar(tip0, pin0, drv, fol, d, rng, prev_t)
        if t is None:
            jam = {"input_deg": x, "reason": f"no follower angle within [{rng[0]:g}, {rng[1]:g}] keeps the rod length"}
            break
        tip, pin = _rot_point(drv, d, tip0), _rot_point(fol, t, pin0)
        mu = transmission_angle_deg(pin - tip, fol, pin)
        if mu < min_mu:
            jam = {"input_deg": x, "reason": f"transmission angle {mu:.1f} deg is below {min_mu:g} deg"}
            break
        per_deg = abs(t - prev_t) / max(1.0, abs(x - prev_in))
        if abs(t - prev_t) > max_step * max(1.0, abs(x - prev_in)):
            jam = {"input_deg": x, "reason": f"follower jumps {per_deg:.1f} deg for one degree of input"}
            break
        done[x] = {"input_deg": float(x), "followers": {name: t}, "transmission_deg": round(mu, 3)}
        prev_in, prev_t = x, t
    steps = [done[x] for x in inputs if x in done]
    out = {"mechanism": mech["id"], "driver": mech["driver"], "steps": steps}
    if jam:
        out["jam"] = jam
    return out


def simulate_mechanism(design: Design, mech: dict) -> dict:
    """Follower angle (deg) at each 1 degree of driver input: clamp(ratio x driver, follower range_deg).
    A follower sitting at its own limit is the jam. With kinematics: four_bar the angle is solved from the rod length
    instead (see solve_four_bar), and a jam is reported under the key "jam"."""
    refusal = _continuous_refusal(design, mech)
    if refusal:
        raise RuntimeError(refusal)
    if mech.get("kinematics") == "four_bar":
        return _simulate_four_bar(design, mech)
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
    four_bar = mech.get("kinematics") == "four_bar"
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
        ov = link_overrides(design, mech, s["input_deg"], next(iter(s["followers"].values()))) if four_bar else None
        posed = posed_component_parts(design, angles, ov) if four_bar else posed_component_parts(design, angles)
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


def link_ratios(design: Design, mech: dict) -> dict[str, float]:
    """Small-angle geometric ratio (driver degrees per driven degree) of each expect attachment that lies on the side of
    link.follower_end: attachment id -> unrounded ratio. math.inf marks a dead point (the follower end lies on that
    attachment's axis). {} when the mechanism has no link or its two link points coincide."""
    from ..geometry import downstream_ids
    atts, link = _atts(design), mech.get("link")
    if not link:
        return {}
    pd, pf = (np.array(atts[link[k]]["location"], dtype=float) for k in ("driver_end", "follower_end"))
    drv = atts[mech["driver"]]["articulation"]
    side = atts[link["follower_end"]]["child"]
    d = pf - pd
    if np.linalg.norm(d) < 1e-9:
        return {}
    u = d / np.linalg.norm(d)

    def lever(art, p):
        w = np.array(art["axis"], dtype=float)
        return float(u @ np.cross(w / np.linalg.norm(w), p - np.array(art["pivot"], dtype=float)))

    num = lever(drv, pd)
    out = {}
    for e in mech.get("expect", []):
        att = atts[e["attachment"]]
        if side not in downstream_ids(design, att):
            continue
        den = lever(att["articulation"], pf)
        out[e["attachment"]] = math.inf if abs(den) < 1e-9 else num / den
    return out


def _ratio_row(design: Design, mech: dict, atts: dict, th: dict) -> CheckResult | None:
    """Small-angle lever ratio from the two link points against each declared expect ratio."""
    mid, cid = mech["id"], f"T6.ratio.{mech['id']}"
    expect = mech.get("expect", [])
    if not expect:
        return None
    link = mech.get("link")
    if not link:
        r = ", ".join(f"{e['ratio']:g}" for e in expect)
        return CheckResult(cid, SKIP, f"mechanism {mid}: ratio {r} is declared, not measured: mechanisms[].link missing", CRIT)
    pd, pf = (np.array(atts[link[k]]["location"], dtype=float) for k in ("driver_end", "follower_end"))
    lo, hi = _input_range(design, mech)
    tol, floor = th["mechanism_ratio_tol"]["value"], th["mechanism_abs_tol_deg"]["value"]
    span = max(abs(lo), abs(hi)) or 1.0
    notes, data = [], {"driver_end": link["driver_end"], "follower_end": link["follower_end"], "ratios": {}}
    if np.linalg.norm(pf - pd) < 1e-9:
        return CheckResult(cid, FAIL, f"mechanism {mid}: dead point: link.driver_end and link.follower_end coincide", CRIT, data)
    geos = link_ratios(design, mech)
    for e in expect:
        if e["attachment"] not in geos:
            notes.append(f"{e['attachment']} not measured (link.follower_end is not on its side)")
            continue
        geo = geos[e["attachment"]]
        if math.isinf(geo):
            return CheckResult(cid, FAIL, f"mechanism {mid}: dead point: the follower end of the link lies on the "
                               f"axis of {e['attachment']} (lever 0)", CRIT, data)
        decl = float(e["ratio"])
        data["ratios"][e["attachment"]] = {"declared": decl, "geometric": round(geo, 4)}
        allowed = max(tol * abs(geo), floor / span)
        if abs(decl - geo) > allowed:
            return CheckResult(cid, FAIL, f"mechanism {mid}: {e['attachment']} declared ratio {decl:g} but the link geometry "
                               f"gives {geo:.3f} (allowed +-{allowed:.3f})", CRIT, data)
        notes.append(f"{e['attachment']} declared {decl:g}, geometry {geo:.3f}")
    if not data["ratios"]:
        return CheckResult(cid, SKIP, f"mechanism {mid}: no expect attachment lies on the side of link.follower_end", CRIT, data)
    return CheckResult(cid, PASS, f"mechanism {mid}: ratio matches the link geometry (small angle): " + "; ".join(notes), CRIT, data)


def _four_bar_needs(design: Design, mech: dict, atts: dict) -> str | None:
    """What a four_bar mechanism lacks (text after "four_bar needs "), or None."""
    from ..geometry import articulated_attachments, att_label, downstream_ids
    if not mech.get("link"):
        return "a link"
    if len(mech["driven"]) != 1:
        return "exactly one driven attachment"
    fol = mech["driven"][0]
    if fol not in {e["attachment"] for e in mech.get("expect", [])}:
        return "the driven attachment in expect"
    lo, hi = _input_range(design, mech)
    if not lo <= 0 <= hi:
        return "input_range_deg containing 0"
    parents = {atts[mech["driver"]]["parent"], atts[fol]["parent"]}
    for a in articulated_attachments(design):
        if att_label(a) in (mech["driver"], fol):
            continue
        if parents & downstream_ids(design, a):
            return f"the servo and the hinge's fixed side not to move with another articulated joint ({att_label(a)})"
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
    refusal = _continuous_refusal(design, mech)
    if refusal:
        return CheckResult(f"T6.mechanism.{mid}", FAIL, refusal, CRIT, data)
    four_bar = mech.get("kinematics") == "four_bar"
    if four_bar:
        need = _four_bar_needs(design, mech, atts)
        if need:
            return CheckResult(f"T6.mechanism.{mid}", FAIL, f"mechanism {mid}: four_bar needs {need}", CRIT, data)
    data["link_pairs"], err = _link(design, mech, atts)
    if err:
        return CheckResult(f"T6.mechanism.{mid}", FAIL, err, CRIT, data)
    try:
        sim = simulate_mechanism(design, mech)
    except RuntimeError as e:
        return CheckResult(f"T6.mechanism.{mid}", FAIL, str(e), CRIT, data)
    if "jam" in sim:
        j = sim["jam"]
        return CheckResult(f"T6.mechanism.{mid}", FAIL,
                           f"mechanism {mid}: four_bar jam at input {j['input_deg']:.0f} deg: {j['reason']}", CRIT, data)
    tol, floor = th["mechanism_ratio_tol"]["value"], th["mechanism_abs_tol_deg"]["value"]
    for s in ([] if four_bar else sim["steps"]):
        for att, ang in s["followers"].items():
            exp = expect[att] * s["input_deg"]
            allowed = max(tol * abs(exp), floor)
            if abs(ang - exp) > allowed:
                return CheckResult(f"T6.mechanism.{mid}", FAIL,
                                   f"mechanism {mid}: follower {att} at {ang:.1f} deg when input is {s['input_deg']:.0f} deg "
                                   f"(expected {exp:.1f} deg, tolerance {allowed:.1f} deg); first stalls at input "
                                   f"{s['input_deg']:.0f} deg", CRIT, data)
    msg = _collision(design, mech, sim, limit, th["mechanism_contact_step_deg"]["value"],
                     set() if four_bar else {frozenset(p) for p in data["link_pairs"]})
    if msg:
        return CheckResult(f"T6.mechanism.{mid}", FAIL, msg, CRIT, data)
    lo, hi = sim["steps"][0]["input_deg"], sim["steps"][-1]["input_deg"]
    step = th["mechanism_contact_step_deg"]["value"]
    if four_bar:
        worst = min(sim["steps"], key=lambda s: s["transmission_deg"])
        return CheckResult(f"T6.mechanism.{mid}", PASS,
                           f"mechanism {mid}: four_bar, no jam over {lo:.0f} to {hi:.0f} deg; follower angle solved from the "
                           f"rod length; minimum transmission angle {worst['transmission_deg']:.1f} deg at input "
                           f"{worst['input_deg']:.0f} deg; no collision at every {step:g} deg", CRIT, data)
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
    arts = [a for a in articulated_attachments(design) if a["articulation"].get("type") != "continuous"]
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
        if row.data.get("link_pairs") and m.get("kinematics") == "four_bar":
            if row.status == PASS:
                pairs = ", ".join(f"{a} & {b}" for a, b in row.data["link_pairs"])
                res.append(CheckResult(f"T6.link.{m['id']}", PASS, f"mechanism {m['id']}: four_bar link checked with the rod "
                                       f"posed on the horn pin: " + pairs, CRIT, {"link_pairs": row.data["link_pairs"], "parts": sorted({i for p in row.data["link_pairs"] for i in p})}))
        elif row.data.get("link_pairs"):
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
