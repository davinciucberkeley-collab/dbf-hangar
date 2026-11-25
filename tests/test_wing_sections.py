from pathlib import Path

import numpy as np
import pytest

from hangar.geom import registry
from hangar.geom.registry import get, validate_params

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
DAT = "airfoils/diamond.dat"


def build(name, params, base=FIXTURE_DIR):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, base)


def wing(**kw):
    p = {"airfoil_file": DAT, "span": 400, "root_chord": 100, "tip_chord": 100, "part": "core", "hinge_frac": 0.75}
    p.update(kw)
    return p


def vol(m):
    return abs(float(m.volume))


def _one(parts):
    assert len(parts) == 1 if isinstance(parts, list) else True
    return parts[0] if isinstance(parts, list) else parts


def test_inboard_volume():
    m = _one(build("wing_panel", wing(tip_chord=50, inboard_span=100)))
    assert m.is_watertight
    assert vol(m) == pytest.approx(138541.67, rel=1e-5)
    assert m.bounds[1][0] == pytest.approx(75, abs=1e-6)


def test_inboard_zero_is_the_old_wing():
    a = _one(build("wing_panel", wing(tip_chord=50)))
    b = _one(build("wing_panel", wing(tip_chord=50, inboard_span=0)))
    assert vol(a) == pytest.approx(102083.33, rel=1e-6)
    assert vol(b) == pytest.approx(vol(a), rel=1e-12)
    assert np.allclose(a.bounds, b.bounds)


def test_inboard_with_sweep_and_dihedral_keeps_old_linear_laws():
    kw = dict(tip_chord=50, sweep_le_deg=10, dihedral_deg=3)
    m = _one(build("wing_panel", wing(inboard_span=100, **kw)))
    ref = _one(build("wing_panel", wing(**kw)))
    assert vol(m) == pytest.approx(138541.67, rel=1e-5)
    assert m.bounds[1][1] == pytest.approx(200, abs=1e-6)
    assert m.bounds[1][2] == pytest.approx(ref.bounds[1][2], abs=1e-6)


def test_inboard_elevon_gets_the_break():
    parts = build("wing_panel", wing(tip_chord=50, inboard_span=100, part="elevon", elevon_y=[50, 150], side="both"))
    assert len(parts) == 2
    for m in parts:
        assert vol(m) == pytest.approx(5533.85, rel=1e-4)


def test_inboard_checks():
    spec = get("wing_panel")
    for ib, bad in ((200, True), (-1, True), (150, False)):
        msgs = [m for m in validate_params(spec, wing(tip_chord=50, inboard_span=ib)) if "inboard_span" in str(m)]
        assert bool(msgs) is bad


def test_one_side():
    full = _one(build("wing_panel", wing(tip_chord=50, inboard_span=100)))
    m = _one(build("wing_panel", wing(tip_chord=50, inboard_span=100, side="right")))
    assert vol(m) == pytest.approx(vol(full) / 2, rel=1e-5)
    assert m.bounds[0][1] >= -1e-9
