"""U4.41-5: tail_surfaces elevator_fin_gap keeps the elevator clear of the fin (hand numbers from the brief)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from hangar.geom import kernel, registry
from hangar.geom.registry import get, validate_params

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
COMMON = {"stab_span": 300, "stab_root_chord": 100, "stab_tip_chord": 60, "fin_thickness": 3,
          "fin_height": 150, "fin_root_chord": 120, "fin_tip_chord": 60, "airfoil_file": "airfoils/diamond.dat"}


def build(name, params):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, FIXTURE_DIR)


def one(**kw):
    ms = build("tail_surfaces", {**COMMON, **kw})
    assert len(ms) == 1
    return ms[0]


def overlap(a, b):
    return abs(a.volume) + abs(b.volume) - abs(kernel.union([a, b]).volume)


def test_default_is_bit_identical():
    a = one(layout="conventional", part="elevator")
    b = one(layout="conventional", part="elevator", elevator_fin_gap=0.0)
    assert np.array_equal(a.vertices, b.vertices)
    assert abs(a.volume) == pytest.approx(17640, rel=1e-3)


def test_conventional_gap_volume():
    m = one(layout="conventional", part="elevator", elevator_fin_gap=1.0)
    assert abs(m.volume) == pytest.approx(17193, rel=1e-3)


# T layout derivation: the stabiliser (z = 150, thickness about 5 mm) sits on the fin top. With the default
# fin_x_le = 0 the rudder at the top spans x 42..60 (0.7 * 60 .. 60), clear of the elevator (x 70..100), so
# there is no overlap. With fin_x_le = 40 the rudder at the top spans x 82..100, inside the elevator range;
# they share |y| < 1.5, z 147.5..150, x 82..100 (wider lower down): well over 0.5 mm3.
@pytest.mark.parametrize("layout,extra", [("conventional", {}), ("t", {"fin_x_le": 40})])
def test_overlap_removed(layout, extra):
    rud = one(layout=layout, part="rudder", **extra)
    assert overlap(one(layout=layout, part="elevator", **extra), rud) > 0.5
    assert overlap(one(layout=layout, part="elevator", elevator_fin_gap=1.0, **extra), rud) < 1e-6


def test_h_layout_gap_volume():
    m = one(layout="h", part="elevator", elevator_fin_gap=1.0)
    assert abs(m.volume) == pytest.approx(17476, rel=1e-3)
    assert overlap(m, one(layout="h", part="rudder")) < 1e-6


def test_gap_checks():
    def msgs(**kw):
        return validate_params(get("tail_surfaces"), {**COMMON, **kw})
    assert any("elevator_fin_gap" in str(x) for x in msgs(elevator_fin_gap=200))
    assert any("elevator_fin_gap" in str(x) for x in msgs(layout="v", elevator_fin_gap=1.0))
    assert any("elevator_fin_gap" in str(x) for x in msgs(elevator_fin_gap=-1))
    assert not any("elevator_fin_gap" in str(x) for x in msgs(layout="conventional", elevator_fin_gap=1.0))


@pytest.mark.parametrize("part", ["full", "fixed", "rudder"])
def test_other_parts_ignore_the_gap(part):
    a = abs(one(layout="conventional", part=part).volume)
    b = abs(one(layout="conventional", part=part, elevator_fin_gap=1.0).volume)
    assert b == pytest.approx(a, rel=1e-12)
