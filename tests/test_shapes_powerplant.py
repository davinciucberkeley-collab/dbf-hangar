import math

import pytest

from hangar.geom import registry
from test_generators import build, vol


def A(r):
    return 0.5 * 48 * r * r * math.sin(2 * math.pi / 48)


NAC = {"length": 200, "diameter": 60}


def nac(**kw):
    p = dict(NAC)
    p.update(kw)
    return build("nacelle", p)[0]


def test_registered():
    assert {"nacelle", "propeller"} <= set(registry.names())


def test_nacelle_volume_frustum_chain():
    m = nac(nose_length=40, nose_shape="cone", tail_length=60, tail_end_frac=0.3)
    exp = A(30) * (40 / 3 * (1 + 0.02 ** 2 + 0.02) + 100 + 60 / 3 * (1 + 0.3 ** 2 + 0.3))
    assert vol(m) == pytest.approx(exp, rel=5e-4)
    assert m.is_watertight
    assert m.bounds[0][0] == pytest.approx(-100, abs=1e-6) and m.bounds[1][0] == pytest.approx(100, abs=1e-6)
    for i in (1, 2):
        assert m.bounds[0][i] == pytest.approx(-30, abs=0.05) and m.bounds[1][i] == pytest.approx(30, abs=0.05)


def test_nacelle_ellipsoid_nose_two_thirds():
    m = nac(nose_length=40, nose_shape="ellipsoid", cap_rings=16, tail_length=0)
    assert vol(m) - A(30) * 160 == pytest.approx(2 / 3 * A(30) * 40, rel=0.02)


def test_nacelle_inlet_removes_bore():
    kw = dict(nose_length=0, tail_length=60, tail_end_frac=0.3)
    a = vol(nac(**kw))
    b = vol(nac(inlet_d=20, inlet_depth=30, **kw))
    assert a - b == pytest.approx(A(10) * 30, rel=1e-3)


def test_nacelle_validation():
    with pytest.raises(Exception, match="nose_length"):
        nac(nose_length=150, tail_length=100)
    with pytest.raises(Exception, match="inlet"):
        nac(inlet_d=20)


PROP = {"diameter": 228.6, "hub_d": 16, "hub_length": 12, "root_chord": 14, "tip_chord": 8,
        "thickness_frac": 0.08, "pitch_deg": 15}


def prop(**kw):
    p = dict(PROP)
    p.update(kw)
    return build("propeller", p)[0]


def ext(m, i):
    return m.bounds[1][i] - m.bounds[0][i]


def test_propeller_bounds_and_blade_count_volume():
    m2, m4 = prop(blades=2), prop(blades=4)
    assert m2.is_watertight and m4.is_watertight
    assert ext(m2, 1) == pytest.approx(228.6, abs=0.5)
    assert ext(m4, 1) == pytest.approx(228.6, abs=0.5) and ext(m4, 2) == pytest.approx(228.6, abs=0.5)
    a0, a1, r0, R = 0.08 * 14 ** 2, 0.08 * 8 ** 2, 7, 114.3
    vb = (R - r0) / 3 * (a0 + a1 + math.sqrt(a0 * a1))
    assert vol(m4) - vol(m2) == pytest.approx(2 * vb, rel=0.03)


def test_propeller_spinner():
    a, b = prop(blades=2), prop(blades=2, spinner_length=25)
    assert b.bounds[0][0] == pytest.approx(-6 - 25, abs=0.01)
    # the cone starts 1 mm inside the hub (x = -5, r = 8) and ends at x = -31, r = 0.16; only the part
    # beyond the hub face (x < -6, r1 = 8 - 7.84/26) adds volume: a 25 mm frustum from r1 to 0.16
    r1 = 8 - (8 - 0.16) / 26
    q = 0.16 / r1
    assert vol(b) - vol(a) == pytest.approx(A(r1) * (25 / 3) * (1 + q * q + q), rel=0.03)


def test_propeller_handed_mirrors_pitch():
    a, b = prop(blades=2, handed="cw"), prop(blades=2, handed="ccw")
    assert vol(a) == pytest.approx(vol(b), rel=1e-6)
    assert abs(abs(a.bounds[0][2]) - abs(b.bounds[0][2])) < 1e-6
    assert abs(abs(a.bounds[1][2]) - abs(b.bounds[1][2])) < 1e-6


def test_propeller_validation():
    with pytest.raises(Exception, match="hub_d"):
        prop(blades=2, hub_d=300)
    with pytest.raises(Exception, match="root_chord"):
        prop(blades=2, root_chord=20, hub_length=12)
