"""U4.37-1: tier 3 reads generated wing_panel wings and tail_surfaces tails without a declared planform."""
import copy
import math
from pathlib import Path

import pytest

from hangar.checks import G, RHO_DEFAULT, validate
from hangar.design import Design, load_design
from hangar.geom.planform import generated_planform
from hangar.geometry import lifting_surface_properties

FIX = Path(__file__).parent / "fixtures" / "derived-planform"
BASE = load_design(FIX).data


def rows(data):
    d = Design(data=copy.deepcopy(data), path=FIX / "plane.yaml")
    card = validate(d)
    return {r.check_id: r for tier in card.tiers for r in tier.results}


def _comp(data, cid):
    return next(c for c in data["components"] if c["id"] == cid)


def test_wing_and_tail_are_seen():
    r = rows(BASE)
    assert r["T3.stall"].status == "PASS"
    assert "T3.static_margin" in r
    want = math.sqrt(2 * 0.610 * G / (RHO_DEFAULT * 0.204 * 1.2))
    assert r["T3.stall"].data["stall_mps"] == pytest.approx(want, rel=0.01)


def test_tail_moves_the_neutral_point_aft():
    d = copy.deepcopy(BASE)
    d["components"] = [c for c in d["components"] if c["id"] != "tail"]
    d["attachments"] = [a for a in d["attachments"] if a["id"] != "tail-fuse"]
    wing_only = rows(d)["T3.static_margin"].data["x_np_mm"]
    x_np = rows(BASE)["T3.static_margin"].data["x_np_mm"]
    assert wing_only == pytest.approx(242.9, abs=3.0)
    assert x_np > wing_only + 20
    assert x_np < 776.4


def test_generated_planform_function():
    wing, tail, fus = (_comp(BASE, i) for i in ("wing", "tail", "fuselage"))
    assert generated_planform(wing) == {"measured": True}
    res = generated_planform(tail)
    assert res["lifting_surface"] == {"span": 400, "root_chord": 120, "tip_chord": 90,
                                      "sweep_le_deg": 0.0, "mirrored": True}
    assert res["offset"] == [0.0, 0.0, 0.0]
    assert generated_planform(fus) is None
    w = copy.deepcopy(wing)
    w["geometry"]["params"]["side"] = "right"
    assert generated_planform(w) is None
    w = copy.deepcopy(wing)
    w["geometry"]["params"].update({"part": "elevon", "elevon_y": [50, 150]})
    assert generated_planform(w) is None
    w = copy.deepcopy(wing)
    w["type"] = "other"
    assert generated_planform(w) is None


def test_unrelated_wing_side_still_fails_as_before():
    d = copy.deepcopy(BASE)
    _comp(d, "wing")["geometry"]["params"]["side"] = "right"
    # the tail is now derived and would be the only lifting surface; drop it so that nothing is derived
    d["components"] = [c for c in d["components"] if c["id"] != "tail"]
    d["attachments"] = [a for a in d["attachments"] if a["id"] != "tail-fuse"]
    r = rows(d)["T3.stall"]
    assert r.status == "FAIL"
    assert "no lifting surface found" in r.message


def test_declared_planform_still_wins():
    d = copy.deepcopy(BASE)
    _comp(d, "wing")["planform"] = {"lifting_surface": {"span": 1200, "root_chord": 200, "tip_chord": 140},
                                    "origin": [200, 0, 0]}
    r = rows(d)
    assert r["T3.stall"].status == "PASS"
    assert "T3.planform_matches_geometry" in r


def test_measured_equals_analytic_area():
    p = lifting_surface_properties({"geometry": {"lifting_surface": {"span": 1200, "root_chord": 200, "tip_chord": 140}},
                                    "position": [200, 0, 0]}, None)
    want = math.sqrt(2 * 0.610 * G / (RHO_DEFAULT * p["area_mm2"] / 1e6 * 1.2))
    got = rows(BASE)["T3.stall"].data["stall_mps"]
    assert got == pytest.approx(want, rel=0.01)
