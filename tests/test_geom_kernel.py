"""U4.21: hangar.geom kernel, materials, generator registry (hand numbers from the brief)."""
from __future__ import annotations

import math

import numpy as np
import pytest
import trimesh

from hangar.design import REPO_ROOT
from hangar.geom import build_component, get
from hangar.geom.kernel import (GeometryError, box, difference, loft, ngon_area, prism, require_solid, tube,
                                union, volume_mm3)
from hangar.geom.materials import density_g_cm3, mass_g
from hangar.geom.registry import Generator, ParamSpec, register, validate_params

CONCEPT_A = REPO_ROOT / "designs" / "concept-a"


def n(r):
    return ngon_area(r)


def test_box_volume_and_mass():
    assert volume_mm3(box((10, 20, 30))) == pytest.approx(6000, rel=1e-9)
    assert mass_g(6000, 1.6) == pytest.approx(9.6)


def test_tube_matches_hand_area():
    t = tube("y", (60, 0, 0), 900, 12, 10)
    assert volume_mm3(t) == pytest.approx((n(6) - n(5)) * 900, abs=0.5)
    assert volume_mm3(t) == pytest.approx(31013.0, abs=0.5)
    assert np.allclose(t.bounds, [[54, -450, -6], [66, 450, 6]], atol=1e-6)
    assert t.is_watertight
    s = tube("x", (0, 0, 0), 10, 6, 0)
    assert volume_mm3(s) == pytest.approx(0.5 * 24 * 9 * math.sin(math.radians(15)) * 10, abs=0.05)
    assert volume_mm3(s) == pytest.approx(279.52, abs=0.05)


def test_prism_with_hole():
    hole = [(50 + 5 * math.cos(2 * math.pi * k / 48), 25 + 5 * math.sin(2 * math.pi * k / 48)) for k in range(48)]
    p = prism([(0, 0), (100, 0), (100, 50), (0, 50)], [hole], plane="xy", offset=0, depth=3)
    assert volume_mm3(p) == pytest.approx(100 * 50 * 3 - n(5) * 3, abs=0.05)
    assert volume_mm3(p) == pytest.approx(14765.05, abs=0.05)
    assert p.is_watertight


def test_loft_frustum():
    sq = lambda h: [(-h, -h), (h, -h), (h, h), (-h, h)]
    f = loft("z", [(0, sq(10)), (30, sq(5))])
    assert volume_mm3(f) == pytest.approx(30 / 3 * (400 + 100 + math.sqrt(400 * 100)), abs=1e-6)
    assert volume_mm3(f) == pytest.approx(7000, abs=1e-6)


def test_difference_box_minus_tube():
    d = difference(box((20, 20, 10)), [tube("z", (0, 0, 0), 20, 6, 0)])
    assert volume_mm3(d) == pytest.approx(4000 - 279.52, abs=0.05)
    assert d.is_watertight


def test_union_of_two_boxes_is_watertight():
    u = union([box((10, 10, 10)), box((10, 10, 10), center=(10, 0, 0))])
    assert u.is_watertight and volume_mm3(u) == pytest.approx(2000, rel=1e-6)


def test_require_solid_rejects_open_mesh():
    tri = trimesh.Trimesh([[0, 0, 0], [1, 0, 0], [0, 1, 0]], [[0, 1, 2]], process=False)
    with pytest.raises(GeometryError):
        require_solid(tri, "tri")


def test_density_lookup_standard_and_override():
    assert density_g_cm3("cfrp-tube") == 1.6
    assert density_g_cm3("x", {"x": {"density_g_cm3": 0.5}}) == 0.5
    assert density_g_cm3("cfrp-tube", {"cfrp-tube": {"density_g_cm3": 2.0}}) == 2.0
    with pytest.raises(KeyError) as e:
        density_g_cm3("nope")
    assert "cfrp-tube" in str(e.value)


def test_registry_validates_params():
    msgs = validate_params(get("tube"), {"axis": "w", "length": -1})
    names = {m.split(":")[0].split()[0] for m in msgs}
    assert names == {"axis", "length", "outer_d"}
    assert any(m.startswith("outer_d") and "missing" in m for m in msgs)
    assert any(m.startswith("foo") for m in validate_params(get("tube"), {"axis": "x", "length": 1, "outer_d": 2, "foo": 1}))
    assert any(m.startswith("length") for m in validate_params(get("tube"), {"axis": "x", "length": True, "outer_d": 2}))
    assert "inner_d must be less than outer_d" in validate_params(
        get("tube"), {"axis": "x", "length": 5, "outer_d": 6, "inner_d": 8})
    with pytest.raises(ValueError):
        register(Generator("tube", {}, lambda p, d: []))


@pytest.mark.parametrize("name,args", [
    ("wng-002", ("y", (60, 0, 0), 900, 12, 10)),
    ("fin-001-r", ("z", (294, 380, 0), 360, 16, 14)),
    ("fin-002-r", ("x", (178.25, 380, 0), 215.5, 14, 12)),
])
def test_tube_generator_matches_importer_stls(name, args):
    ref = trimesh.load(CONCEPT_A / "meshes" / f"{name}.stl", force="mesh")
    ax, c, ln, od, idd = args
    comp = {"id": name, "geometry": {"generator": "tube", "params": {
        "axis": ax, "center": list(c), "length": ln, "outer_d": od, "inner_d": idd}}}
    (m,) = build_component(comp, CONCEPT_A)
    assert volume_mm3(m) == pytest.approx(volume_mm3(ref), rel=1e-3)
    assert np.abs(m.bounds - ref.bounds).max() <= 0.01


def test_mesh_file_generator(tmp_path):
    b = box((10, 20, 30))
    b.export(tmp_path / "b.stl")
    (m,) = build_component({"id": "c", "geometry": {"generator": "mesh_file", "params": {"file": "b.stl"}}}, tmp_path)
    assert volume_mm3(m) == pytest.approx(volume_mm3(b), rel=1e-6)
