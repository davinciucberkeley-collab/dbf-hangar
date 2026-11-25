"""U18.3: wing spar bending by beam theory (T3.spar_bending, report-only); thresholds in standards/spar.yaml.

Assumptions: the spar alone carries the bending (skin and foam core give no stiffness); lift is n x weight with no
inertial relief from wing mass (conservative); the moment is taken at the centre line (spar continuous through the
fuselage); the spar section is constant along its length.
"""
from __future__ import annotations

import hangar.geom  # noqa: F401  (registers the generators)
from hangar.geom.registry import fill_defaults, get

from ..calcs import spar as beam
from ..checks import G
from ..design import FAIL, PASS, SKIP, CheckResult
from . import discipline_check
from .applicability import NEEDS, skip_row
from .fidelity import resolve_threshold

SP = "spar.yaml"
CID = "T3.spar_bending"
CRIT = f"{SP}#spar_reserve_factor_min"


def _main_wing(components: list[dict]) -> tuple[float, float, float] | None:
    """(span, root_chord, tip_chord) of the largest mirrored lifting wing (by planform area), or None."""
    cands = []
    for c in components:
        g = c.get("geometry") or {}
        ls = g.get("lifting_surface")
        if ls and ls.get("lifting", True) and ls.get("mirrored", True):
            cands.append((ls["span"], ls["root_chord"], ls["tip_chord"]))
        if g.get("generator") == "wing_panel":
            p = fill_defaults(get("wing_panel"), g.get("params") or {})
            if p["side"] == "both" and p["part"] in ("full", "core"):
                cands.append((p["span"], p["root_chord"], p["tip_chord"]))
    if not cands:
        return None
    return max(cands, key=lambda t: t[0] * (t[1] + t[2]) / 2)


def _spar(components: list[dict], span: float) -> dict | None:
    """The longest tube spar along y, at least half the wing span long, or None."""
    best = None
    for c in components:
        g = c.get("geometry") or {}
        p = g.get("params") or {}
        if (c.get("type") == "structure" and g.get("generator") == "tube" and p.get("axis") == "y"
                and p.get("length", 0) >= 0.5 * span):
            if best is None or p["length"] > best["geometry"]["params"]["length"]:
                best = c
    return best


@discipline_check(CID, 3)
def spar_bending(ctx, rep) -> list[CheckResult]:
    m = ctx.design.data["morphology"]
    if not NEEDS["winged"](m):
        return [skip_row(CID, f"not applicable: spar bending is for winged designs "
                              f"(morphology lift={m['lift']}, vtol_method={m.get('vtol_method', 'none')})", CRIT)]
    components = ctx.design.data.get("components", [])
    main = _main_wing(components)
    if main is None:
        return [CheckResult(CID, SKIP, "no main wing found (needs a lifting_surface or a wing_panel generator)", CRIT)]
    span, root_c, tip_c = main
    spar = _spar(components, span)
    if spar is None:
        return [CheckResult(CID, SKIP, "no spar tube found (needs a type structure component with generator tube, "
                                       "axis y, length at least half the wing span)", CRIT)]
    sp_id = spar["id"]
    p = spar["geometry"]["params"]

    weight_n = ctx.mp["mass_g"] / 1000 * G
    n_lim = resolve_threshold(f"{SP}#spar_limit_load_factor")["value"]
    ult = resolve_threshold("design-standards.yaml#ultimate_factor")["value"]
    load_n = n_lim * weight_n
    loads = {d: beam.spanwise_load(span, root_c, tip_c, load_n, d) for d in ("elliptic", "schrenk")}
    moments = {d: beam.root_moment_nmm(y, dy, w) for d, (y, dy, w) in loads.items()}
    dist = max(moments, key=moments.get)
    M = moments[dist]
    y, dy, w = loads[dist]

    I, c = beam.tube_section(p["outer_d"], p["inner_d"])
    sigma = M * c / I
    sigma_ult = sigma * ult

    mm = spar.get("mass_model")
    mat = mm["material"] if isinstance(mm, dict) and "material" in mm else spar.get("material")
    allow = resolve_threshold(f"{SP}#spar_material_allowable_mpa")["value"].get(mat)
    E = resolve_threshold(f"{SP}#spar_material_modulus_mpa")["value"].get(mat)

    data = {"component": sp_id, "root_moment_nmm": round(M, 1), "stress_limit_mpa": round(sigma, 2),
            "stress_ultimate_mpa": round(sigma_ult, 2), "distribution": dist, "load_factor": n_lim,
            "material": str(mat)}
    defl = frac = None
    if E is not None:
        defl = beam.tip_deflection_mm(y, dy, w, span, E * I)
        frac = defl / (span / 2)
        data["tip_deflection_mm"] = round(defl, 2)
        data["tip_deflection_fraction_semispan"] = round(frac, 4)
    base = f"spar {sp_id}: root bending moment {M / 1000:.2f} N*m (n={n_lim}, {dist}), "

    if allow is None:
        msg = (base + f"stress {sigma:.1f} MPa at limit, {sigma_ult:.1f} MPa at ultimate; "
                      f"not judged: no sourced allowable for material '{mat}' in spar.yaml")
        return [CheckResult(CID, SKIP, msg, CRIT, data)]

    rf = allow / sigma_ult
    rf_min = resolve_threshold(f"{SP}#spar_reserve_factor_min")["value"]
    data.update({"reserve_factor": round(rf, 3), "allowable_mpa": allow,
                 "band": "within" if rf >= rf_min else "below"})
    msg = (base + f"stress {sigma:.1f} MPa x {ult} = {sigma_ult:.1f} vs allowable {allow} MPa, "
                  f"reserve factor {rf:.2f} vs min {rf_min}")
    if E is not None:
        msg += f"; tip deflection {defl:.1f} mm ({frac:.1%} of semi-span)"
    return [CheckResult(CID, PASS if rf >= rf_min else FAIL, msg, CRIT, data)]
