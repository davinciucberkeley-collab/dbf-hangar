"""U18.3: spanwise lift, root bending moment and tip deflection of a cantilever wing spar (beam theory)."""
from __future__ import annotations

import math


def spanwise_load(span_mm: float, root_chord_mm: float, tip_chord_mm: float, total_load_n: float,
                  distribution: str, n: int = 400) -> tuple[list[float], float, list[float]]:
    """Stations y_i on one half wing, the step dy and the lift per unit span w_i (N/mm) for a lift distribution."""
    s = span_mm / 2
    dy = s / n
    ys = [(i + 0.5) * dy for i in range(n)]
    S = span_mm * (root_chord_mm + tip_chord_mm) / 2
    L = total_load_n

    def chord(y: float) -> float:
        return root_chord_mm - (root_chord_mm - tip_chord_mm) * y / s

    def elliptic(y: float) -> float:
        return 4 * L / (math.pi * span_mm) * math.sqrt(1 - (y / s) ** 2)

    if distribution == "elliptic":
        ws = [elliptic(y) for y in ys]
    elif distribution == "schrenk":
        ws = [0.5 * (L * chord(y) / S + elliptic(y)) for y in ys]
    else:
        raise ValueError(f"unknown distribution {distribution!r}")
    return ys, dy, ws


def root_moment_nmm(y: list[float], dy: float, w: list[float]) -> float:
    """Root bending moment (N*mm) of the lift distribution w about the centre line."""
    return sum(wi * yi * dy for yi, wi in zip(y, w))


def tip_deflection_mm(y: list[float], dy: float, w: list[float], span_mm: float, ei_nmm2: float) -> float:
    """Tip deflection (mm) of a cantilever spar of bending stiffness ei_nmm2 under lift w (unit-load integral)."""
    s = span_mm / 2
    return sum(wi * dy * (yi ** 2 * s / 2 - yi ** 3 / 6) for yi, wi in zip(y, w)) / ei_nmm2


def tube_section(outer_d_mm: float, inner_d_mm: float) -> tuple[float, float]:
    """Second moment of area I (mm^4) and outer fibre distance c (mm) of a circular tube."""
    return math.pi / 64 * (outer_d_mm ** 4 - inner_d_mm ** 4), outer_d_mm / 2
