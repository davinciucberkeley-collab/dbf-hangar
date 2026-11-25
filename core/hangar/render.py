"""Headless PNG views of a design (flat painter's-algorithm projection, matplotlib Agg)."""
from __future__ import annotations

import colorsys
import math
from pathlib import Path

import numpy as np

from .export import TYPE_HUES
from .geometry import component_parts, is_point_mass

VIEWS = ("top", "side", "front", "iso")


def _unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def _basis(view: str):
    if view == "top":
        return np.array([0.0, 1, 0]), np.array([-1.0, 0, 0])
    if view == "side":
        return np.array([1.0, 0, 0]), np.array([0.0, 0, 1])
    if view == "front":
        return np.array([0.0, -1, 0]), np.array([0.0, 0, 1])
    if view == "iso":
        t = _unit([-1, -1, 1])
        right = _unit(np.cross([0, 0, 1], t))
        return right, np.cross(t, right)
    raise ValueError("view must be one of top, side, front, iso")


def render_png(design, out, *, view: str = "iso", size: int = 900, max_faces: int = 60000) -> Path:
    right, up = _basis(view)
    try:
        import matplotlib
    except ImportError as e:
        raise RuntimeError("design render needs matplotlib: pip install matplotlib (or pip install -e .[render])") from e
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.collections import PolyCollection
    from matplotlib.figure import Figure

    t = np.cross(right, up)
    light = _unit(t + 0.5 * right + 0.5 * up)
    parts = []  # (triangles (n,3,3), rgb)
    for c in design.components:
        if is_point_mass(c):
            continue
        rgb = np.array(colorsys.hsv_to_rgb(TYPE_HUES.get(c["type"], 0.9), 0.45, 0.85))
        for m in component_parts(c, design.base_dir):
            parts.append((np.asarray(m.triangles, dtype=float), rgb))
    total = sum(len(tri) for tri, _ in parts)
    k = max(1, math.ceil(total / max_faces))
    tris, cols = [], []
    for tri, rgb in parts:
        tri = tri[::k]
        if not len(tri):
            continue
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        ln = np.linalg.norm(n, axis=1)
        n = n / np.where(ln > 0, ln, 1)[:, None]
        shade = 0.35 + 0.65 * np.abs(n @ light)
        tris.append(tri)
        cols.append(rgb[None, :] * shade[:, None])
    fig = Figure(figsize=(size / 100, size / 100), dpi=100, facecolor="white")
    FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    if tris:
        tri = np.concatenate(tris)
        col = np.concatenate(cols)
        order = np.argsort(tri.mean(axis=1) @ t, kind="stable")
        tri, col = tri[order], col[order]
        proj = np.stack([tri @ right, tri @ up], axis=-1)
        ax.add_collection(PolyCollection(proj, facecolors=col, linewidths=0, antialiaseds=False))
        lo, hi = proj.reshape(-1, 2).min(axis=0), proj.reshape(-1, 2).max(axis=0)
        pad = 0.05 * float(max(hi - lo))
        ax.set_xlim(lo[0] - pad, hi[0] + pad)
        ax.set_ylim(lo[1] - pad, hi[1] + pad)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(0.01, 0.01, f"{design.id}  {view}  mm", fontsize=9, ha="left", va="bottom")
    out = Path(out)
    fig.savefig(out, dpi=100, metadata={"Software": None})
    return out
