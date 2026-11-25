"""U18.2: compare a computed number with a published one against a tolerance from standards/calibration.yaml."""
from __future__ import annotations

from .gates.fidelity import resolve_threshold

KEYS = ("calibration_tol_mass_fraction", "calibration_tol_geometry_fraction", "calibration_tol_stall_fraction")


def error_fraction(computed: float, published: float) -> float:
    if published == 0:
        raise ValueError("published value is zero")
    return (computed - published) / published


def tolerance(key: str) -> tuple[float, bool]:
    t = resolve_threshold(f"calibration.yaml#{key}")
    if t is None:
        raise KeyError(key)
    return t["value"], t["source"] == "pending"


def within(computed: float, published: float, key: str) -> bool:
    return abs(error_fraction(computed, published)) <= tolerance(key)[0]
