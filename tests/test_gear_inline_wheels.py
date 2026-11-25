import math

import numpy as np
import pytest

from hangar.geom.registry import get, validate_params
from test_generators import build, vol

G = {"layout": "tricycle", "main_x": 500, "track": 400, "attach_z": 100, "ground_z": 0,
     "wheel_d": 40, "wheel_w": 15, "leg_d": 8, "front_x": 100}


def gear(**kw):
    p = dict(G)
    p.update(kw)
    return build("landing_gear", p)


def msgs(**kw):
    p = dict(G)
    p.update(kw)
    return validate_params(get("landing_gear"), p)


Vw = vol(build("tube", {"axis": "y", "length": 15, "outer_d": 40})[0])
Vb1 = vol(build("tube", {"axis": "x", "length": 1.0, "outer_d": 8})[0])


def test_one_wheel_is_bit_identical():
    a = gear()[0].vertices
    b = gear(main_wheels=1, wheel_pitch=60)[0].vertices
    assert np.array_equal(a, b)


def test_three_wheels_volume():
    parts = gear(main_wheels=3, wheel_pitch=60)
    assert len(parts) == 1 and parts[0].is_watertight
    d = vol(parts[0]) - vol(gear()[0])
    assert d == pytest.approx(2 * (2 * Vw + 2 * (60 - 40) * Vb1), rel=1e-3)


def test_three_wheels_bounds():
    b = gear(main_wheels=3, wheel_pitch=60)[0].bounds
    assert b[1][0] == pytest.approx(580, abs=1e-3)
    assert b[0][0] == pytest.approx(100 - 20, abs=1e-3)


def test_pitch_check():
    assert any("wheel_pitch" in m for m in msgs(main_wheels=3, wheel_pitch=30))
    assert msgs(main_wheels=3, wheel_pitch=60) == []
    assert any("wheel_pitch" in m for m in msgs(main_wheels=2))


def test_two_wheels_symmetry():
    b = gear(main_wheels=2, wheel_pitch=50)[0].bounds
    assert abs(b[0][1] + b[1][1]) < 1e-6


def test_disc_shape_is_bit_identical():
    assert np.array_equal(gear()[0].vertices, gear(wheel_shape="disc")[0].vertices)


def test_tyre_shape():
    m = gear(wheel_shape="tyre")[0]
    assert m.is_watertight
    assert vol(m) < vol(gear()[0])
    b, b0 = m.bounds, gear()[0].bounds
    assert np.allclose(b, b0, atol=1e-3)
    assert msgs(wheel_shape="square")


def test_front_attach_z():
    assert np.array_equal(gear()[0].vertices, gear(front_attach_z=100)[0].vertices)
    m = gear(front_attach_z=60)[0]
    assert m.is_watertight and m.bounds[1][2] == pytest.approx(100, abs=1e-3)
    assert any("front_attach_z" in x for x in msgs(front_attach_z=40))
    assert msgs(front_attach_z=60) == []
