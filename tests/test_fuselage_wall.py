"""U16.1 S9c: fuselage_loft wall, a hollow shell with closed ends."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from hangar.geom import registry
from hangar.geom.registry import get, validate_params
from hangar.geometry import component_parts

DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
BOX = dict(stations=[[0, 100, 60], [200, 100, 60]], shape="rect")
ELL = dict(stations=[[0, 40, 40], [100, 100, 60], [200, 40, 40]], nose_length=30, tail_length=30)


def build(params):
    return registry.build_component({"id": "f", "geometry": {"generator": "fuselage_loft", "params": params}}, DIR)[0]


def test_default_is_bit_identical():
    for p in (BOX, ELL):
        a, b = build(p), build({**p, "wall": 0.0})
        assert np.array_equal(a.vertices, b.vertices)
        assert np.array_equal(a.faces, b.faces)


def test_box_shell_volume():
    assert abs(build(BOX).volume) == pytest.approx(1_200_000, abs=1)
    m = build({**BOX, "wall": 2.0})
    assert abs(m.volume) == pytest.approx(146_304, abs=5)
    assert m.is_watertight


def test_box_shell_points():
    m = build({**BOX, "wall": 2.0})
    for pt, want in [((100, 0, 0), False), ((1, 0, 0), True), ((199, 0, 0), True), ((100, 49, 0), True),
                     ((100, 47, 0), False), ((100, 0, 29), True), ((100, 0, 27), False)]:
        assert bool(m.contains([pt])[0]) is want, pt


def test_ellipse_with_caps_is_hollow_and_closed():
    solid = build(ELL)
    m = build({**ELL, "wall": 3.0})
    assert m.is_watertight
    assert abs(m.volume) < abs(solid.volume)
    assert not m.contains([(100, 0, 0)])[0]
    assert m.contains([(-28, 0, 0)])[0]
    parts = m.split(only_watertight=False)
    assert len(parts) == 2
    assert sorted(x.volume > 0 for x in parts) == [False, True]
    assert m.volume > 0


def test_too_thick_is_refused():
    def msgs(**kw):
        return validate_params(get("fuselage_loft"), {"stations": [[0, 10, 10], [100, 10, 10]], "shape": "rect", **kw})
    assert any("wall" in str(x) for x in msgs(wall=5.0))
    assert not any("wall" in str(x) for x in msgs(wall=4.0))
    build({"stations": [[0, 10, 10], [100, 10, 10]], "shape": "rect", "wall": 4.0})
    assert any("wall" in str(x) for x in msgs(wall=-1))


def test_hollow_fuselage_still_takes_a_cavity():
    comp = {"id": "f", "geometry": {"generator": "fuselage_loft", "params": {**BOX, "wall": 2.0}},
            "position": [0, 0, 0]}
    cut = {**comp, "cavities": [{"geometry": {"box": {"size": [10, 10, 10]}}, "position": [100, 0, 29]}]}
    v0 = sum(abs(p.volume) for p in component_parts(comp, DIR))
    v1 = sum(abs(p.volume) for p in component_parts(cut, DIR))
    assert v0 - v1 == pytest.approx(200, abs=1)
