"""U18.4: handbook approximations of the longitudinal and lateral modes from dimensional derivatives (2-state models, Lanchester phugoid, 4-state lateral matrix)."""
from __future__ import annotations

import math

import numpy as np


def _pair(a: float, c: float, err: str) -> tuple[float, float]:
    # lambda^2 + a lambda + c with a = -(trace); returns (omega_n, zeta)
    if c <= 0:
        raise ValueError(err)
    w = math.sqrt(c)
    return w, a / (2 * w)


def short_period(m_alpha: float, m_q: float, z_alpha: float) -> tuple[float, float]:
    """(omega_n rad/s, zeta) of alpha_dot = q + z_alpha alpha, q_dot = m_alpha alpha + m_q q."""
    return _pair(-(z_alpha + m_q), z_alpha * m_q - m_alpha,
                 "statically unstable pitch: no oscillatory short-period mode")


def dutch_roll(y_beta: float, n_r: float, n_beta: float) -> tuple[float, float]:
    """(omega_n rad/s, zeta) of beta_dot = y_beta beta - r, r_dot = n_beta beta + n_r r."""
    return _pair(-(y_beta + n_r), y_beta * n_r + n_beta, "no oscillatory Dutch-roll mode")


def phugoid_lanchester(speed_mps: float, lift_over_drag: float, g: float = 9.80665) -> tuple[float, float]:
    return math.sqrt(2) * g / speed_mps, 1 / (math.sqrt(2) * lift_over_drag)


def lateral_modes(a: list[list[float]]) -> dict:
    """Dutch roll, roll subsidence and spiral from the 4x4 matrix for states (beta, p, r, phi)."""
    ev = list(np.linalg.eigvals(np.array(a, dtype=float)))
    cplx = [e for e in ev if abs(e.imag) > 1e-9]
    dr = None
    if cplx:
        e = cplx[0]
        w = abs(e)
        dr = {"omega": float(w), "zeta": float(-e.real / w)}
    real = sorted(float(e.real) for e in ev if abs(e.imag) <= 1e-9)
    roll_tau = None
    if real and real[0] < 0:
        roll_tau = -1 / real[0]
        real = real[1:]
    spiral = min(real, key=abs) if real else None
    ttd = math.log(2) / spiral if spiral is not None and spiral > 0 else None
    return {"dutch_roll": dr, "roll_tau_s": roll_tau, "spiral_lambda": spiral, "spiral_time_to_double_s": ttd}


def lateral_matrix(y_beta, l_beta, l_p, l_r, n_beta, n_p, n_r, speed_mps, g=9.80665) -> list[list[float]]:
    """States (beta, p, r, phi); sideforce due to p and r and Ixz neglected."""
    return [[y_beta, 0, -1, g / speed_mps], [l_beta, l_p, l_r, 0], [n_beta, n_p, n_r, 0], [0, 1, 0, 0]]
