"""U4.37-4a / U4.39: fuselage_loft per-station centre z and opt-in smooth_rings."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from hangar.geom import registry
from hangar.geom.registry import get, validate_params

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
ST3 = [[0, 40, 20], [100, 40, 20]]
BULGE = [[0, 40, 20], [100, 60, 30], [200, 40, 20]]


def build(name, params, base=FIXTURE_DIR):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, base)


def vol(m):
    return abs(float(m.volume))


def A(w, h):
    return 0.5 * 48 * (w / 2) * (h / 2) * math.sin(2 * math.pi / 48)


def fus(stations, **kw):
    (m,) = build("fuselage_loft", {"stations": stations, **kw})
    return m


def test_no_dz_is_bit_identical():
    kw = dict(nose_length=30, tail_length=50, tail_upsweep_deg=10)
    a = fus(ST3, **kw)
    b = fus([s + [0] for s in ST3], **kw)
    assert np.array_equal(a.vertices, b.vertices)


def test_dz_shifts_a_station():
    m = fus([[0, 40, 20, 0], [100, 40, 20, 30]])
    assert vol(m) == pytest.approx(vol(fus(ST3)), rel=1e-9)
    assert m.bounds[0][2] == pytest.approx(-10, abs=1e-6)
    assert m.bounds[1][2] == pytest.approx(40, abs=1e-6)


def test_nose_follows_first_station_dz():
    m = fus([[0, 40, 20, 30], [100, 40, 20]], nose_length=30)
    assert m.bounds[1][2] == pytest.approx(40, abs=1e-6)
    assert m.bounds[0][2] == pytest.approx(-10, abs=1e-6)


def test_tail_cap_starts_from_last_station_dz():
    m = fus([[0, 40, 20], [100, 40, 20, 30]], tail_length=100, tail_upsweep_deg=10)
    assert m.bounds[1][2] == pytest.approx(30 + 100 * math.tan(math.radians(10)) + 10 * 0.02, abs=1e-4)


def test_smooth_rings_default_is_bit_identical():
    a = fus(BULGE)
    b = fus(BULGE, smooth_rings=1)
    assert np.array_equal(a.vertices, b.vertices)


def test_smooth_rings_straight_is_unchanged():
    a = fus(ST3)
    b = fus(ST3, smooth_rings=4)
    assert vol(b) == pytest.approx(vol(a), rel=1e-9)
    assert len(b.vertices) > len(a.vertices)


def test_smooth_rings_bulge_hits_the_stations():
    m = fus(BULGE, smooth_rings=4)
    assert m.is_watertight
    assert m.bounds[1][1] == pytest.approx(30, abs=1e-6)
    assert m.bounds[1][2] == pytest.approx(15, abs=1e-6)
    assert vol(fus(BULGE)) < vol(m) < A(60, 30) * 200


def test_smooth_rings_dz():
    m = fus([[0, 40, 20, 0], [100, 40, 20, 30], [200, 40, 20, 0]], smooth_rings=4)
    assert m.bounds[1][2] == pytest.approx(40, abs=1e-6)
    assert m.bounds[0][2] == pytest.approx(-10, abs=1e-6)


def _msgs(params):
    return " ".join(str(x) for x in validate_params(get("fuselage_loft"), params))


def test_smooth_rings_validation():
    assert "smooth_rings" in _msgs({"stations": ST3, "smooth_rings": 0})


def test_station_validation():
    assert "stations" in _msgs({"stations": [[0, 40, 20, 1, 2], [100, 40, 20]]})
    assert "stations" in _msgs({"stations": [[0, 40, 20, "a"], [100, 40, 20]]})
    assert "stations" not in _msgs({"stations": [[0, 40, 20, -5], [100, 40, 20]]})
