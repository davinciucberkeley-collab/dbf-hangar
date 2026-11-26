"""U18.4-3: dynamic modes (short period, phugoid, Dutch roll, spiral) from the AeroSandbox vortex lattice; report-only."""
from __future__ import annotations

import importlib.util

import numpy as np

from ..calcs import modes
from ..checks import RHO_DEFAULT
from ..design import FAIL, PASS, SKIP, WARN, CheckResult
from . import discipline_check
from .applicability import NEEDS, skip_row
from .fidelity import resolve_threshold
from .stability import ST, declared_surfaces, main_and_tails

CID = "T3.dynamic_modes"
NOTE = "AeroSandbox VLM, NACA 0012 sections, alpha 2 deg, Ixz neglected"


def _row(mode, msg, key, ok, w, z, ttd=None):
    crit = f"{ST}#{key}"
    data = {"mode": mode, "omega_rad_s": None if w is None else round(w, 3),
            "zeta": None if z is None else round(z, 4),
            "time_to_double_s": None if ttd is None else round(ttd, 2), "band": "within" if ok else "below"}
    if ok:
        return CheckResult(CID, PASS, msg, crit, data)
    if resolve_threshold(crit)["source"] == "pending":
        return CheckResult(CID, WARN, msg + f"; provisional: {crit} pending", crit, data)
    return CheckResult(CID, FAIL, msg, crit, data)


def _val(key):
    return resolve_threshold(f"{ST}#{key}")["value"]


@discipline_check(CID, 3)
def dynamic_modes(ctx, rep) -> list[CheckResult]:
    crit = f"{ST}#short_period_damping_min"
    design = ctx.design
    m = design.data["morphology"]
    if not NEEDS["winged"](m):
        return [skip_row(CID, f"not applicable: dynamic modes are for winged designs (morphology lift={m['lift']}, "
                              f"vtol_method={m.get('vtol_method', 'none')})", crit)]
    if importlib.util.find_spec("aerosandbox") is None:
        return [CheckResult(CID, SKIP, "aerosandbox not installed; run: python -m pip install aerosandbox "
                            "(dynamic modes not computed)", crit, {"tool": "aerosandbox"})]
    main, h, v = main_and_tails(declared_surfaces(design))
    if main is None:
        return [CheckResult(CID, SKIP, "no main wing found among declared lifting_surface components", crit)]
    speed = (design.data.get("requirements") or {}).get("cruise_speed_mps")
    if not speed:
        return [CheckResult(CID, SKIP, "requirements.cruise_speed_mps missing", crit)]
    flight = design.data.get("flight") or {}
    comp = {c["id"]: c for c in design.data["components"]}
    surf = {"main": comp[main["id"]], "h": comp[h[0]["id"]] if h else None, "v": comp[v[0]["id"]] if v else None}
    rho = flight.get("air_density_kgm3") or RHO_DEFAULT
    try:
        from ..calcs.asb_derivatives import stability_derivatives
        d = stability_derivatives(surf, [x / 1000 for x in ctx.mp["cg_mm"]], speed, rho)
    except Exception as e:  # noqa: BLE001  (a tool failure is a SKIP, never a crash)
        return [CheckResult(CID, SKIP, f"aerosandbox failed: {type(e).__name__}: {e}", crit, {"tool": "aerosandbox"})]
    mass = ctx.mp["mass_g"] / 1000
    inertia = np.array(ctx.mp["inertia_gmm2"]) * 1e-9
    ix, iy, iz = inertia[0][0], inertia[1][1], inertia[2][2]
    q = 0.5 * rho * speed ** 2
    s, c, b = main["area_mm2"] / 1e6, main["mac_mm"] / 1000, main["span_mm"] / 1000
    z_a = -d["CLa"] * q * s / (mass * speed)
    m_a = d["Cma"] * q * s * c / iy
    m_q = d["Cmq"] * q * s * c ** 2 / (2 * speed * iy)
    y_b = d["CYb"] * q * s / (mass * speed)
    l_b = d["Clb"] * q * s * b / ix
    l_p = d["Clp"] * q * s * b ** 2 / (2 * speed * ix)
    l_r = d["Clr"] * q * s * b ** 2 / (2 * speed * ix)
    n_b = d["Cnb"] * q * s * b / iz
    n_p = d["Cnp"] * q * s * b ** 2 / (2 * speed * iz)
    n_r = d["Cnr"] * q * s * b ** 2 / (2 * speed * iz)
    out = []

    try:
        w, z = modes.short_period(m_a, m_q, z_a)
        zmin = _val("short_period_damping_min")
        out.append(_row("short_period", f"short period: omega {w:.2f} rad/s, damping {z:.2f} vs min {zmin} ({NOTE})",
                        "short_period_damping_min", z >= zmin, w, z))
    except ValueError as e:
        out.append(CheckResult(CID, WARN, str(e), crit, {"mode": "short_period", "band": "below"}))

    pcrit = f"{ST}#phugoid_damping_min"
    ld = flight.get("cruise_ld")
    if not ld:
        out.append(CheckResult(CID, SKIP, "flight.cruise_ld missing: phugoid not computed", pcrit, {"mode": "phugoid"}))
    else:
        w, z = modes.phugoid_lanchester(speed, ld)
        pmin = _val("phugoid_damping_min")
        out.append(_row("phugoid", f"phugoid (Lanchester): omega {w:.2f} rad/s, damping {z:.3f} vs min {pmin}",
                        "phugoid_damping_min", z >= pmin, w, z))

    lat = modes.lateral_modes(modes.lateral_matrix(y_b, l_b, l_p, l_r, n_b, n_p, n_r, speed))
    dr = lat["dutch_roll"]
    if dr is None:
        out.append(CheckResult(CID, WARN, "no oscillatory Dutch-roll mode", f"{ST}#dutch_roll_damping_min",
                               {"mode": "dutch_roll", "omega_rad_s": None, "zeta": None, "time_to_double_s": None,
                                "band": "below"}))
    else:
        dmin = _val("dutch_roll_damping_min")
        out.append(_row("dutch_roll", f"Dutch roll: omega {dr['omega']:.2f} rad/s, damping {dr['zeta']:.2f} vs min "
                        f"{dmin} ({NOTE})", "dutch_roll_damping_min", dr["zeta"] >= dmin, dr["omega"], dr["zeta"]))
    ttd = lat["spiral_time_to_double_s"]
    scrit = f"{ST}#spiral_time_to_double_min_s"
    if ttd is None:
        out.append(CheckResult(CID, PASS, "spiral stable", scrit,
                               {"mode": "spiral", "omega_rad_s": None, "zeta": None, "time_to_double_s": None,
                                "band": "within"}))
    else:
        smin = _val("spiral_time_to_double_min_s")
        out.append(_row("spiral", f"spiral: unstable, time to double {ttd:.1f} s vs min {smin} s ({NOTE})",
                        "spiral_time_to_double_min_s", ttd >= smin, None, None, ttd))
    return out
