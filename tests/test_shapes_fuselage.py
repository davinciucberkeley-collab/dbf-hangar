"""U12.3-1: fuselage_loft nose and tail caps, upsweep, super-ellipse (hand formulas from the brief)."""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from hangar.geom import registry
from hangar.geom.registry import get, validate_params

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
ST = [[0, 40, 20], [100, 40, 20]]


def build(name, params, base=FIXTURE_DIR):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, base)


def vol(m):
    return abs(float(m.volume))


def A(w, h):
    return 0.5 * 48 * (w / 2) * (h / 2) * math.sin(2 * math.pi / 48)


def fus(**kw):
    (m,) = build("fuselage_loft", {"stations": ST, **kw})
    return m


def test_default_unchanged():
    (m,) = build("fuselage_loft", {"stations": [[0, 40, 20], [100, 20, 10]]})
    assert vol(m) == pytest.approx(36547.33, rel=1e-5)


def test_cone_nose_and_tail_volume():
    m = fus(nose_length=30, tail_length=50)
    c = 1 + 0.02 ** 2 + 0.02
    expect = A(40, 20) * 100 + A(40, 20) * 30 / 3 * c + A(40, 20) * 50 / 3 * c
    assert m.is_watertight
    assert vol(m) == pytest.approx(expect, rel=1e-4)
    assert m.bounds[0][0] == pytest.approx(-30.0, abs=1e-6)
    assert m.bounds[1][0] == pytest.approx(150.0, abs=1e-6)


def test_ellipsoid_nose_is_about_two_thirds():
    n, L = 16, 30
    m = fus(nose_length=L, nose_shape="ellipsoid", cap_rings=n)
    nose = vol(m) - A(40, 20) * 100
    assert nose == pytest.approx(2 / 3 * A(40, 20) * L, rel=0.02)

    def s(t):
        return max(0.02, math.sqrt(1 - (1 - t) ** 2))
    chain = sum(L / n / 3 * A(40, 20) * (s(k / n) ** 2 + s((k + 1) / n) ** 2 + s(k / n) * s((k + 1) / n))
                for k in range(n))
    assert nose == pytest.approx(chain, rel=1e-4)


def test_upsweep_keeps_volume_and_lifts_tail():
    a = fus(tail_length=50)
    b = fus(tail_length=50, tail_upsweep_deg=10)
    assert vol(b) == pytest.approx(vol(a), rel=1e-6)
    # Tail end top = 50*tan10 + 10*0.02 = 9.016 < 10 (body top), so the body still sets the bound at 50.
    tail_top = 50 * math.tan(math.radians(10)) + 10 * 0.02
    assert b.bounds[1][2] == pytest.approx(max(10.0, tail_top), abs=1e-4)
    # With tail 100 the end top 100*tan10 + 0.2 = 17.83 exceeds the body and sets the bound.
    c = fus(tail_length=100, tail_upsweep_deg=10)
    assert c.bounds[1][2] == pytest.approx(100 * math.tan(math.radians(10)) + 10 * 0.02, abs=1e-4)


def test_superellipse():
    e = vol(fus(shape="ellipse"))
    r = vol(fus(shape="rect"))
    assert vol(fus(shape="superellipse", exponent=2.0)) == pytest.approx(e, rel=1e-9)
    m = fus(shape="superellipse", exponent=4.0)
    assert e < vol(m) < r
    assert m.bounds[0][1] == pytest.approx(-20, abs=1e-6) and m.bounds[1][1] == pytest.approx(20, abs=1e-6)
    assert m.bounds[0][2] == pytest.approx(-10, abs=1e-6) and m.bounds[1][2] == pytest.approx(10, abs=1e-6)


@pytest.mark.parametrize("name,val", [("tip_frac", 0.7), ("exponent", 1.0), ("tail_upsweep_deg", 75),
                                      ("nose_length", -1)])
def test_new_param_validation(name, val):
    p = {"stations": ST, name: val}
    if name == "exponent":
        p["shape"] = "superellipse"
    msgs = validate_params(get("fuselage_loft"), p)
    assert msgs and any(name in m for m in msgs)
