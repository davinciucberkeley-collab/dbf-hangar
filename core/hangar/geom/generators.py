"""Registered geometry generators (U9.1: tube, mesh_file; U9.2 adds the aircraft ones)."""
from __future__ import annotations

from .._lazy import trimesh

from hangar.geom import kernel
from hangar.geom.registry import Generator, ParamSpec, register


def _tube_build(p: dict, base_dir) -> list:
    return [kernel.tube(p["axis"], p["center"], p["length"], p["outer_d"], p["inner_d"])]


def _tube_check(p: dict) -> list[str]:
    return [] if p["inner_d"] < p["outer_d"] else ["inner_d must be less than outer_d"]


register(Generator(
    "tube",
    {"axis": ParamSpec("choice", required=True, choices=("x", "y", "z"), doc="tube axis"),
     "center": ParamSpec("vec3", default=[0.0, 0.0, 0.0], doc="centre, mm"),
     "length": ParamSpec("number", required=True, exclusive_minimum=0, doc="length along the axis, mm"),
     "outer_d": ParamSpec("number", required=True, exclusive_minimum=0, doc="outer diameter, mm"),
     "inner_d": ParamSpec("number", default=0.0, minimum=0, doc="bore diameter, mm (0 = solid)")},
    _tube_build, check=_tube_check))


def _mesh_file_build(p: dict, base_dir) -> list:
    try:
        m = trimesh.load(base_dir / p["file"], force="mesh")
    except Exception as e:
        raise kernel.GeometryError(f"cannot load {p['file']}: {e}") from e
    return [kernel.require_solid(m, p["file"])]


register(Generator(
    "mesh_file",
    {"file": ParamSpec("string", required=True, doc="design-folder-relative mesh file")},
    _mesh_file_build, files=lambda p: [p["file"]]))
