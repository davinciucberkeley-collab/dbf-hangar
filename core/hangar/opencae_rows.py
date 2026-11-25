"""Tier-2 rows from results OpenCAE wrote earlier (designs/<id>/opencae/results.json). Never runs OpenCAE."""
from __future__ import annotations

from . import opencae_cli
from .design import FAIL, PASS, SKIP, CheckResult
from .gates.discipline import OPS, _crit, _entry, _judge, _skip
from .geom import overlay
from .geometry import is_point_mass
from .mass import mass_properties

OPENCAE_ROW_IDS = ("T2.opencae_hover_tw", "T2.opencae_current_margin", "T2.opencae_endurance", "T2.opencae_structure_sf",
                   "T2.opencae_cfd_ld", "T2.opencae_flight", "T2.opencae_mass_cross", "T2.opencae")
CRIT = "opencae_cli"
_MARGINS = (("motor_current_margin", "motor"), ("esc_current_margin", "ESC"), ("battery_current_margin", "battery"))


def _hover_design(design) -> bool:
    m = design.data["morphology"]
    return m.get("lift") == "multirotor" or m.get("vtol_method", "none") != "none"


def tier2_opencae(design) -> list[CheckResult]:
    """Rows from designs/<id>/opencae/results.json. Never runs anything."""
    with overlay.forced_off():
        return _rows(design)


def _rows(design) -> list[CheckResult]:
    rec = opencae_cli.load_result(design)
    sidecar = (design.base_dir / "opencae-inputs.yaml").is_file()
    if rec is None:
        if not sidecar:
            return []
        return [_skip("T2.opencae", "no stored OpenCAE results; run: plane opencae run "
                      f"{design.id} --analyses mass,propulsion", CRIT)]
    if rec["design_hash"] != opencae_cli.design_fingerprint(design, tuple(rec["analyses"])):
        return [_skip("T2.opencae", "stored OpenCAE results are out of date (design or standards changed); run: "
                      f"plane opencae run {design.id} --analyses {','.join(rec['analyses'])}", CRIT)]
    an = rec["result"]["analyses"]
    head = rec["opencae_head"]
    hover = _hover_design(design)
    out: list[CheckResult] = []

    def get(name):
        """Metrics of analysis `name`; None when absent, or after appending its SKIP / FAIL row."""
        if name not in an:
            return None
        a = an[name]
        if a["status"] == "not_evaluated":
            out.append(_skip(f"T2.opencae_{name}", f"OpenCAE {name} not evaluated: missing {', '.join(a['missing'])}",
                             CRIT, {"opencae_head": head}))
            return None
        if a["status"] == "error":
            out.append(CheckResult(f"T2.opencae_{name}", FAIL, f"OpenCAE {name} failed: {a['summary']}", CRIT,
                                   {"opencae_head": head}))
            return None
        return a["metrics"]

    def emit(cid, ok, msg, m, key, crit, pending=False):
        """One row; a pending limit gives SKIP with would_be. The message always ends with the basis."""
        basis = m[key]["basis"]
        res = _judge(cid, PASS if ok else FAIL, msg, crit, pending, {"basis": basis, "opencae_head": head},
                     "standards/" + crit)
        res.message += f"; OpenCAE basis {basis}"
        out.append(res)

    def val(m, key):
        return m[key]["value"]

    p = get("propulsion")
    if p is not None:
        if hover:
            lim = _entry("design-standards.yaml", "hover_thrust_to_weight_min")["value"]
            tw = val(p, "tw_ratio")
            emit("T2.opencae_hover_tw", tw >= lim,
                 f"OpenCAE hover T/W {tw:.2f} (thrust {val(p, 'thrust_total_max_n'):.1f} N total, static; minimum {lim})",
                 p, "tw_ratio", "design-standards.yaml#hover_thrust_to_weight_min")
        lim, pend = _crit(OPS, "electrical_rating_min_ratio")
        for key, label in _MARGINS:
            v = val(p, key)
            emit("T2.opencae_current_margin", v >= lim,
                 f"OpenCAE {label} current margin {v:.2f} (rating over full-throttle current; minimum {lim})",
                 p, key, "operations.yaml#electrical_rating_min_ratio", pend)
        if hover:
            t = _crit(OPS, "mission_hover_min")[0]
            reserve = _crit(OPS, "energy_reserve_fraction")[0]
            need = t * (1 + reserve)
            v = val(p, "hover_endurance_min")
            emit("T2.opencae_endurance", v >= need,
                 f"OpenCAE hover time {v:.1f} min vs need {need:.1f} min (mission {t} min + {reserve:.0%} reserve)",
                 p, "hover_endurance_min", "operations.yaml#mission_hover_min")
    s = get("structure")
    if s is not None:
        lim, pend = _crit(OPS, "opencae_structure_sf_min")
        sf = val(s, "safety_factor")
        emit("T2.opencae_structure_sf", sf >= lim,
             f"OpenCAE structure safety factor {sf:.2f} (peak {val(s, 'max_stress_mpa'):.1f} MPa, "
             f"{val(s, 'max_disp_mm'):.2f} mm; minimum {lim})", s, "safety_factor",
             "operations.yaml#opencae_structure_sf_min", pend)
    c = get("cfd")
    if c is not None:
        declared = (design.data.get("flight") or {}).get("cruise_ld")
        if declared is None:
            out.append(_skip("T2.opencae_cfd_ld", "flight.cruise_ld missing: nothing to compare the computed L/D with",
                             "standards/operations.yaml#opencae_cfd_ld_tolerance_fraction",
                             {"basis": c["ld"]["basis"], "opencae_head": head}))
        else:
            lim, pend = _crit(OPS, "opencae_cfd_ld_tolerance_fraction")
            ld = val(c, "ld")
            err = abs(ld - declared) / declared
            emit("T2.opencae_cfd_ld", err <= lim,
                 f"OpenCAE L/D {ld:.2f} vs declared {declared:.2f} (difference {err:.0%}; tolerance {lim:.0%}); "
                 f"converged {bool(val(c, 'converged'))}; SU2 drag is indicative only",
                 c, "ld", "operations.yaml#opencae_cfd_ld_tolerance_fraction", pend)
    f = get("flight")
    if f is not None and hover:
        lim, pend = _crit(OPS, "opencae_flight_max_tilt_deg_max")
        tilt = val(f, "max_tilt_deg")
        emit("T2.opencae_flight", tilt <= lim,
             f"OpenCAE hover recovery: peak tilt {tilt:.1f} deg, settled in {val(f, 'settle_time_s'):.1f} s, "
             f"drift {val(f, 'position_error_m') * 100:.0f} cm, throttle margin {val(f, 'throttle_margin'):.2f}; "
             f"maximum tilt {lim} deg", f, "max_tilt_deg", "operations.yaml#opencae_flight_max_tilt_deg_max", pend)
    ms = get("mass")
    if ms is not None:
        lim, pend = _crit(OPS, "opencae_mass_cross_tolerance_g")
        # point masses are not in OpenCAE's mass.parts: add them back before comparing totals
        point_g = sum(float(c["mass_g"]) for c in design.components if is_point_mass(c))
        a = val(ms, "mass_kg") * 1000 + point_g
        b = mass_properties(design)["mass_g"]
        d = abs(a - b)
        extra = f" (includes {point_g:.1f} g of point masses not in OpenCAE)" if point_g else ""
        emit("T2.opencae_mass_cross", d <= lim,
             f"OpenCAE mass {a:.1f} g{extra} vs plane {b:.1f} g (difference {d:.1f} g; tolerance {lim} g)",
             ms, "mass_kg", "operations.yaml#opencae_mass_cross_tolerance_g", pend)
    return out
