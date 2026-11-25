"""Concept A calculations ported from the team's redesign/qp/A/proofs at a93f14d; registered by name in hangar.calcs.CALCS."""
import math
from datetime import date, timedelta as td


# ================================================================ propulsion model (prop_a.py, parameterised)
def _prop(tab, n):
    ks = sorted(tab, key=lambda r: r[0])
    n = max(ks[0][0], min(ks[-1][0], n))
    for a, b in zip(ks, ks[1:]):
        if a[0] <= n <= b[0]:
            f = (n - a[0]) / (b[0] - a[0])
            return a[1] + f * (b[1] - a[1]), a[2] + f * (b[2] - a[2])


def _run(tab, kv, rm, i0, vm):
    """motor terminal voltage -> (rpm, I, thrust N, shaft W)"""
    kt = 60 / (2 * math.pi * kv)
    lo, hi = 3000.0, 12000.0
    for _ in range(60):
        n = (lo + hi) / 2
        th, pw = _prop(tab, n)
        q = pw / (n * 2 * math.pi / 60)
        v = n / kv + (q / kt + i0) * rm
        lo, hi = (n, hi) if v < vm else (lo, n)
    n = (lo + hi) / 2
    th, pw = _prop(tab, n)
    q = pw / (n * 2 * math.pi / 60)
    return n, q / kt + i0, th, pw


def _full(tab, kv, rm, i0, rp, vrest, duty):
    """four motors saturated at `duty`, pack drop through rp"""
    lo, hi = 3.0, vrest
    for _ in range(50):
        vb = (lo + hi) / 2
        i = _run(tab, kv, rm, i0, vb * duty)[1]
        lo, hi = (vb, hi) if vrest - 4 * i * rp > vb else (lo, vb)
    return _run(tab, kv, rm, i0, vb * duty) + (vb,)


def _hover(tab, kv, rm, i0, m, der, cant, dl, eff, cm, g):
    """(gf per motor, rpm, A per motor, motor W, pack W incl. margins, pack A, motor volts)"""
    t = m * g / (4 * math.cos(math.radians(cant)) * dl) / der
    lo, hi = 3.0, 16.0
    for _ in range(60):
        vm = (lo + hi) / 2
        lo, hi = (vm, hi) if _run(tab, kv, rm, i0, vm)[2] < t else (lo, vm)
    n, i, th, pw = _run(tab, kv, rm, i0, vm)
    pin_ = vm * i / eff * cm
    return t * der / g * 1000, n, i, vm * i, 4 * pin_, 4 * pin_ / 14.8, vm


def _tw(tab, kv, rm, i0, rp, der, cant, hot, spin_cap, v_fresh, v_sag_rest, g, lo, hi_frac, m):
    th = {}
    for tag, vr in (("fresh", v_fresh), ("sag", v_sag_rest)):
        for duty in (1.0, spin_cap):
            t_ = _full(tab, kv, rm, i0, rp, vr, duty)[2]
            th[(tag, duty)] = 4 * t_ / g * 1000 * (hot if tag == "sag" else 1.0) * der * math.cos(math.radians(cant))
    r = {k: v / (m * 1000) for k, v in th.items()}
    win = lambda tw: 100 * (hi_frac * tw - lo) / (hi_frac * tw + lo)
    return {"fresh_cap": r[("fresh", spin_cap)], "sag_cap": r[("sag", spin_cap)], "fresh_unc": r[("fresh", 1.0)], "sag_unc": r[("sag", 1.0)],
            "window_cap_pct": win(r[("sag", spin_cap)]), "window_unc_pct": win(r[("sag", 1.0)]), "sag_cap_gf": th[("sag", spin_cap)]}


def _one_motor(apc_table, kv, rm_ohm, i0_a, rp_ohm, derate, cant_deg, download, spin_cap, v_fresh, g, m, duty):
    ih = _hover(apc_table, kv, rm_ohm, i0_a, m, 1.0, cant_deg, download, 0.98, 1.10, g)
    vb = v_fresh
    for _ in range(30):
        i = _run(apc_table, kv, rm_ohm, i0_a, vb * duty)[1]
        ipack = i * duty + 3 * ih[2] * ih[6] / vb
        vb = v_fresh - rp_ohm * ipack
    return i


# ================================================================ mass
def mass_pred(basic, gf, over, gate):
    return basic * gf + over * gate


def mass_itemised(items, over, gate):
    base = sum(g for g, _ in items)
    growth = sum(g * k for g, k in items)
    return (base + growth) / 1000 + over * gate


def cuts_required(cuts, target, m, gf):
    return cuts - (target - m) * 1000 / gf


def structure_mass(g):
    return sum(g)


# ================================================================ CG, static margin
def cg_trim(cg, pack, trim, trim_fwd, basic):
    s = pack * trim / (basic * 1000)
    sf = pack * trim_fwd / (basic * 1000)
    return {"shift_mm": s, "fwd_mm": cg - sf, "aft_mm": cg + s}


def static_margin(np, cg, c):
    return (np - cg) / c * 100


# ================================================================ thrust-to-weight and the transition window
def tw_at(apc_table, kv, rm_ohm, i0_a, rp_ohm, derate, cant_deg, download, hot_sag, spin_cap, v_fresh, v_sag_rest, g, lo, hi_frac, m):
    return _tw(apc_table, kv, rm_ohm, i0_a, rp_ohm, derate, cant_deg, hot_sag, spin_cap, v_fresh, v_sag_rest, g, lo, hi_frac, m)


def window_mass(apc_table, kv, rm_ohm, i0_a, rp_ohm, derate, cant_deg, download, hot_sag, spin_cap, v_fresh, v_sag_rest, g, lo, hi_frac, w):
    th = _tw(apc_table, kv, rm_ohm, i0_a, rp_ohm, derate, cant_deg, hot_sag, spin_cap, v_fresh, v_sag_rest, g, lo, hi_frac, 1.0)["sag_cap_gf"]
    w = w / 100
    return th * hi_frac / (lo * (1 + w) / (1 - w)) / 1000


# ================================================================ motor current, ESC
def motor_current_capped(apc_table, kv, rm_ohm, i0_a, rp_ohm, derate, cant_deg, download, spin_cap, v_fresh, g, m, duty):
    return _one_motor(apc_table, kv, rm_ohm, i0_a, rp_ohm, derate, cant_deg, download, spin_cap, v_fresh, g, m, duty)


def esc_required(apc_table, kv, rm_ohm, i0_a, rp_ohm, derate, cant_deg, download, spin_cap, v_fresh, g, m, factor):
    return factor * _one_motor(apc_table, kv, rm_ohm, i0_a, rp_ohm, derate, cant_deg, download, spin_cap, v_fresh, g, m, 1.0)


# ================================================================ mission: cruise time, energy to BATT_LOW, fence
def cruise_need(v, g, bank, leg, settle, laps, ga, runin):
    r = v * v / (g * math.tan(math.radians(bank)))
    tl = (2 * leg + 2 * math.pi * r) / v
    return {"need_s": settle + (laps + ga + runin) * tl, "radius_m": r, "lap_s": tl}


def endurance(apc_table, kv, rm_ohm, i0_a, derate, cant_deg, download, esc_eff, ctrl_margin, g, m, pack_ah, pack_v, floor_frac, reserve_frac, hover_s,
              trans_wh_ref, climb_wh_ref, cruise_w_ref, ref_mass_kg, trans_exp, cruise_exp):
    usable = pack_ah * pack_v * floor_frac * reserve_frac
    ph = _hover(apc_table, kv, rm_ohm, i0_a, m, derate, cant_deg, download, esc_eff, ctrl_margin, g)[4]
    eh, etr, ecl = ph * hover_s / 3600, trans_wh_ref * (m / ref_mass_kg) ** trans_exp, climb_wh_ref * (m / ref_mass_kg)
    pc = cruise_w_ref * (m / ref_mass_kg) ** cruise_exp
    return {"cruise_s": (usable - eh - etr - ecl) / pc * 3600, "usable_wh": usable, "hover_w": ph, "cruise_w": pc}


def fence_bound(leg, r, runout):
    return leg / 2 + r + runout


# ================================================================ stall
def stall(m, g, rho, s, cl, k):
    vs = math.sqrt(2 * m * g / (rho * s * cl))
    return {"vs_ms": vs, "k_vs_ms": k * vs}


# ================================================================ hover yaw authority
def yaw_authority(cant_term_ref_nm, arm_factor, cant_deg, cant_ref_deg, q_model_nmm, q_gain):
    return (cant_term_ref_nm * arm_factor * math.sin(math.radians(cant_deg)) / math.sin(math.radians(cant_ref_deg))
            + q_gain * q_model_nmm / 1000)


# ================================================================ pitch use
def pitch_use(peak, stop):
    return peak / stop


# ================================================================ flutter, divergence, reversal, vibration (shared helpers)
def lowest(x):
    return min(x)


def highest(x):
    return max(x)


def flutter_line(k, vd):
    return k * vd


def wing_flutter_lowest(base, nofin):
    return min(min(base), min(nofin))


def bridge_tau(od, idd, m, k):
    j = math.pi / 32 * (od ** 4 - idd ** 4)            # mm4
    return k * m * 1e3 * (od / 2) / j                    # MPa


def vib_low_limit(rpm, sep):
    return rpm / 60 / sep


def vib_high_limit(f, sep):
    return f * sep


def gm_shifted(lo, hi):
    return min(min(lo), min(hi))


# ================================================================ servo torque at the 7.2 V rail
def servo_factors(stall_72_nm, hinge_vd_nm, preload_nm, damper_slew_nm, damper_slew_cold_nm, load_factor, arm_mm, horn_mm):
    req = load_factor * (hinge_vd_nm + preload_nm + damper_slew_nm)
    req_cold = load_factor * (hinge_vd_nm + preload_nm + damper_slew_cold_nm)
    return {"factor_25c": stall_72_nm / req, "factor_0c_equal_arms": stall_72_nm / req_cold,
            "factor_0c_real_arms": stall_72_nm * horn_mm / arm_mm / req_cold, "ratio_to_hinge": stall_72_nm / hinge_vd_nm}


# ================================================================ cost, schedule, transport
def bom_cost(rows, tax, faa, ship, bump, tubes, budget, rship=None):
    sh = dict(ship)
    shipping = sum(sh[g] for g in {r[2] for r in rows})
    line = lambda i: next(r[4] for r in rows if r[0] == i)
    extra = sum(rship) if rship is not None else sh["TMotor"] + sh["RMRC"] + sh["Amazon"]

    def total(b):
        goods = sum(q * u * (1 + (b if unv else 0)) for _, _, _, q, u, unv in rows)
        f = 1 + b
        air = line("R01") * f + sum(r[3] * r[4] for r in rows if r[0] in tubes) + 0.5 * line("R03") * f
        reserve = (line("W01") + line("P01") + line("M01") + air) * (1 + tax) + extra
        return goods * (1 + tax) + shipping + faa + reserve, reserve
    t0, r0 = total(0.0)
    t30, r30 = total(bump)
    return {"total_usd": t0, "total_30_usd": t30, "margin_usd": budget - t0, "margin_30_usd": budget - t30, "reserve_usd": r0, "shipping_usd": shipping}


def _sched_run(gates, start, repair, redo, recess, booked, p, crash):
    r0, r1 = (date.fromisoformat(x) for x in recess)

    def rate(d):
        return (booked + (1 if r0 <= d <= r1 else 0)) * p

    def advance(d, need):
        while need > 0:
            r = rate(d)
            if need <= r:
                return d + td(days=round(7 * need / r))
            need -= r
            d += td(days=7)
        return d
    d, end = start, start
    for i, n in enumerate(gates):
        d = advance(d, n)
        end = d
        if crash and i == 3:                                   # after F04: repair loop, then F04 repeated
            d += td(days=repair)
            d = advance(d, redo)
            end = d
    return end


def schedule(gates, start, deadline, repair, redo, recess, booked, p, p_sens, req_f01):
    s, dl = date.fromisoformat(start), date.fromisoformat(deadline)
    end = _sched_run(gates, s, repair, redo, recess, booked, p, True)
    late = s
    while _sched_run(gates, late, repair, redo, recess, booked, p, True) > dl:
        late -= td(days=1)
    while _sched_run(gates, late + td(days=1), repair, redo, recess, booked, p, True) <= dl:
        late += td(days=1)
    end_sens = _sched_run(gates, s, repair, redo, recess, booked, p_sens, True)
    return {"slack_days": (dl - end).days, "f01_slack_days": (late - s).days, "f01_to_req_days": (date.fromisoformat(req_f01) - s).days,
            "slack_sens_days": (dl - end_sens).days}


def box_fit(box, lim):
    return max(a / b for a, b in zip(sorted(box, reverse=True), sorted(lim, reverse=True)))


# ================================================================ scaling helper for design-to-claim unit conversion
def scale_value(v, k):
    return {"value": v * k}


CALCS = {
    "mass_pred": mass_pred,
    "mass_itemised": mass_itemised,
    "cuts_required": cuts_required,
    "structure_mass": structure_mass,
    "cg_trim": cg_trim,
    "static_margin": static_margin,
    "tw_at": tw_at,
    "window_mass": window_mass,
    "motor_current_capped": motor_current_capped,
    "esc_required": esc_required,
    "cruise_need": cruise_need,
    "endurance": endurance,
    "fence_bound": fence_bound,
    "stall": stall,
    "yaw_authority": yaw_authority,
    "pitch_use": pitch_use,
    "lowest": lowest,
    "highest": highest,
    "flutter_line": flutter_line,
    "wing_flutter_lowest": wing_flutter_lowest,
    "bridge_tau": bridge_tau,
    "vib_low_limit": vib_low_limit,
    "vib_high_limit": vib_high_limit,
    "gm_shifted": gm_shifted,
    "servo_factors": servo_factors,
    "bom_cost": bom_cost,
    "schedule": schedule,
    "box_fit": box_fit,
    "scale_value": scale_value,
}
