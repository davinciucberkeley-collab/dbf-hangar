"""U18.4: tail lift and elevator deflection to trim a wing-tail aircraft in level flight (stick-fixed, tail at zero incidence)."""
from __future__ import annotations

import math


def helmbold_slope(aspect_ratio: float) -> float:
    """Lift-curve slope per rad, Helmbold: 2 pi AR / (2 + sqrt(AR^2 + 4))."""
    return 2 * math.pi * aspect_ratio / (2 + math.sqrt(aspect_ratio ** 2 + 4))


def trim_tail_lift_n(weight_n: float, load_factor: float, x_cg_mm: float, x_wing_ac_mm: float,
                     x_tail_ac_mm: float, m_ac_nmm: float = 0.0) -> float:
    """Tail lift (N) that trims the aircraft; negative = tail down-force.

    Moments about the CG, nose-up positive, x aft:
    M_ac + L_w (x_cg - x_w) + L_t (x_cg - x_t) = 0 with L_w + L_t = n W.
    Substituting L_w = nW - L_t gives L_t = (M_ac + nW (x_cg - x_w)) / (x_t - x_w).
    """
    if x_tail_ac_mm == x_wing_ac_mm:
        raise ValueError("tail and wing aerodynamic centres coincide")
    return (m_ac_nmm + load_factor * weight_n * (x_cg_mm - x_wing_ac_mm)) / (x_tail_ac_mm - x_wing_ac_mm)


def tail_lift_coefficient(tail_lift_n: float, q_pa: float, tail_area_m2: float) -> float:
    return tail_lift_n / (q_pa * tail_area_m2)


def elevator_deflection_deg(cl_tail: float, tail_aspect_ratio: float, eta: float, tau: float) -> float:
    """Elevator deflection (deg) for a tail lift coefficient; negative = trailing edge up."""
    return math.degrees(cl_tail / (eta * helmbold_slope(tail_aspect_ratio) * tau))
