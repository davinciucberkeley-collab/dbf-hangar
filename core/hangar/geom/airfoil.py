"""Named airfoil references: generated NACA 4-digit sections and files in knowledge/airfoils/ (U4.36)."""
from __future__ import annotations

import math
import re
from pathlib import Path

from hangar.design import REPO_ROOT
from hangar.geom.kernel import GeometryError

AIRFOIL_DIR = REPO_ROOT / "knowledge" / "airfoils"
_NACA = re.compile(r"^naca[0-9]{4}$")


def is_named(ref: str) -> bool:
    return not any(c in ref for c in "./\\")


def naca4_rows(code: str, n: int = 60) -> list[tuple[float, float]]:
    """NACA 4-digit section, Selig order (upper TE -> LE, then lower), 2n+1 rows, open trailing edge."""
    if not re.fullmatch(r"[0-9]{4}", str(code)):
        raise GeometryError(f"NACA 4-digit code must be 4 digits, got {code!r}")
    m, p, t = int(code[0]) / 100, int(code[1]) / 10, int(code[2:]) / 100
    up, lo = [], []
    for i in range(n + 1):
        b = (1 - math.cos(math.pi * i / n)) / 2
        yt = 5 * t * (0.2969 * math.sqrt(b) - 0.1260 * b - 0.3516 * b ** 2 + 0.2843 * b ** 3 - 0.1015 * b ** 4)
        if m == 0 or p == 0:
            yc = th = 0.0
        elif b < p:
            yc = m / p ** 2 * (2 * p * b - b * b)
            th = math.atan(2 * m / p ** 2 * (p - b))
        else:
            yc = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * b - b * b)
            th = math.atan(2 * m / (1 - p) ** 2 * (p - b))
        up.append((b - yt * math.sin(th), yc + yt * math.cos(th)))
        lo.append((b + yt * math.sin(th), yc - yt * math.cos(th)))
    rows = up[::-1] + lo[1:]
    return [(round(x, 7), round(y, 7)) for x, y in rows]   # 7 decimals, as a written .dat, so name == file exactly


def resolve(ref: str):
    name = ref.lower()
    if _NACA.match(name):
        return "rows", naca4_rows(name[4:])
    path = AIRFOIL_DIR / f"{ref}.dat"
    if path.is_file():
        return "path", path
    known = sorted(p.stem for p in AIRFOIL_DIR.glob("*.dat")) if AIRFOIL_DIR.is_dir() else []
    raise GeometryError(f"airfoil {ref!r}: not a NACA 4-digit name and no knowledge/airfoils/{ref}.dat "
                        f"(known: {', '.join(known + ['nacaXXXX'])})")
