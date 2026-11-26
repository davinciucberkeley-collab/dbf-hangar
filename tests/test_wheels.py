import copy
import math

import numpy as np
import pytest
from pathlib import Path

from hangar.checks import validate
from hangar.design import Design, load_design
from hangar.geom.registry import get, validate_params
from hangar.index import mechanism_sweeps
from test_generators import build, vol

FIX = Path(__file__).parent / "fixtures" / "wheels"
RECIPE = Path(__file__).parent / "fixtures" / "mechanism-recipe"
ROOT = Path(__file__).parent.parent
G = {"layout": "tricycle", "main_x": 100, "track": 200, "attach_z": 0, "ground_z": -100, "wheel_d": 60, "wheel_w": 20,
     "leg_d": 6, "front_x": 20, "front_wheel_d": 40, "front_attach_z": 0, "wheel_shape": "disc"}


def rows(data, base=FIX):
    d = Design(data=copy.deepcopy(data), path=base / "plane.yaml")
    return [(r.check_id, r.status, r.message) for t in validate(d).tiers for r in t.results]


def fix():
    return load_design(FIX / "plane.yaml")


def test_merged_is_bit_identical():
    a = build("landing_gear", G)[0].vertices
    b = build("landing_gear", {**G, "wheels": "merged"})[0].vertices
    assert np.array_equal(a, b)


def test_separate_has_no_wheels():
    sep = build("landing_gear", {**G, "wheels": "separate", "axle_d": 3})
    assert len(sep) == 1 and sep[0].is_watertight
    b = sep[0].bounds
    assert b[0][1] == pytest.approx(-111, abs=0.2) and b[1][1] == pytest.approx(111, abs=0.2)
    assert b[0][0] == pytest.approx(17, abs=0.2) and b[1][0] == pytest.approx(103, abs=0.2)
    assert b[0][2] > -90
    mb = build("landing_gear", G)[0].bounds
    assert mb[0][1] == pytest.approx(-110, abs=0.2) and mb[1][1] == pytest.approx(110, abs=0.2)
    assert mb[0][2] == pytest.approx(-100, abs=0.5)


def test_separate_needs_one_main_wheel():
    msgs = validate_params(get("landing_gear"), {**G, "wheels": "separate", "main_wheels": 2, "wheel_pitch": 80})
    assert any("wheels: separate" in m for m in msgs)


def test_wheel_volume_and_bore():
    w = build("wheel", {"wheel_d": 60, "wheel_w": 20, "shape": "disc"})[0]
    assert w.is_watertight and vol(w) == pytest.approx(math.pi * 900 * 20, rel=5e-3)
    wb = build("wheel", {"wheel_d": 60, "wheel_w": 20, "shape": "disc", "bore_d": 3.4})[0]
    assert vol(w) - vol(wb) == pytest.approx(math.pi * 1.7 ** 2 * 20, rel=0.05)
    assert wb.bounds[0][1] == pytest.approx(-10, abs=1e-6) and wb.bounds[1][1] == pytest.approx(10, abs=1e-6)
    assert wb.bounds[0][2] == pytest.approx(-30, abs=0.2) and wb.bounds[1][2] == pytest.approx(30, abs=0.2)
    assert build("wheel", {"wheel_d": 60, "wheel_w": 20, "shape": "tyre", "bore_d": 0})[0].is_watertight
    msgs = validate_params(get("wheel"), {"wheel_d": 60, "wheel_w": 20, "bore_d": 40})
    assert any("bore_d" in m for m in msgs)


def test_fixture_t1_passes():
    rs = rows(fix().data)
    assert not [r for r in rs if r[1] == "FAIL" and r[0].startswith(("T0", "T1"))]
    for w in ("gear-wheel-r", "gear-wheel-l", "gear-wheel-n"):
        assert any(r[0] == "T1.attachment" and r[1] == "PASS" and r[2].startswith(w + ":") for r in rs), w
        assert any(r[0] == "T1.articulation" and r[1] == "PASS" and r[2].startswith(w + ":") and "continuous" in r[2]
                   for r in rs), w
    for r in rs:
        assert "range min of gear-wheel" not in r[2] and "sweep gear-wheel" not in r[2]


def test_displaced_nose_wheel_fails_contact():
    data = copy.deepcopy(fix().data)
    next(c for c in data["components"] if c["id"] == "gear")["geometry"]["params"]["front_x"] = 50
    rs = rows(data)
    fails = [r for r in rs if r[0] == "T1.attachment_contact" and r[1] == "FAIL"]
    assert any(r[2].startswith("gear-wheel-n:") for r in fails)
    assert not any(r[2].startswith(("gear-wheel-r:", "gear-wheel-l:")) for r in fails)


def test_continuous_is_not_a_driver():
    data = copy.deepcopy(fix().data)
    assert not any(r[0] == "T6.undriven.gear-wheel-r" for r in rows(data))
    data["mechanisms"] = [{"id": "bad", "driver": "gear-wheel-r", "driven": ["gear-wheel-r"]}]
    rs = rows(data)
    assert any(r[0] == "T6.mechanism.bad" and r[1] == "FAIL" and "continuous joint" in r[2] for r in rs)


def test_spin_sweeps():
    sw = mechanism_sweeps(fix())
    mechs = {m["id"]: m for m in sw["mechanisms"]}
    assert set(mechs) == {"spin-gear-wheel-r", "spin-gear-wheel-l", "spin-gear-wheel-n"}
    for m in mechs.values():
        assert m["input_range_deg"] == [0, 360] and len(m["steps"]) == 361
    t = np.array(mechs["spin-gear-wheel-r"]["steps"][90]["transforms"]["wheel-r"]).reshape(4, 4)
    assert (t @ [100, 100, -40, 1])[:3] == pytest.approx([130, 100, -70], abs=1e-6)
    assert (t @ [100, 100, -70, 1])[:3] == pytest.approx([100, 100, -70], abs=1e-6)


def test_version_gate_and_schema():
    data = copy.deepcopy(fix().data)
    data["schema_version"] = "1.2"
    assert any(r[0] == "T0.version" and r[1] == "FAIL" and "continuous" in r[2] for r in rows(data))
    data = copy.deepcopy(fix().data)
    data["attachments"][1]["articulation"]["range_deg"] = [-5, 5]
    assert any(r[0] == "T0.schema" and r[1] == "FAIL" for r in rows(data))
    data = copy.deepcopy(fix().data)
    data["attachments"][1]["articulation"]["type"] = "revolute"
    assert any(r[0] == "T0.schema" and r[1] == "FAIL" for r in rows(data))
    assert "continuous" in (ROOT / "docs" / "pdl" / "reference.md").read_text(encoding="utf-8")


def test_existing_revolute_rows_unchanged():
    rs = rows(load_design(RECIPE / "plane.yaml").data, RECIPE)
    r = next(r for r in rs if r[0] == "T1.articulation" and r[2].startswith("stab-elev:"))
    assert r[1] == "PASS" and "revolute, range [-25°, 25°]" in r[2]
