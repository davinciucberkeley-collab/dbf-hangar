"""Hinge geometry helpers for generated control surfaces (U16.1 S6): gap, bevel offsets and knuckle cylinders.

Plain numpy/trimesh; no registry import. Lengths mm, angles degrees, component-local frame.
"""
from __future__ import annotations

import math

import numpy as np
from .._lazy import trimesh

from hangar.geom import kernel
from hangar.geom.kernel import GeometryError


def sweep_factor(dx: float, dy: float) -> float:
    """1 / cos(L) of a hinge line running (dx, dy) in the section-normal plane; converts a normal gap to a section gap."""
    if dy == 0:
        raise GeometryError("sweep_factor: hinge line has no extent along the span (dy == 0)")
    return math.hypot(dx, dy) / abs(dy)


def front_offsets(gap: float, half_thickness: float, throw_deg: float, style: str,
                  k: float = 1.0) -> tuple[float | None, float]:
    """(ridge offset or None, front offset), mm behind the hinge line in the section."""
    if style == "bevel":
        return k * gap, k * (gap + half_thickness * math.tan(math.radians(throw_deg)))
    return None, k * gap


def aft_normal(p0, p1, up) -> np.ndarray:
    """Unit normal of the hinge plane (hinge line and `up`), pointing aft (x >= 0)."""
    n = np.cross(np.asarray(up, dtype=float), np.asarray(p1, dtype=float) - np.asarray(p0, dtype=float))
    n = n / np.linalg.norm(n)
    return -n if n[0] < 0 else n


def cylinder_between(p, q, radius: float, sections: int = 48) -> trimesh.Trimesh:
    p, q = np.asarray(p, dtype=float), np.asarray(q, dtype=float)
    d = q - p
    m = trimesh.creation.cylinder(radius=radius, height=float(np.linalg.norm(d)), sections=sections)
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d))
    m.apply_translation((p + q) / 2.0)
    return kernel.require_solid(m, "cylinder_between")


def knuckles(p0, p1, n, gap: float, count: int, diameter: float, length: float) -> list:
    p0, p1, n = (np.asarray(v, dtype=float) for v in (p0, p1, n))
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    out = []
    for i in range(count):
        c = p0 + (p1 - p0) * (i + 0.5) / count + n * gap
        out.append(cylinder_between(c - d * length / 2.0, c + d * length / 2.0, diameter / 2.0))
    return out
