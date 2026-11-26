"""U18.4: tail volume coefficients (and, in later briefs, trim and dynamic modes) for fixed-wing designs; thresholds in standards/stability.yaml."""
from __future__ import annotations

import math  # noqa: F401  (named in the brief; later U18.4 briefs use it)

import numpy as np

from ..calcs import trim as trimcalc
from ..checks import G, RHO_DEFAULT
from ..design import FAIL, PASS, SKIP, WARN, CheckResult
from ..geometry import lifting_surface_properties, rotation_matrix
from . import discipline_check
from .applicability import skip_row
from .fidelity import resolve_threshold

ST = "stability.yaml"


def declared_surfaces(design) -> list[dict]:
    out = []
    for c in design.data["components"]:
        ls = (c.get("geometry") or {}).get("lifting_surface")
        if not ls:
            continue
        p = lifting_surface_properties(c)
        y = rotation_matrix(c.get("rotation_deg")) @ np.array([0.0, 1.0, 0.0])
        out.append({"id": c["id"], "area_mm2": p["area_mm2"], "mac_mm": p["mac_mm"], "x_ac_mm": p["x_ac_mm"],
                    "span_mm": ls["span"], "aspect_ratio": p["aspect_ratio"], "lifting": p["lifting"],
                    "vertical": bool(abs(y[2]) > abs(y[1]))})
    return out


def main_and_tails(surfaces):
    cands = [s for s in surfaces if not s["vertical"] and s["lifting"]]
    if not cands:
        return None, [], []
    main = max(cands, key=lambda s: s["area_mm2"])
    h = [s for s in cands if s["id"] != main["id"] and s["x_ac_mm"] > main["x_ac_mm"]]
    v = [s for s in surfaces if s["vertical"] and s["x_ac_mm"] > main["x_ac_mm"]]
    return main, h, v


def _na(ctx, cid, what, crit):
    m = ctx.design.data["morphology"]
    if m["lift"] == "fixed-wing":
        return None
    return skip_row(cid, f"not applicable: {what} is for fixed-wing designs with a tail "
                         f"(morphology lift={m['lift']}, vtol_method={m.get('vtol_method', 'none')})", crit)


@discipline_check("T3.tail_volume", 3)
def tail_volume(ctx, rep) -> list[CheckResult]:
    cid, crit = "T3.tail_volume", f"{ST}#tail_volume_h_min"
    na = _na(ctx, cid, "tail volume", crit)
    if na:
        return [na]
    main, h, v = main_and_tails(declared_surfaces(ctx.design))
    if main is None:
        return [CheckResult(cid, SKIP, "no main wing found among declared lifting_surface components "
                            "(generated tail_surfaces and mesh planforms are not read yet)", crit)]
    S, c, b = main["area_mm2"], main["mac_mm"], main["span_mm"]
    out = []
    for name, key, tails, ref in (("Vh", "h", h, S * c), ("Vv", "v", v, S * b)):
        kcrit = f"{ST}#tail_volume_{key}_min"
        if not tails:
            kind = "horizontal" if key == "h" else "vertical"
            out.append(CheckResult(cid, SKIP, f"no {kind} tail found among declared lifting_surface components",
                                   kcrit, {"coefficient": name}))
            continue
        x = sum(t["area_mm2"] * (t["x_ac_mm"] - main["x_ac_mm"]) for t in tails) / ref
        lo_t, hi_t = (resolve_threshold(f"{ST}#tail_volume_h_min"), resolve_threshold(f"{ST}#tail_volume_h_max")) \
            if key == "h" else (resolve_threshold(f"{ST}#tail_volume_v_min"), resolve_threshold(f"{ST}#tail_volume_v_max"))
        lo, hi = lo_t["value"], hi_t["value"]
        band = "below" if x < lo else "above" if x > hi else "within"
        data = {"coefficient": name, "value": round(x, 4), "band": band, "surfaces": [t["id"] for t in tails]}
        if band == "within":
            out.append(CheckResult(cid, PASS, f"{name} {x:.3f} within {lo}-{hi}", kcrit, data))
            continue
        msg = f"{name} {x:.3f} {band} {lo}-{hi}"
        if lo_t["source"] == "pending":
            out.append(CheckResult(cid, WARN, msg + f"; provisional: {kcrit} pending", kcrit, data))
        else:
            out.append(CheckResult(cid, FAIL, msg, kcrit, data))
    return out


@discipline_check("T3.trim", 3)
def trim(ctx, rep) -> list[CheckResult]:
    cid, crit = "T3.trim", f"{ST}#elevator_travel_up_deg"
    it = _na(ctx, cid, "elevator trim", crit)
    if it is not None:
        return [it]
    main, h, _v = main_and_tails(declared_surfaces(ctx.design))
    if main is None or not h:
        return [CheckResult(cid, SKIP, "no main wing or no horizontal tail among declared lifting_surface components",
                            crit, {"condition": "all"})]
    t = max(h, key=lambda s: s["area_mm2"])
    s_t = t["area_mm2"] / 1e6
    weight_n = ctx.mp["mass_g"] / 1000 * G
    x_cg = ctx.mp["cg_mm"][0]
    rho = ctx.design.data.get("flight", {}).get("air_density_kgm3", RHO_DEFAULT)
    eta = resolve_threshold("design-standards.yaml#aft_surface_efficiency")["value"]
    tau_t = resolve_threshold(f"{ST}#elevator_effectiveness_tau")
    tau = tau_t["value"]
    cm_t = resolve_threshold(f"{ST}#wing_cm_ac")
    cm_ac = cm_t["value"]
    up = resolve_threshold(f"{ST}#elevator_travel_up_deg")
    down = resolve_threshold(f"{ST}#elevator_travel_down_deg")
    pending = any(x["source"] == "pending" for x in (tau_t, cm_t, up, down))
    stall = next((r.data.get("stall_mps") for r in rep.results if r.check_id == "T3.stall"), None)
    cruise = (ctx.design.data.get("requirements") or {}).get("cruise_speed_mps")
    out = []
    for cond, v, why in (("cruise", cruise, "requirements.cruise_speed_mps missing"),
                         ("stall", stall, "T3.stall not available")):
        if not v:
            out.append(CheckResult(cid, SKIP, f"{cond}: {why}", crit, {"condition": cond}))
            continue
        q = 0.5 * rho * v ** 2
        l_t = trimcalc.trim_tail_lift_n(weight_n, 1, x_cg, main["x_ac_mm"], t["x_ac_mm"],
                                        cm_ac * (q * 1e-6) * main["area_mm2"] * main["mac_mm"])
        cl_t = trimcalc.tail_lift_coefficient(l_t, q, s_t)
        de = trimcalc.elevator_deflection_deg(cl_t, t["aspect_ratio"], eta, tau)
        limit = -up["value"] if de < 0 else down["value"]
        within = abs(de) <= abs(limit)
        msg = (f"{cond}: V {v:.1f} m/s, tail lift {l_t:.2f} N ({'down' if l_t < 0 else 'up'}), "
               f"elevator {de:+.1f} deg vs default travel {limit:+.0f} deg "
               f"(stick-fixed, tail at zero incidence, cm_ac {cm_ac}, tau {tau})")
        if pending and not within:
            msg += "; provisional: stability.yaml#elevator_travel_up_deg pending"
        data = {"condition": cond, "speed_mps": round(v, 2), "tail_lift_n": round(l_t, 3), "tail_cl": round(cl_t, 4),
                "elevator_deg": round(de, 2), "x_cg_mm": round(x_cg, 1), "tail": t["id"],
                "band": "within" if within else "above"}
        status = PASS if within else (WARN if pending else FAIL)
        out.append(CheckResult(cid, status, msg, crit, data))
    return out
