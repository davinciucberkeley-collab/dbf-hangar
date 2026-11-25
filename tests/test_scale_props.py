"""U13.8-5: generator-built scale propeller library parts (geometry = propeller generator)."""
import math

import numpy as np
import pytest

from hangar.geom import library, registry
from hangar.ops import call

PROP_2B = "scale-prop-2b-191"
PROP_8B = "scale-prop-8b-a400m"
PETG_G_PER_MM3 = 0.00127


def _ids():
    return [pid for pid in (PROP_2B, PROP_8B) if pid in library.list_parts()]


def _built(pid):
    part = library.load_part(pid)
    meshes = registry.build_component({"id": pid, "geometry": part["geometry"]}, part["_dir"])
    return part, meshes


def _volume(meshes):
    return sum(abs(m.volume) for m in meshes)


def _extents(meshes):
    lo = np.min([m.bounds[0] for m in meshes], axis=0)
    hi = np.max([m.bounds[1] for m in meshes], axis=0)
    return hi - lo


def test_parts_listed_and_valid():
    ids = [row["id"] for row in call("parts.list", category="propeller").data["parts"]]
    assert PROP_2B in ids
    for pid in _ids():
        assert library.part_errors(library.load_part(pid), pid) == []


def test_geometry_is_the_generator():
    assert _ids(), "no scale-prop part shipped"
    for pid in _ids():
        part = library.load_part(pid)
        assert part["geometry"]["generator"] == "propeller"
        meshes = registry.build_component(
            {"id": "p", "geometry": {"generator": "library_part", "params": {"part": pid}}}, part["_dir"])
        assert meshes and all(m.is_watertight for m in meshes)


def test_diameter_and_blades():
    part, meshes = _built(PROP_2B)
    ext = _extents(meshes)
    assert max(ext[1], ext[2]) == pytest.approx(191.0, abs=1.0)
    assert part["dimensions_mm"][1] == pytest.approx(191.0, abs=0.2)
    if PROP_8B in library.list_parts():
        part8, meshes8 = _built(PROP_8B)
        ext8 = _extents(meshes8)
        d8 = part8["geometry"]["params"]["diameter"]
        assert ext8[1] == pytest.approx(d8, rel=0.02)
        assert ext8[2] == pytest.approx(d8, rel=0.02)


def test_mass_is_volume_times_petg():
    for pid in _ids():
        part, meshes = _built(pid)
        assert part["mass_g"] == pytest.approx(_volume(meshes) * PETG_G_PER_MM3, abs=0.06)


def test_not_a_solid_disc():
    part, meshes = _built(PROP_2B)
    ext = _extents(meshes)
    disc = math.pi * 95.5 ** 2 * ext[0]
    assert _volume(meshes) < 0.05 * disc


def test_plane_parts_show_runs():
    assert call("parts.show", id=PROP_2B).ok
