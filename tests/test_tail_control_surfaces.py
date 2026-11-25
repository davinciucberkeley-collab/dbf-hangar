"""U4.37-4b: tail_surfaces and fin build fixed part, elevator or rudder (hand numbers from the brief)."""
from __future__ import annotations

from pathlib import Path

import pytest

from hangar.geom import registry
from hangar.geom.registry import get, validate_params

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
COMMON = {"stab_span": 300, "stab_root_chord": 100, "stab_tip_chord": 60, "fin_thickness": 3,
          "fin_height": 150, "fin_root_chord": 120, "fin_tip_chord": 60, "airfoil_file": "airfoils/diamond.dat"}


def build(name, params):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, FIXTURE_DIR)


def one(layout="conventional", **kw):
    ms = build("tail_surfaces", {**COMMON, "layout": layout, **kw})
    assert len(ms) == 1
    assert ms[0].is_watertight
    return ms[0]


def vol(layout="conventional", **kw):
    return abs(one(layout, **kw).volume)


def test_default_part_is_full_and_unchanged():
    assert vol() == pytest.approx(vol(part="full"), rel=1e-12)
    assert vol() == pytest.approx(40500 + 98000 - 750, rel=2e-3)


def test_elevator_volume():
    assert vol(part="elevator") == pytest.approx(0.009 / 0.05 * 98000, rel=1e-3)


def test_rudder_volume():
    assert vol(part="rudder") == pytest.approx(0.3 * 40500, rel=1e-3)


def test_pieces_sum_to_the_whole():
    parts = vol(part="fixed") + vol(part="elevator") + vol(part="rudder")
    assert parts == pytest.approx(vol(part="full"), rel=0.01)


def test_fin_parts():
    fin = {"thickness": 3, "root_chord": 120, "tip_chord": 60, "height": 150}
    assert abs(build("fin", {**fin, "part": "front"})[0].volume) == pytest.approx(28350, rel=1e-6)
    assert abs(build("fin", {**fin, "part": "rear"})[0].volume) == pytest.approx(12150, rel=1e-6)
    msgs = validate_params(get("fin"), {**fin, "hinge_frac": 1.0})
    assert any("hinge_frac" in m for m in msgs)


def test_v_layout():
    msgs = validate_params(get("tail_surfaces"), {**COMMON, "layout": "v", "part": "rudder"})
    assert any("rudder" in m for m in msgs)
    one("v", part="elevator")


def test_hinge_frac_validation():
    for f in (0, 1):
        msgs = validate_params(get("tail_surfaces"), {**COMMON, "hinge_frac": f})
        assert any("hinge_frac" in m for m in msgs)
