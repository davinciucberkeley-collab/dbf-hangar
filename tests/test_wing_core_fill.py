"""U13.7-7 (T145): wing_panel core_fill keeps the core full-chord outside the elevon span."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from hangar.geom import registry
from hangar.geom.registry import get, validate_params
from hangar.geometry import strip_planform

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
DAT = "airfoils/diamond.dat"
ROOT = Path(__file__).resolve().parent.parent


def build(name, params, base=FIXTURE_DIR):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, base)


def wing(**kw):
    p = {"airfoil_file": DAT, "span": 400, "root_chord": 100, "tip_chord": 100, "part": "core", "hinge_frac": 0.75}
    p.update(kw)
    return p


def vol(m):
    return abs(float(m.volume))


def _core(**kw):
    return build("wing_panel", wing(tip_chord=50, elevon_y=[50, 150], **kw))


def test_default_is_bit_identical():
    a = _core()
    b = _core(core_fill="off")
    assert np.array_equal(a[0].vertices, b[0].vertices)
    assert vol(a[0]) == pytest.approx(102083.33, rel=1e-6)


def test_core_fill_volume():
    parts = _core(core_fill="outside")
    assert len(parts) == 1 and parts[0].is_watertight
    assert vol(parts[0]) == pytest.approx(109570.3, rel=1e-4)


def test_core_fill_plus_elevons_equal_the_full_wing():
    core = vol(_core(core_fill="outside")[0])
    el = build("wing_panel", wing(tip_chord=50, hinge_frac=0.75, part="elevon", elevon_y=[50, 150]))
    full = build("wing_panel", wing(tip_chord=50, part="full"))
    assert core + sum(vol(m) for m in el) == pytest.approx(vol(full[0]), rel=1e-4)
    assert vol(full[0]) == pytest.approx(116666.7, rel=1e-4)


def test_core_fill_bounds():
    assert _core(core_fill="outside")[0].bounds[1][0] == pytest.approx(100.0, abs=1e-6)
    assert _core()[0].bounds[1][0] == pytest.approx(75.0, abs=1e-6)


def test_core_fill_with_sweep_dihedral_and_inboard():
    ref = vol(_core(core_fill="outside")[0])
    m = _core(core_fill="outside", sweep_le_deg=10, dihedral_deg=3)
    assert len(m) == 1 and m[0].is_watertight
    assert vol(m[0]) == pytest.approx(ref, rel=1e-4)
    for ib in (100, 30):
        m = _core(core_fill="outside", inboard_span=ib)
        assert len(m) == 1 and m[0].is_watertight


def test_planform_area_is_complete_with_fill():
    def owners(**kw):
        return {
            "w": build("wing_panel", wing(tip_chord=50, elevon_y=[50, 150], **kw)),
            "r": build("wing_panel", wing(tip_chord=50, part="elevon", side="right", elevon_y=[50, 150])),
            "l": build("wing_panel", wing(tip_chord=50, part="elevon", side="left", elevon_y=[50, 150])),
        }
    kw = dict(n=41, gap_tol=3.0, control_frac=0.15)
    assert strip_planform(owners(core_fill="outside"), "w", **kw)["area_mm2"] == pytest.approx(30000, rel=0.01)
    assert strip_planform(owners(), "w", **kw)["area_mm2"] == pytest.approx(26250, rel=0.01)


def _msgs(p):
    return [m for m in validate_params(get("wing_panel"), p) if "core_fill" in str(m)]


def test_core_fill_checks():
    assert _msgs(wing(core_fill="outside"))
    assert _msgs(wing(part="full", elevon_y=[50, 150], core_fill="outside"))
    assert _msgs(wing(elevon_y=[150, 50], core_fill="outside"))
    assert not _msgs(wing(elevon_y=[50, 150], core_fill="outside"))


def test_doc_section():
    t = (ROOT / "docs" / "mechanisms.md").read_text(encoding="utf-8")
    for s in ("## Splitting a wing into core and ailerons", "core_fill: outside", "158,130", "192,514"):
        assert s in t
