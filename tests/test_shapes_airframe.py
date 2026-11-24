import math

import pytest

from hangar.geom import registry
from test_generators import build, vol


def A(r):
    return 0.5 * 48 * r * r * math.sin(2 * math.pi / 48)


def strut(**kw):
    p = {"start": [0, 0, 0], "end": [0, 100, 50], "diameter": 6}
    p.update(kw)
    return build("strut", p)[0]


GEAR = {"layout": "tricycle", "main_x": 100, "track": 200, "attach_z": 0, "ground_z": -100,
        "wheel_d": 40, "wheel_w": 12, "leg_d": 4, "front_x": -150}


def gear(**kw):
    p = dict(GEAR)
    p.update(kw)
    return build("landing_gear", p)[0]


def test_registered():
    assert {"strut", "landing_gear"} <= set(registry.names())


def test_strut_round_volume():
    m = strut()
    assert vol(m) == pytest.approx(A(3) * math.sqrt(100 ** 2 + 50 ** 2), rel=1e-6)
    assert m.is_watertight
    assert m.bounds[0][0] == pytest.approx(-3.0, abs=1e-6) and m.bounds[1][0] == pytest.approx(3.0, abs=1e-6)
    assert m.bounds[0][1] >= -3.0 and m.bounds[1][1] <= 103.0


def test_strut_streamlined_volume():
    m = strut(chord=18)
    assert vol(m) == pytest.approx(0.5 * 48 * (9 * 3) * math.sin(2 * math.pi / 48) * 111.8034, rel=1e-6)
    assert m.is_watertight
    assert m.bounds[0][0] == pytest.approx(-9.0, abs=1e-6) and m.bounds[1][0] == pytest.approx(9.0, abs=1e-6)


@pytest.mark.parametrize("end", [[0, 0, 80], [80, 0, 0]])
def test_strut_vertical_and_along_x_are_valid(end):
    m = strut(end=end)
    assert m.is_watertight
    assert vol(m) == pytest.approx(A(3) * 80, rel=1e-6)


def test_strut_validation():
    with pytest.raises(Exception, match="start"):
        strut(end=[0, 0, 0])
    with pytest.raises(Exception, match="chord"):
        strut(chord=4)


def test_tricycle_gear_volume():
    m = gear()
    assert vol(m) == pytest.approx(3 * A(20) * 12 + 3 * (A(2) * 80 - A(2) * 20), rel=2e-3)
    assert m.is_watertight
    assert m.bounds[0][2] == pytest.approx(-100.0, abs=1e-6) and m.bounds[1][2] == pytest.approx(0.0, abs=1e-6)
    assert m.bounds[0][1] == pytest.approx(-106, abs=1e-6) and m.bounds[1][1] == pytest.approx(106, abs=1e-6)
    assert m.bounds[0][0] == pytest.approx(-170, abs=1e-6) and m.bounds[1][0] == pytest.approx(120, abs=1e-6)


def test_splay_keeps_wheels_and_lengthens_legs():
    base = vol(gear())
    m = gear(leg_splay_deg=10)
    assert m.is_watertight
    assert m.bounds[0][1] == pytest.approx(-106, abs=1e-6) and m.bounds[1][1] == pytest.approx(106, abs=1e-6)
    # Brief value 2*A(2)*80*(1/cos-1) = 30.9 omitted that the tilted leg also gains overlap with its wheel: the
    # lowest 20 mm of vertical leg (wheel radius) lies inside the wheel and lengthens by the same factor, so
    # the union grows by only the 60 mm outside the wheel: 2*A(2)*60*(1/cos(10deg)-1) = 23.2 mm^3.
    exp = 2 * A(2) * 60 * (1 / math.cos(math.radians(10)) - 1)
    assert vol(m) - base == pytest.approx(exp, abs=1.0)


def test_taildragger_layout_check():
    with pytest.raises(Exception, match="front_x"):
        gear(layout="taildragger")
    m = gear(layout="taildragger", front_x=400)
    assert m.is_watertight
    assert m.bounds[1][0] == pytest.approx(420, abs=1e-6)


def test_gear_wheel_must_fit():
    with pytest.raises(Exception, match="wheel_d"):
        gear(wheel_d=150)
