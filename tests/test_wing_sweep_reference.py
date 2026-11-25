"""U13.8-4: wing_panel opt-in sweep_reference (root | outboard_le)."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from hangar.geom import registry
from hangar.geom.registry import get, validate_params

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
DAT = "airfoils/diamond.dat"
P = {"airfoil_file": DAT, "span": 400, "root_chord": 100, "tip_chord": 50, "inboard_span": 100,
     "part": "full", "side": "right"}
T10 = math.tan(math.radians(10))


def build(name, params, base=FIXTURE_DIR):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, base)


def vol(m):
    return abs(float(m.volume))


def wp(**kw):
    return build("wing_panel", {**P, **kw})[0]


def le(m, y):
    v = np.asarray(m.vertices)
    return float(v[np.abs(v[:, 1] - y) < 1e-6][:, 0].min())


def test_default_is_bit_identical():
    for s in (0, 10):
        a = np.asarray(wp(sweep_le_deg=s).vertices)
        b = np.asarray(wp(sweep_le_deg=s, sweep_reference="root").vertices)
        assert np.array_equal(a, b)


def test_root_reference_leading_edge_offsets():
    m = wp(sweep_le_deg=10)
    assert le(m, 100) == pytest.approx(17.633, abs=1e-3)
    assert le(m, 200) == pytest.approx(35.265, abs=1e-3)


def test_outboard_reference_leading_edge_offsets():
    m = wp(sweep_le_deg=10, sweep_reference="outboard_le")
    assert le(m, 100) == pytest.approx(0.0, abs=1e-6)
    assert le(m, 200) == pytest.approx(17.633, abs=1e-3)
    assert le(m, 0) == pytest.approx(0.0, abs=1e-6)


def test_c172_numbers():
    c = dict(span=1200, root_chord=177, tip_chord=116, inboard_span=274)
    m = wp(**c, sweep_le_deg=3.3, sweep_reference="outboard_le")
    assert le(m, 274) == pytest.approx(0.0, abs=1e-6)
    assert le(m, 600) == pytest.approx(326 * math.tan(math.radians(3.3)), abs=1e-2)
    assert le(m, 600) == pytest.approx(18.80, abs=1e-2)
    h = wp(**c, sweep_le_deg=1.8, sweep_reference="root")
    assert le(h, 274) == pytest.approx(8.61, abs=1e-2)
    assert le(h, 600) == pytest.approx(18.85, abs=1e-2)
    # exact: 600 tan(1.8 deg) = 18.8558, 326 tan(3.3 deg) = 18.7970, gap 0.0588 (brief rounded to 0.05)
    assert abs(le(h, 600) - le(m, 600)) < 0.06


def test_volume_is_invariant_to_the_reference():
    v0 = vol(wp(sweep_le_deg=0))
    for r in ("root", "outboard_le"):
        assert vol(wp(sweep_le_deg=10, sweep_reference=r)) == pytest.approx(v0, rel=1e-6)


def test_dihedral_and_twist_stay_root_referenced():
    for kw in ({"dihedral_deg": 3}, {"twist_tip_deg": 2}):
        for r in ("root", "outboard_le"):
            a = np.asarray(wp(sweep_le_deg=10, **kw).vertices)
            b = np.asarray(wp(sweep_le_deg=10, sweep_reference=r, **kw).vertices)
            za = np.sort(a[np.abs(a[:, 1] - 200) < 1e-6][:, 2])
            zb = np.sort(b[np.abs(b[:, 1] - 200) < 1e-6][:, 2])
            assert np.allclose(za, zb, atol=1e-9)


def test_check():
    g = get("wing_panel")
    bad = validate_params(g, {**P, "inboard_span": 0, "sweep_reference": "outboard_le"})
    assert any("sweep_reference" in str(e) for e in bad)
    assert not any("sweep_reference" in str(e) for e in validate_params(g, {**P, "sweep_reference": "outboard_le"}))
    unk = validate_params(g, {**P, "sweep_reference": "tip"})
    assert any("sweep_reference" in str(e) for e in unk)


def test_docs_say_it():
    ps = get("wing_panel").params
    assert "inboard_span" in ps["sweep_le_deg"].doc and "outboard_le" in ps["sweep_le_deg"].doc
    assert "dihedral and twist always start at the root" in ps["inboard_span"].doc


def test_split_wing_follows_the_reference():
    kw = dict(airfoil_file=DAT, span=400, root_chord=100, tip_chord=50, inboard_span=20, hinge_frac=0.75,
              part="core", elevon_y=[50, 150], core_fill="outside")
    ref = build("wing_panel", {**kw, "sweep_le_deg": 0})
    m = build("wing_panel", {**kw, "sweep_le_deg": 10, "sweep_reference": "outboard_le"})
    assert len(m) == 1 and m[0].is_watertight
    assert vol(m[0]) == pytest.approx(vol(ref[0]), rel=1e-4)
