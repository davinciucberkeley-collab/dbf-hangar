"""U4.22 Part A: wing_panel, fin, plate, fuselage_loft, motor_mount (hand numbers from the brief)."""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

from hangar.geom import registry
from hangar.geom.kernel import GeometryError, box, ngon_area
from hangar.geom.registry import get, validate_params
from hangar.geom.wing import read_airfoil

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


def test_read_airfoil_selig_and_lednicer_and_crlf(tmp_path):
    up, lo = read_airfoil(FIXTURE_DIR / DAT)
    assert np.allclose(up, [[0, 0], [0.5, 0.05], [1, 0]])
    assert np.allclose(lo, [[0, 0], [0.5, -0.05], [1, 0]])
    led = "diamond lednicer\n3. 3.\n\n0.0 0.0\n0.5 0.05\n1.0 0.0\n\n0.0 0.0\n0.5 -0.05\n1.0 0.0\n"
    f = tmp_path / "led.dat"
    f.write_bytes(led.replace("\n", "\r\n").encode())
    up2, lo2 = read_airfoil(f)
    assert np.allclose(up2, up) and np.allclose(lo2, lo)
    g = tmp_path / "selig.dat"
    g.write_bytes((FIXTURE_DIR / DAT).read_text().replace("\n", "\r\n").encode())
    up3, lo3 = read_airfoil(g)
    assert np.allclose(up3, up) and np.allclose(lo3, lo)


def test_wing_rect_core_volume():
    (m,) = build("wing_panel", wing())
    assert m.is_watertight
    assert vol(m) == pytest.approx(175000.0, rel=1e-6)
    b = m.bounds
    assert b[0][0] == pytest.approx(0, abs=1e-6) and b[1][0] == pytest.approx(75, abs=1e-6)
    assert b[0][1] == pytest.approx(-200, abs=1e-6) and b[1][1] == pytest.approx(200, abs=1e-6)


def test_wing_taper_sweep_dihedral_volume_and_bounds():
    (m,) = build("wing_panel", wing(tip_chord=50))
    assert vol(m) == pytest.approx(102083.33, rel=1e-6)
    (m,) = build("wing_panel", wing(tip_chord=50, sweep_le_deg=10, dihedral_deg=3))
    assert vol(m) == pytest.approx(102083.33, rel=1e-6)
    assert m.bounds[1][1] == pytest.approx(200, abs=1e-6)
    assert m.bounds[1][0] == pytest.approx(75.0, abs=0.05)
    assert m.bounds[1][2] == pytest.approx(12.98, abs=0.05)


def test_wing_side_right_is_half():
    (m,) = build("wing_panel", wing(side="right"))
    assert vol(m) == pytest.approx(87500.0, rel=1e-6)
    assert m.bounds[0][1] == pytest.approx(0, abs=1e-6) and m.bounds[1][1] == pytest.approx(200, abs=1e-6)


def test_wing_twist_changes_tip_only():
    (a,) = build("wing_panel", wing())
    (b,) = build("wing_panel", wing(twist_tip_deg=5))
    assert b.is_watertight

    def zext(m, y):
        s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        return s.bounds[:, 2]

    assert np.allclose(zext(a, 0), zext(b, 0), atol=1e-6)

    def edges(m):
        v = m.section(plane_origin=[0, 199.9, 0], plane_normal=[0, 1, 0]).vertices
        le = v[np.abs(v[:, 0] - v[:, 0].min()) < 1e-3][:, 2].mean()
        te = v[np.abs(v[:, 0] - v[:, 0].max()) < 1e-3][:, 2].mean()
        return le, te

    (le_a, te_a), (le_b, te_b) = edges(a), edges(b)
    assert le_b > le_a + 0.1 and te_b < te_a - 0.1


def test_wing_spar_bore():
    p = wing(root_chord=200, tip_chord=200, bore_x=100, bore_z=0, bore_d=9)
    (m,) = build("wing_panel", p)
    assert m.is_watertight
    assert vol(m) == pytest.approx(700000.0 - ngon_area(4.5) * 400, rel=1e-4)
    bad = wing(root_chord=200, tip_chord=200, bore_d=9)
    msgs = validate_params(get("wing_panel"), bad)
    assert any("bore_x" in m for m in msgs)


def test_wing_cut_files(tmp_path):
    (tmp_path / "airfoils").mkdir()
    shutil.copy(FIXTURE_DIR / DAT, tmp_path / DAT)
    box((20, 30, 10), (100, 0, 0)).export(tmp_path / "cutter.stl")
    p = wing(root_chord=200, tip_chord=200, cut_files=["cutter.stl"])
    (m,) = build("wing_panel", p, tmp_path)
    assert m.is_watertight
    assert vol(m) == pytest.approx(700000 - 6000, rel=1e-6)
    comp = {"id": "t", "geometry": {"generator": "wing_panel", "params": p}}
    assert registry.component_files(comp) == ["airfoils/diamond.dat", "cutter.stl"]
    box((20, 30, 10), (100, 500, 0)).export(tmp_path / "far.stl")
    (m,) = build("wing_panel", wing(root_chord=200, tip_chord=200, cut_files=["far.stl"]), tmp_path)
    assert vol(m) == pytest.approx(700000, rel=1e-6)
    with pytest.raises(GeometryError, match="nothere.stl"):
        build("wing_panel", wing(root_chord=200, tip_chord=200, cut_files=["nothere.stl"]), tmp_path)


def test_wing_elevon_split():
    p = wing(part="elevon", elevon_y=[50, 150], side="both")
    a, b = build("wing_panel", p)
    assert vol(a) == pytest.approx(6250.0, rel=1e-3) and vol(b) == pytest.approx(6250.0, rel=1e-3)
    assert a.bounds[0][1] == pytest.approx(50, abs=1e-6) and a.bounds[1][1] == pytest.approx(150, abs=1e-6)
    assert b.bounds[0][1] == pytest.approx(-150, abs=1e-6) and b.bounds[1][1] == pytest.approx(-50, abs=1e-6)
    for bad in ([150, 50], [0, 0]):
        msgs = validate_params(get("wing_panel"), wing(part="elevon", elevon_y=bad))
        assert any("elevon_y" in m for m in msgs)


def test_fin_trapezoid():
    p = {"thickness": 3, "root_chord": 100, "tip_chord": 40, "height": 200, "plane_y": 380}
    (m,) = build("fin", p)
    assert vol(m) == pytest.approx(42000.0, rel=1e-6)
    assert m.bounds[0][1] == pytest.approx(378.5) and m.bounds[1][1] == pytest.approx(381.5)
    assert m.bounds[0][2] == pytest.approx(0, abs=1e-6) and m.bounds[1][2] == pytest.approx(200)
    (m,) = build("fin", {**p, "sweep_le_deg": 20})
    assert vol(m) == pytest.approx(42000.0, rel=1e-6)
    (m,) = build("fin", {**p, "height": -200})
    assert m.bounds[0][2] == pytest.approx(-200) and m.bounds[1][2] == pytest.approx(0, abs=1e-6)


def test_plate_with_holes():
    p = {"size": [100, 50], "thickness": 3, "holes": [[-25, 0, 10], [25, 0, 10]]}
    (m,) = build("plate", p)
    assert vol(m) == pytest.approx(15000 - 2 * ngon_area(5) * 3, rel=1e-4)
    (m,) = build("plate", {"plane": "xz", "size": [100, 50], "thickness": 3, "center": [0, 10, 0]})
    assert m.bounds[0][1] == pytest.approx(8.5) and m.bounds[1][1] == pytest.approx(11.5)
    msgs = validate_params(get("plate"), {**p, "holes": [[60, 0, 10]]})
    assert any("holes" in m for m in msgs)


def test_fuselage_loft_frustum():
    st = [[0, 40, 20], [100, 20, 10]]
    (m,) = build("fuselage_loft", {"stations": st})
    assert m.is_watertight
    assert vol(m) == pytest.approx(36547.33, rel=1e-5)
    assert m.bounds[0][0] == pytest.approx(0, abs=1e-6) and m.bounds[1][0] == pytest.approx(100)
    assert m.bounds[0][1] == pytest.approx(-20) and m.bounds[1][1] == pytest.approx(20)
    (m,) = build("fuselage_loft", {"stations": st, "shape": "rect"})
    assert vol(m) == pytest.approx(100 / 3 * (800 + 200 + 400), rel=1e-6)
    msgs = validate_params(get("fuselage_loft"), {"stations": [[0, 40, 20], [0, 20, 10]]})
    assert any("stations" in m for m in msgs)


def test_motor_mount_volume():
    p = {"plate_size": [30, 30], "plate_t": 3, "bolt_pattern": [19, 16], "bolt_d": 2.5,
         "sleeve_od": 14, "sleeve_id": 10, "sleeve_len": 20}
    (m,) = build("motor_mount", p)
    A, L, t = ngon_area, 20, 3
    expect = 30 * 30 * t - 4 * A(1.25) * t + A(7) * L - A(5) * (t + L)
    assert m.is_watertight
    assert vol(m) == pytest.approx(expect, rel=2e-4)
    assert m.bounds[0][0] == pytest.approx(0, abs=1e-6) and m.bounds[1][0] == pytest.approx(23)
    msgs = validate_params(get("motor_mount"), {**p, "bolt_pattern": [10, 10]})
    assert any("bolt_pattern" in m for m in msgs)


def test_all_generators_listed():
    assert registry.names() == ["fin", "fuselage_loft", "mesh_file", "motor_mount", "plate", "tube", "wing_panel"]
