"""U4.36-4: airfoil_file accepts nacaXXXX and knowledge/airfoils names."""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

from hangar.geom import airfoil, registry
from hangar.geom.kernel import GeometryError

REPO = Path(__file__).resolve().parents[1]
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
WING = {"span": 1000, "root_chord": 200, "tip_chord": 150}
COMMON = {"stab_span": 300, "stab_root_chord": 100, "stab_tip_chord": 60, "fin_thickness": 3,
          "fin_height": 150, "fin_root_chord": 120, "fin_tip_chord": 60, "airfoil_file": "airfoils/diamond.dat"}


def build(name, params, base):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, base)


def wing(ref, base):
    return build("wing_panel", {"airfoil_file": ref, **WING}, base)


def test_naca0012_values():
    r = np.array(airfoil.naca4_rows("0012"))
    assert len(r) == 121
    assert r[0] == pytest.approx([1.0, 0.00126], abs=1e-6)
    assert r[60] == pytest.approx([0.0, 0.0], abs=1e-12)
    assert r[-1] == pytest.approx([1.0, -0.00126], abs=1e-6)
    assert r[:, 1].max() == pytest.approx(0.060015, abs=2e-5)
    assert r[:, 1].min() == pytest.approx(-0.060015, abs=2e-5)
    assert abs(r[np.argmax(r[:, 1]), 0] - 0.2966) < 0.005
    for i in range(121):
        assert r[i, 1] == pytest.approx(-r[120 - i, 1], abs=1e-9)


def test_naca2412_values():
    r = np.array(airfoil.naca4_rows("2412"))
    assert r[:, 1].max() == pytest.approx(0.079198, abs=2e-5)
    assert r[:, 1].min() == pytest.approx(-0.042360, abs=2e-5)
    assert r[60] == pytest.approx([0.0, 0.0], abs=1e-12)
    assert r[0, 0] == pytest.approx(1.0000838, abs=1e-6)


def test_naca_via_wing_panel_is_watertight_and_matches_file(tmp_path):
    ms = wing("naca2412", tmp_path)
    assert len(ms) == 1 and ms[0].is_watertight
    assert abs(ms[0].volume) == pytest.approx(2535464, rel=1e-3)
    lines = ["NACA 2412"] + [f"{x:.7f} {y:.7f}" for x, y in airfoil.naca4_rows("2412")]
    (tmp_path / "n.dat").write_text("\n".join(lines) + "\n")
    m2 = wing("n.dat", tmp_path)
    assert abs(m2[0].volume) == pytest.approx(abs(ms[0].volume), rel=1e-9)


def test_library_name_and_unknown_name(tmp_path, monkeypatch):
    (tmp_path / "lib").mkdir()
    (tmp_path / "airfoils").mkdir()
    src = REPO / "knowledge/airfoils/s5010.dat"
    shutil.copy(src, tmp_path / "lib" / "copy5010.dat")
    shutil.copy(src, tmp_path / "airfoils" / "s5010.dat")
    monkeypatch.setattr(airfoil, "AIRFOIL_DIR", tmp_path / "lib")
    a = wing("copy5010", tmp_path)
    b = wing("airfoils/s5010.dat", tmp_path)
    assert abs(a[0].volume) == pytest.approx(abs(b[0].volume), rel=1e-9)
    with pytest.raises(GeometryError) as e:
        wing("nosuch", tmp_path)
    assert "known:" in str(e.value) and "naca" in str(e.value)


def test_named_file_list_is_empty():
    def files(ref):
        return registry.component_files({"geometry": {"generator": "wing_panel", "params": {"airfoil_file": ref, **WING}}})
    assert files("naca2412") == []
    assert files("airfoils/s5010.dat") == ["airfoils/s5010.dat"]


def test_tail_surfaces_accepts_a_name():
    ms = build("tail_surfaces", {**COMMON, "airfoil_file": "naca0012", "layout": "conventional"}, FIXTURE_DIR)
    assert len(ms) == 1 and ms[0].is_watertight


def test_s5010_library_file_is_a_copy():
    assert (REPO / "knowledge/airfoils/s5010.dat").read_bytes() == (REPO / "designs/concept-a-param/airfoils/s5010.dat").read_bytes()
