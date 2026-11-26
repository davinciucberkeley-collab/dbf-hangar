"""U18.4: stability derivatives of a declared airframe from the AeroSandbox vortex lattice (opt-in tool, imported lazily)."""
from __future__ import annotations

import math

KEYS = ("CLa", "Cma", "Cmq", "CYb", "Clb", "Cnb", "Clp", "Clr", "Cnp", "Cnr")


def stability_derivatives(surfaces: dict, cg_m: list[float], speed_mps: float, rho: float,
                          alpha_deg: float = 2.0) -> dict:
    """Ten non-dimensional derivatives per radian from AeroSandbox VortexLatticeMethod.

    `surfaces` is {"main": c, "h": c or None, "v": c or None}, each c a PDL component dict with
    geometry.lifting_surface (mm). Every surface gets a symmetric NACA 0012 section (PDL carries only an airfoil name).
    `rho` is accepted for the caller's dimensional conversion and is not passed on: AeroSandbox uses its sea-level
    atmosphere. Raises KeyError listing any derivative the installed AeroSandbox result lacks.
    """
    import aerosandbox as asb
    import numpy as np

    from ..geometry import lifting_surface_properties, rotation_matrix

    def wing(name: str, c: dict):
        ls = c["geometry"]["lifting_surface"]
        mirrored = ls.get("mirrored", True)
        half = (ls["span"] / 2 if mirrored else ls["span"]) / 1000
        sweep = math.tan(math.radians(ls.get("sweep_le_deg", 0))) * half
        y = rotation_matrix(c.get("rotation_deg")) @ np.array([0.0, 1.0, 0.0])
        if abs(y[2]) > abs(y[1]):
            tip = [sweep, 0.0, half]
        else:
            tip = [sweep, half, math.tan(math.radians(ls.get("dihedral_deg", 0))) * half]
        foil = asb.Airfoil("naca0012")
        return asb.Wing(name=name, symmetric=mirrored, xyz_le=[p / 1000 for p in c["position"]],
                        xsecs=[asb.WingXSec(xyz_le=[0, 0, 0], chord=ls["root_chord"] / 1000, airfoil=foil),
                               asb.WingXSec(xyz_le=tip, chord=ls["tip_chord"] / 1000, airfoil=foil)])

    main = surfaces["main"]
    p = lifting_surface_properties(main)
    wings = [wing(n, c) for n, c in (("main", main), ("h", surfaces.get("h")), ("v", surfaces.get("v")))
             if c is not None]
    airplane = asb.Airplane(name="declared", wings=wings, s_ref=p["area_mm2"] / 1e6, c_ref=p["mac_mm"] / 1000,
                            b_ref=main["geometry"]["lifting_surface"]["span"] / 1000, xyz_ref=list(cg_m))
    op = asb.OperatingPoint(velocity=speed_mps, alpha=alpha_deg, atmosphere=asb.Atmosphere(altitude=0))
    res = asb.VortexLatticeMethod(airplane=airplane, op_point=op, spanwise_resolution=6,
                                  chordwise_resolution=4).run_with_stability_derivatives()
    missing = [k for k in KEYS if k not in res]
    if missing:
        raise KeyError(f"AeroSandbox result lacks: {', '.join(missing)}")
    return {k: float(res[k]) for k in KEYS}
