"""Five report-only discipline checks (joint RF, control authority, transition margin, endurance, electrical rating) as tier sub-checks."""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import linprog

from ..design import FAIL, PASS, SKIP, CheckResult
from . import discipline_check
from .fidelity import resolve_threshold
from .interfaces import load_connection_types

OPS, LOADS, CT = "operations.yaml", "load-cases.yaml", "connection-types.yaml"


class _Missing(Exception):
    pass


def _entry(file: str, key: str) -> dict:
    th = resolve_threshold(f"{file}#{key}")
    if th is None or th["value"] is None:
        raise _Missing(f"{file}#{key}")
    return th


def _std(file: str, key: str, note: list[str]):
    """Model-input value; a pending source adds `file#key` to `note`."""
    th = _entry(file, key)
    if str(th["source"]).strip().lower() == "pending":
        note.append(f"{file}#{key}")
    return th["value"]


def _crit(file: str, key: str) -> tuple:
    """Criterion value and whether its source is pending."""
    th = _entry(file, key)
    return th["value"], str(th["source"]).strip().lower() == "pending"


def _prov(note: list[str]) -> str:
    return "; provisional: " + ", ".join(sorted(set(note))) + " pending" if note else ""


def _judge(check_id, status, numbers, crit_file_key, pending, data, criterion) -> CheckResult:
    if pending:
        return CheckResult(check_id, SKIP, f"{numbers}; not judged: {crit_file_key} pending", criterion,
                           {**data, "would_be": status})
    return CheckResult(check_id, status, numbers, criterion, data)


def _skip(check_id, why, crit, data=None) -> CheckResult:
    return CheckResult(check_id, SKIP, why, crit, data or {})


def _lift_motors(design) -> list[dict]:
    return [c for c in design.components if c["type"] == "motor"
            and c.get("propulsion", {}).get("role", "both") in ("lift", "both")]


def _vtol(design) -> bool:
    m = design.data["morphology"]
    return m.get("vtol_method", "none") != "none" or m["lift"] == "multirotor"


def _hover(ctx) -> dict | None:
    from ..checks import _hover_up, _upward_lift
    from ..geometry import pose_angles, pose_transforms, posed_component_parts
    from ..mass import mass_properties
    design, note = ctx.design, []
    up = _hover_up(design)
    hover_pose = design.data.get("flight", {}).get("hover_pose")
    h_ang = pose_angles(design, hover_pose)
    mp = mass_properties(design, h_ang) if hover_pose else ctx.mp
    tf = pose_transforms(design, h_ang)
    posed = posed_component_parts(design, h_ang)
    lift = _upward_lift(design, tf, up)
    f = {m["id"]: float(np.linalg.norm(force)) / m["propulsion"]["max_thrust_n"] for m, force in lift}
    if not f or sum(f.values()) <= 1e-9:
        return None
    sag = _std(OPS, "pack_sag_fraction", note)
    weight = mp["mass_g"] / 1000 * _g()
    thrust = weight / sum(f.values())
    tmax = {m["id"]: m["propulsion"]["max_thrust_n"] * (1 - sag) ** 2 for m, _ in lift}
    return {"mp": mp, "up": up, "tf": tf, "posed": posed, "lift": lift, "T": thrust, "Tmax": tmax, "f": f, "note": note}


def _g() -> float:
    from ..checks import G
    return G


def _rho(design) -> float:
    from ..checks import RHO_DEFAULT
    return design.data.get("flight", {}).get("air_density_kgm3", RHO_DEFAULT)


def _axis_moment(c, a, dt_lo, dt_hi) -> float:
    """T37 (D58): the largest moment about one axis both ways that the motors give with the net upward thrust held (sum a_i dT_i = 0,
    dT_i in [dt_lo_i, dt_hi_i]); returns min(M(+), M(-)), or 0.0 when the solver finds no feasible allocation."""
    best = []
    for sign in (1.0, -1.0):
        res = linprog(-sign * np.asarray(c, dtype=float), A_eq=[list(a)], b_eq=[0.0], bounds=list(zip(dt_lo, dt_hi)), method="highs")
        if res.status != 0:
            return 0.0
        best.append(-float(res.fun))
    return max(0.0, min(best))


def _active(h: dict) -> list[dict]:
    """Lift motors that have an upward thrust component at hover."""
    return [m for m, _ in h["lift"] if h["f"][m["id"]] > 1e-9]


# ---------------------------------------------------------------- T2.joint_rf
@discipline_check("T2.joint_rf", 2)
def joint_rf(ctx, rep) -> list[CheckResult]:
    from ..checks import _subtree_mass, joint_own_rating
    cid, crit = "T2.joint_rf", f"{LOADS}#joint_rf_min"
    design = ctx.design
    try:
        rf_min, pending = _crit(LOADS, "joint_rf_min")
    except _Missing as e:
        return [_skip(cid, f"{e} missing", crit)]
    s = ctx.std["structure"]
    n = s["landing_load_factor"]["value"] * s.get("ultimate_factor", {}).get("value", 1.0)
    lib = load_connection_types()
    res = []
    for a in design.data.get("attachments", []):
        if "connection" not in a:
            continue
        label = a.get("id") or f"{a['parent']}->{a['child']}"
        t = lib.get(a["connection"])
        if t is None:
            res.append(_skip(cid, f"{label}: connection {a['connection']} not in standards/connection-types.yaml",
                             crit, {"joint": label}))
            continue
        if t.get("structural", True) is False:
            continue
        own, basis = joint_own_rating(a)
        rated = own if own is not None else t.get("rated_load_n")
        if rated is None:
            res.append(_skip(cid, f"{label}: {t['id']} has no rated_load_n in standards/connection-types.yaml and the joint states none (pending a sourced rating)",
                             crit, {"joint": label}))
            continue
        load = _subtree_mass(design, a["parent"], a["child"]) / 1000 * _g() * n
        rf = rated / load
        where = "joint" if own is not None else "library"
        msg = f"{label}: RF {rf:.2f} (rating {rated} N, {where} value / load {load:.1f} N at {n}g) vs min {rf_min}"
        status = PASS if rf >= rf_min else FAIL
        data = {"joint": label, "rf": round(rf, 3), "rating_source": where}
        if own is not None and basis == "derived" and not pending:
            res.append(_skip(cid, f"{msg}; not judged: the joint's rating is derived, pending a sourced value", crit,
                             {**data, "would_be": status}))
        else:
            res.append(_judge(cid, status, msg, f"{LOADS}#joint_rf_min", pending, data, crit))
    if not res:
        res.append(_skip(cid, "no structural attachment declares a connection (attachments[].connection)",
                         crit, {"parts": []}))
    return res


# ---------------------------------------------------------------- T3.control_authority
@discipline_check("T3.control_authority", 3)
def control_authority(ctx, rep) -> list[CheckResult]:
    cid, crit = "T3.control_authority", f"{OPS}#hover_ctrl_factor"
    design = ctx.design
    if not _lift_motors(design) or not _vtol(design):
        return [_skip(cid, "not applicable: no lift motors or vtol_method none", crit)]
    try:
        h = _hover(ctx)
        if h is None:
            return [CheckResult(cid, FAIL, "no lift motor has upward thrust at hover", crit)]
        note = h["note"]
        factor, pending = _crit(OPS, "hover_ctrl_factor")
        v_wind = _std(OPS, "hover_wind_mps", note)
        cd = _std(OPS, "wind_drag_coefficient", note)
        lever_frac = _std(OPS, "wind_moment_min_lever_fraction", note)
    except _Missing as e:
        return [_skip(cid, f"{e} missing", crit)]
    T, active = h["T"], _active(h)
    over = [m for m in active if T > h["Tmax"][m["id"]]]
    if over:
        tm = h["Tmax"][over[0]["id"]]
        return [CheckResult(cid, FAIL, f"hover thrust {T:.2f} N exceeds the sagged-pack maximum {tm:.2f} N"
                            + _prov(note), crit, {"axis": "all"})]
    cg = np.array(h["mp"]["cg_mm"], dtype=float)
    up = h["up"]
    taus = []
    for m in active:
        parts = h["posed"][m["id"]]
        if not parts:
            return [_skip(cid, f"motor {m['id']}: no geometry for its position", crit)]
        p = np.mean([np.asarray(pt.center_mass, dtype=float) for pt in parts], axis=0)
        u = h["tf"][m["id"]][:3, :3] @ np.array(m["propulsion"]["axis"], dtype=float)
        u = u / np.linalg.norm(u)
        taus.append((np.cross((p - cg) / 1000, u), float(np.dot(u, up)), -T, h["Tmax"][m["id"]] - T))
    h0 = np.array([0.0, 1.0, 0.0]) - np.dot([0.0, 1.0, 0.0], up) * up
    if np.linalg.norm(h0) < 1e-6:
        h0 = np.array([0.0, 0.0, 1.0])
    pitch = h0 / np.linalg.norm(h0)
    axes = {"pitch": pitch, "roll": np.cross(up, pitch), "yaw": up}
    allparts = [pt for ps in h["posed"].values() for pt in ps if len(pt.vertices)]
    if not allparts:
        return [_skip(cid, "no geometry for the wind moment", crit)]
    lo = np.min([pt.bounds[0] for pt in allparts], axis=0)
    hi = np.max([pt.bounds[1] for pt in allparts], axis=0)
    ext = hi - lo
    ext_up = float(np.sum(np.abs(up) * ext))
    ext_h = lambda e: float(np.sum(np.abs(e) * ext))  # noqa: E731
    area = max(ext_h(axes["pitch"]), ext_h(axes["roll"])) * ext_up / 1e6
    lever = max(abs(float(np.dot((lo + hi) / 2 - cg, up))), lever_frac * ext_up) / 1000
    m_wind = 0.5 * _rho(design) * v_wind ** 2 * cd * area * lever
    res = []
    trim_yaw = T * sum(float(np.dot(tau, up)) for tau, _, _, _ in taus)
    for name, e in axes.items():
        m_axis = _axis_moment([float(np.dot(tau, e)) for tau, _, _, _ in taus], [a for _, a, _, _ in taus],
                              [lo_ for _, _, lo_, _ in taus], [hi_ for _, _, _, hi_ in taus])
        r = m_axis / m_wind if m_wind > 0 else math.inf
        msg = (f"{name}: control moment {m_axis:.3f} N*m, wind moment {m_wind:.3f} N*m, ratio {r:.2f} vs min {factor} "
               "(sagged pack, differential thrust at constant total upward thrust, cant geometry only)")
        data = {"axis": name}
        if name == "yaw":
            data["trim_yaw_nm"] = round(trim_yaw, 3)
            msg += f"; yaw moment at equal hover thrust {trim_yaw:.3f} N*m (not judged); yaw wind moment uses the pitch/roll model (conservative)"
        msg += _prov(note)
        if name == "yaw" and r < factor:
            res.append(_skip(cid, msg + "; not judged: yaw from prop reaction torque is not modelled (PDL has no spin/torque field)",
                             crit, {**data, "would_be": FAIL}))
        else:
            res.append(_judge(cid, PASS if r >= factor else FAIL, msg, f"{OPS}#hover_ctrl_factor", pending, data, crit))
    return res


# ---------------------------------------------------------------- T3.transition_margin
@discipline_check("T3.transition_margin", 3)
def transition_margin(ctx, rep) -> list[CheckResult]:
    cid, crit = "T3.transition_margin", f"{OPS}#transition_thrust_fraction_max"
    design = ctx.design
    if design.data["morphology"].get("vtol_method", "none") == "none":
        return [_skip(cid, "not applicable: morphology.vtol_method is none", crit)]
    motors = _lift_motors(design)
    if not motors:
        return [_skip(cid, "no lift motors", crit)]
    res = []
    flight = design.data.get("flight", {})
    # Row A: declared transition speed against the stall speed
    crit_a = f"{OPS}#transition_stall_ratio_min"
    try:
        ratio_min, pend_a = _crit(OPS, "transition_stall_ratio_min")
        if "transition_speed_mps" not in flight:
            res.append(_skip(cid, "speed margin: flight.transition_speed_mps missing", crit_a,
                             {"parts": ["transition_speed"]}))
        elif not flight.get("transition_speed_source"):
            res.append(_skip(cid, "speed margin: flight.transition_speed_source missing", crit_a,
                             {"parts": ["transition_speed"]}))
        else:
            stall = next((r.data.get("stall_mps") for r in (rep.results if rep else []) if r.check_id == "T3.stall"), None)
            if stall is None:
                res.append(_skip(cid, "speed margin: no T3.stall row (no lifting surface)", crit_a,
                                 {"parts": ["transition_speed"]}))
            else:
                v = flight["transition_speed_mps"]
                ratio = v / stall
                msg = f"speed margin: transition speed {v} m/s / stall {stall} m/s = {ratio:.2f} vs min {ratio_min}"
                res.append(_judge(cid, PASS if ratio >= ratio_min else FAIL, msg, crit_a, pend_a,
                                  {"parts": ["transition_speed"]}, crit_a))
    except _Missing as e:
        res.append(_skip(cid, f"speed margin: {e} missing", crit_a, {"parts": ["transition_speed"]}))
    # Row B: hover thrust fraction at entry
    try:
        h = _hover(ctx)
        if h is None:
            res.append(CheckResult(cid, FAIL, "entry thrust fraction: no lift motor has upward thrust at hover", crit))
        else:
            fmax, pend_b = _crit(OPS, "transition_thrust_fraction_max")
            active = _active(h)
            frac = max(h["T"] / h["Tmax"][m["id"]] for m in active)
            msg = (f"entry thrust fraction: hover thrust {h['T']:.2f} N is {frac:.2f} of the sagged-pack maximum "
                   f"vs max {fmax}" + _prov(h["note"]))
            res.append(_judge(cid, PASS if frac <= fmax else FAIL, msg, crit, pend_b,
                              {"parts": [m["id"] for m in active]}, crit))
    except _Missing as e:
        res.append(_skip(cid, f"entry thrust fraction: {e} missing", crit))
    return res


# ---------------------------------------------------------------- T3.endurance
@discipline_check("T3.endurance", 3)
def endurance(ctx, rep) -> list[CheckResult]:
    cid, crit = "T3.endurance", f"{OPS}#energy_reserve_fraction"
    design = ctx.design
    req, flight = design.data.get("requirements", {}), design.data.get("flight", {})
    note: list[str] = []
    try:
        reserve, pending = _crit(OPS, "energy_reserve_fraction")
        eta = _std(OPS, "propulsive_efficiency", note)
        t_hover = _std(OPS, "mission_hover_min", note)
        t_cruise = _std(OPS, "mission_cruise_min", note)
        usable = _std(OPS, "battery_usable_fraction", note)
        cell_v = _std(OPS, "lipo_nominal_cell_v", note)
        weight = ctx.mp["mass_g"] / 1000 * _g()
        rho = _rho(design)
        e_hover = e_cruise = 0.0
        phases = []
        if _vtol(design):
            h = _hover(ctx)
            if h is not None:
                note += h["note"]
                p_sum = 0.0
                for m in _active(h):
                    d = m["propulsion"].get("prop_diameter_mm")
                    if d is None:
                        return [_skip(cid, f"motor {m['id']}: propulsion.prop_diameter_mm missing", crit)]
                    area = math.pi * (d / 2000) ** 2
                    p_sum += h["T"] ** 1.5 / math.sqrt(2 * rho * area)
                e_hover = p_sum / eta * t_hover * 60
                phases.append(f"hover {e_hover / 3600:.2f} Wh")
        if design.data["morphology"]["lift"] != "multirotor":
            for path, ok in (("requirements.cruise_speed_mps", "cruise_speed_mps" in req),
                             ("flight.cruise_ld", "cruise_ld" in flight),
                             ("flight.cruise_ld_source", bool(flight.get("cruise_ld_source")))):
                if not ok:
                    return [_skip(cid, f"{path} missing", crit)]
            e_cruise = weight * req["cruise_speed_mps"] / (flight["cruise_ld"] * eta) * t_cruise * 60
            phases.append(f"cruise {e_cruise / 3600:.2f} Wh")
        if not phases:
            return [_skip(cid, "no mission phase applies (not vtol with upward thrust, and multirotor)", crit)]
        packs = [c for c in design.components if c["type"] == "battery" and "battery" in c]
        if not packs:
            return [_skip(cid, "no battery component with a `battery` block (components[].battery)", crit)]
        e_usable = sum(c["battery"]["capacity_mah"] / 1000 * c["battery"]["cells_s"] * cell_v * 3600 * usable
                       for c in packs)
    except _Missing as e:
        return [_skip(cid, f"{e} missing", crit)]
    e_need = (e_hover + e_cruise) * (1 + reserve)
    msg = (f"usable {e_usable / 3600:.1f} Wh vs need {e_need / 3600:.1f} Wh ({', '.join(phases)}, "
           f"+{reserve:.0%} reserve)" + _prov(note))
    return [_judge(cid, PASS if e_usable >= e_need else FAIL, msg, f"{OPS}#energy_reserve_fraction", pending,
                   {"parts": [c["id"] for c in packs]}, crit)]


# ---------------------------------------------------------------- T7.electrical_rating
@discipline_check("T7.electrical_rating", 7)
def electrical_rating(ctx, rep) -> list[CheckResult]:
    cid, crit = "T7.electrical_rating", f"{CT}#wire_ampacity_a"
    design = ctx.design
    note: list[str] = []
    motors = [c for c in design.components if c["type"] == "motor"]
    if not motors:
        return [_skip(cid, "no motor component", crit)]
    for m in motors:
        if "max_current_a" not in m.get("propulsion", {}):
            return [_skip(cid, f"motor {m['id']}: propulsion.max_current_a missing", crit, {"parts": [m["id"]]})]
    peak = sum(m["propulsion"]["max_current_a"] for m in motors)
    batteries = [c["id"] for c in design.components if c["type"] == "battery"]
    if not batteries:
        return [_skip(cid, "no battery component", crit)]
    try:
        ratio, ratio_pending = _crit(OPS, "electrical_rating_min_ratio")
        res = []

        def compare(label, rating, parts, what):
            ok = rating >= peak * ratio
            msg = f"{label}: {what} {rating:.1f} A vs peak {peak:.1f} A x {ratio}"
            return _judge(cid, PASS if ok else FAIL, msg, f"{OPS}#electrical_rating_min_ratio", ratio_pending,
                          {"parts": parts}, crit)

        for c in design.components:
            if c["type"] != "battery":
                continue
            b = c.get("battery", {})
            if "max_discharge_c" not in b or "capacity_mah" not in b:
                res.append(_skip(cid, f"{c['id']}: battery.max_discharge_c missing", crit, {"parts": [c["id"]]}))
            else:
                res.append(compare(f"pack {c['id']}", b["capacity_mah"] / 1000 * b["max_discharge_c"], [c["id"]],
                                   "discharge rating"))
        lib = load_connection_types()
        for a in design.data.get("attachments", []):
            if "connection" not in a or not ({a["parent"], a["child"]} & set(batteries)):
                continue
            label = a.get("id") or f"{a['parent']}->{a['child']}"
            parts = [a["parent"], a["child"]]
            t = lib.get(a["connection"])
            if t is None:
                res.append(_skip(cid, f"{label}: connection {a['connection']} not in standards/connection-types.yaml",
                                 crit, {"parts": parts}))
            elif t.get("kind") != "electrical":
                continue  # a strap or tape is not a disconnect
            elif "rated_current_a" not in t:
                res.append(_skip(cid, f"{label}: {t['id']} has no rated_current_a in standards/connection-types.yaml (pending a sourced value)",
                                 crit, {"parts": parts}))
            else:
                res.append(compare(f"disconnect {label}", t["rated_current_a"], parts, f"{t['id']} rating"))
        table, wire_pending = _crit(CT, "wire_ampacity_a")
        derate = _std(OPS, "wire_pair_derate", note)
        table = {int(k): v for k, v in table.items()}
        for h in design.data.get("wiring", {}).get("harnesses", []):
            if not ({h["from"], h["to"]} & set(batteries)):
                continue
            parts = [h["from"], h["to"]]
            g = h.get("gauge_awg")
            if g is None:
                res.append(_skip(cid, f"{h['id']}: wiring.harnesses[].gauge_awg missing", crit, {"parts": parts}))
            elif int(g) not in table:
                res.append(_skip(cid, f"{h['id']}: {g} AWG not in connection-types.yaml#wire_ampacity_a", crit,
                                 {"parts": parts}))
            else:
                cap = table[int(g)] * derate
                ok = cap >= peak
                msg = (f"harness {h['id']}: {g} AWG {table[int(g)]} A x {derate} = {cap:.1f} A vs peak {peak:.1f} A"
                       + _prov(note))
                res.append(_judge(cid, PASS if ok else FAIL, msg, crit, wire_pending, {"parts": parts}, crit))
    except _Missing as e:
        return [_skip(cid, f"{e} missing", crit)]
    return res
