"""U16.1 S6: hinge gap, bevel and knuckles on generated control surfaces (generator params only)."""
import math
from pathlib import Path

import numpy as np
import pytest

from hangar.geom import kernel, registry, wing, hinge
from hangar.geom.registry import get, validate_params
from hangar.geometry import joint_rotation

DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
WING = dict(airfoil_file="naca0012", span=400, root_chord=100, tip_chord=100, part="elevon", hinge_frac=0.7,
            elevon_y=[20, 180], side="right")
TAIL = dict(layout="conventional", airfoil_file="naca0012", stab_span=400, stab_root_chord=100, stab_tip_chord=100,
            fin_thickness=12, fin_height=100, fin_root_chord=100, fin_tip_chord=100, hinge_frac=0.7)
FIN = dict(thickness=12, root_chord=100, tip_chord=100, height=100, hinge_frac=0.7, part="rear")
DEFAULTS = dict(hinge_gap=0.0, hinge_style="none", hinge_throw_deg=0.0, hinge_knuckles=0, knuckle_d=0.0,
                knuckle_len=0.0)
ANGLES = range(-25, 26, 5)


def build(name, params):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, DIR)


def one(name, params):
    ms = build(name, params)
    assert len(ms) == 1
    return ms[0]


def rot(mesh, p0, axis, deg):
    m = mesh.copy()
    m.apply_transform(joint_rotation({"axis": axis, "pivot": p0}, deg))
    return m.vertices


def min_x_swept(mesh, p0, axis):
    """Smallest x over all angles, relative to the hinge plane x = p0[0] (the brief's hand values are relative)."""
    return min(float(rot(mesh, p0, axis, a)[:, 0].min()) for a in ANGLES) - p0[0]


def test_pure_helpers():
    assert hinge.sweep_factor(160 * math.tan(math.radians(20)), 160) == pytest.approx(1.0641778, abs=1e-6)
    r, f = hinge.front_offsets(1.0, 3.6634, 25, "bevel")
    assert (r, f) == (pytest.approx(1.0, abs=1e-6), pytest.approx(2.7082715, abs=1e-6))
    assert hinge.front_offsets(1.0, 3.6634, 25, "none") == (None, 1.0)
    assert hinge.front_offsets(1.0, 3.6634, 25, "bevel", k=1.0641778)[0] == pytest.approx(1.0641778, abs=1e-6)
    cyl = hinge.cylinder_between([0, 0, 0], [0, 0, 10], 2)
    assert cyl.bounds[:, 2] == pytest.approx([0, 10], abs=1e-6)
    assert cyl.bounds[:, 0] == pytest.approx([-2, 2], abs=1e-6)
    assert cyl.is_watertight
    with pytest.raises(kernel.GeometryError):
        hinge.sweep_factor(1, 0)


def _same(a, b):
    assert np.array_equal(a.vertices, b.vertices) and np.array_equal(a.faces, b.faces)


def test_defaults_are_bit_identical():
    _same(one("wing_panel", WING), one("wing_panel", {**WING, **DEFAULTS}))
    t = {**TAIL, "part": "elevator"}
    _same(one("tail_surfaces", t), one("tail_surfaces", {**t, **DEFAULTS}))
    f = {**FIN}
    _same(one("fin", f), one("fin", {**f, **DEFAULTS}))


def test_gap_only_moves_the_front():
    p0, p1 = wing.hinge_line(WING, DIR)
    assert p0 == pytest.approx([70, 20, 0], abs=1e-9)
    assert p1 == pytest.approx([70, 180, 0], abs=1e-9)
    base = one("wing_panel", WING)
    m = one("wing_panel", {**WING, "hinge_gap": 1.5})
    assert m.vertices[:, 0].min() == pytest.approx(71.5, abs=1e-6)
    assert m.vertices[:, 0].max() == pytest.approx(base.vertices[:, 0].max(), abs=1e-9)
    assert m.volume < base.volume


BEVEL = {**WING, "hinge_gap": 1.0, "hinge_style": "bevel", "hinge_throw_deg": 25}


def test_bevel_ridge_and_chamfer():
    v = one("wing_panel", BEVEL).vertices
    assert v[:, 0].min() == pytest.approx(71.0, abs=1e-6)
    assert np.all(np.abs(v[v[:, 0] < 71.0 + 1e-6][:, 2]) < 1e-9)
    e = v[np.abs(v[:, 1] - 20) < 1e-6]
    xs = np.unique(np.round(e[:, 0], 9))
    assert xs[1] == pytest.approx(72.7083, abs=2e-4)
    assert np.abs(e[np.abs(e[:, 0] - xs[1]) < 1e-6][:, 2]) == pytest.approx(3.3953, abs=2e-3)


def test_wing_clearance_property():
    axis, p0 = [0, 1, 0], [70, 20, 0]
    res = {}
    for gap, style in ((0.0, "none"), (0.0, "bevel"), (1.0, "bevel")):
        m = one("wing_panel", {**WING, "hinge_gap": gap, "hinge_style": style, "hinge_throw_deg": 25})
        res[(gap, style)] = min_x_swept(m, p0, axis)
    assert res[(0.0, "none")] == pytest.approx(-1.5482, abs=2e-3)
    assert res[(0.0, "bevel")] >= -1e-6
    assert res[(1.0, "bevel")] >= 0.9


def test_swept_wing_uses_the_sweep_factor():
    params = {**BEVEL, "sweep_le_deg": 20}
    p0, p1 = (np.array(x) for x in wing.hinge_line(params, DIR))
    n = np.array([math.cos(math.radians(20)), -math.sin(math.radians(20)), 0])
    m = one("wing_panel", params)
    assert ((m.vertices - p0) @ n).min() == pytest.approx(1.0, abs=1e-6)
    for a in ANGLES:
        v = rot(m, p0, p1 - p0, a)
        assert ((v - p0) @ n).min() >= 0.9


KN = {**BEVEL, "hinge_knuckles": 2, "knuckle_d": 1.8, "knuckle_len": 8}


def test_knuckles():
    m = one("wing_panel", KN)
    assert len(m.split(only_watertight=False)) == 1
    x = m.vertices[:, 0]
    assert 70.095 <= x.min() <= 70.105
    y = m.vertices[x < 70.5][:, 1]
    ok = ((y >= 56 - 1e-6) & (y <= 64 + 1e-6)) | ((y >= 136 - 1e-6) & (y <= 144 + 1e-6))
    assert ok.all()
    dv = m.volume - one("wing_panel", BEVEL).volume
    assert 5 < dv < 41
    assert min_x_swept(m, [70, 20, 0], [0, 1, 0]) >= -1e-6

    def msgs(**kw):
        return [str(e) for e in validate_params(get("wing_panel"), {**WING, **kw})]
    assert any("knuckle_d" in s for s in msgs(hinge_gap=1.0, hinge_knuckles=2, knuckle_d=3.0, knuckle_len=8))
    assert any("hinge_gap" in s for s in msgs(hinge_knuckles=2, knuckle_d=1.0, knuckle_len=8))
    assert any("hinge_throw_deg" in s for s in msgs(hinge_style="bevel"))
    assert any("only part elevon" in s for s in msgs(part="full", hinge_gap=1))


def test_tail_elevator_and_rudder():
    el = {**TAIL, "part": "elevator"}
    assert one("tail_surfaces", {**el, "hinge_gap": 1.5}).vertices[:, 0].min() == pytest.approx(71.5, abs=1e-6)
    assert one("fin", {**FIN, "hinge_gap": 1.5}).vertices[:, 0].min() == pytest.approx(71.5, abs=1e-6)
    b = {**FIN, "hinge_gap": 1.0, "hinge_style": "bevel", "hinge_throw_deg": 25}
    m = one("fin", b)
    assert m.vertices[:, 0].min() == pytest.approx(71.0, abs=1e-6)
    sec = m.vertices[np.abs(m.vertices[:, 2]) < 1e-6]
    xs = np.unique(np.round(sec[:, 0], 9))
    assert xs[0] == pytest.approx(71.0, abs=2e-4) and xs[1] == pytest.approx(73.7978, abs=2e-4)
    res = {}
    for gap, style in ((0.0, "none"), (0.0, "bevel"), (1.0, "bevel")):
        mm = one("fin", {**FIN, "hinge_gap": gap, "hinge_style": style, "hinge_throw_deg": 25})
        res[(gap, style)] = min_x_swept(mm, [70, 0, 0], [0, 0, 1])
    assert res[(0.0, "none")] == pytest.approx(-2.5357, abs=2e-3)
    assert res[(0.0, "bevel")] >= -1e-6
    assert res[(1.0, "bevel")] >= 0.9
    assert one("tail_surfaces", {**TAIL, "part": "rudder", "hinge_gap": 1.5}).vertices[:, 0].min() == pytest.approx(
        71.5, abs=1e-6)
    msgs = [str(e) for e in validate_params(get("tail_surfaces"), {**TAIL, "part": "full", "hinge_gap": 1})]
    assert any("only part elevator or rudder" in s for s in msgs)
