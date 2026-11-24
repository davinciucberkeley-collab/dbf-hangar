"""Material densities and the mass model: mass = volume x density + extra_g."""
from __future__ import annotations

import functools
from pathlib import Path

import yaml

_FILE = Path(__file__).resolve().parents[3] / "standards" / "materials.yaml"


@functools.lru_cache(maxsize=1)
def _standard() -> dict:
    data = yaml.safe_load(_FILE.read_text(encoding="utf-8")) or {}
    return dict((data.get("material_density_g_cm3") or {}).get("value") or {})


def density_g_cm3(material: str, design_materials: dict | None = None) -> float:
    dm = design_materials or {}
    if material in dm and isinstance(dm[material], dict) and "density_g_cm3" in dm[material]:
        return float(dm[material]["density_g_cm3"])
    std = _standard()
    if material in std:
        return float(std[material])
    known = sorted(set(std) | {k for k, v in dm.items() if isinstance(v, dict) and "density_g_cm3" in v})
    raise KeyError(f"unknown material {material!r}; known: {', '.join(known)}")


def mass_g(volume_mm3: float, density_g_cm3: float, extra_g: float = 0.0) -> float:
    return volume_mm3 / 1000.0 * density_g_cm3 + extra_g
