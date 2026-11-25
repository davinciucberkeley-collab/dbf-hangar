"""U12.3-4: tail_surfaces generator (hand numbers from the brief)."""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from hangar.geom import registry
from hangar.geom.registry import get, validate_params

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
COMMON = {"stab_span": 300, "stab_root_chord": 100, "stab_tip_chord": 60, "fin_thickness": 3,
          "fin_height": 150, "fin_root_chord": 120, "fin_tip_chord": 60, "airfoil_file": "airfoils/diamond.dat"}


def build(name, params):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, FIXTURE_DIR)


def one(layout, **kw):
    ms = build("tail_surfaces", {**COMMON, "layout": layout, **kw})
    assert len(ms) == 1
    assert ms[0].is_watertight
    return ms[0]


def test_v_tail_volume_and_bounds():
    m = one("v")
    assert abs(m.volume) == pytest.approx(98000, rel=1e-3)
    assert m.bounds[0][1] == pytest.approx(-150, abs=1e-4)
    assert m.bounds[1][1] == pytest.approx(150, abs=1e-4)
    assert m.bounds[1][2] == pytest.approx(150 * math.tan(math.radians(35)) + 3.0, abs=0.05)


def test_conventional_volume_and_bounds():
    m = one("conventional")
    assert abs(m.volume) == pytest.approx(40500 + 98000 - 750, rel=2e-3)
    assert m.bounds[0][0] == pytest.approx(0, abs=1e-4)
    assert m.bounds[1][0] == pytest.approx(120, abs=1e-4)
    assert m.bounds[1][1] == pytest.approx(150, abs=1e-4)
    assert m.bounds[0][2] == pytest.approx(-5, abs=0.05)
    assert m.bounds[1][2] == pytest.approx(150, abs=0.05)


def test_t_tail_volume_and_bounds():
    m = one("t")
    assert abs(m.volume) == pytest.approx(138500 - 510, rel=2e-3)
    assert m.bounds[0][2] == pytest.approx(0, abs=0.05)
    assert m.bounds[1][2] == pytest.approx(155, abs=0.05)


def test_h_tail_volume_and_bounds():
    m = one("h")
    assert abs(m.volume) == pytest.approx(98000 + 2 * 40500 - 542, rel=2e-3)
    assert m.bounds[0][1] == pytest.approx(-151.5, abs=1e-3)
    assert m.bounds[1][1] == pytest.approx(151.5, abs=1e-3)
    assert m.bounds[0][2] == pytest.approx(-75, abs=0.05)
    assert m.bounds[1][2] == pytest.approx(75, abs=0.05)


def test_stab_x_offset():
    a = one("v")
    b = one("v", stab_x_le=400)
    assert b.bounds[0][0] == pytest.approx(400.0, abs=1e-4)
    assert abs(b.volume) == pytest.approx(abs(a.volume), rel=1e-6)


def test_validation():
    g = get("tail_surfaces")
    p = {**COMMON, "layout": "conventional"}
    del p["fin_height"]
    assert any("fin_height" in e for e in validate_params(g, p))
    v = {k: x for k, x in COMMON.items() if not k.startswith("fin_")}
    assert validate_params(g, {**v, "layout": "v"}) == []
    assert any("v_dihedral_deg" in e for e in validate_params(g, {**v, "layout": "v", "v_dihedral_deg": 90}))
