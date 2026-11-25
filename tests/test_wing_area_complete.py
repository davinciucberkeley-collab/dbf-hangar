"""U13.7-8: tier 3 warns when a core wing leaves part of the planform uncovered."""
import copy
from pathlib import Path

import pytest

from hangar.checks import validate
from hangar.design import Design, load_design
from hangar.gates.fidelity import resolve_threshold

FIX = Path(__file__).parent / "fixtures" / "derived-planform"
BASE = load_design(FIX).data
ROOT = Path(__file__).resolve().parents[1]
ID = "T3.wing_area_complete"


def rows(data):
    d = Design(data=copy.deepcopy(data), path=FIX / "plane.yaml")
    card = validate(d)
    return {r.check_id: r for tier in card.tiers for r in tier.results}


def _wing(data):
    return next(c for c in data["components"] if c["id"] == "wing")


def core_wing(data, **extra):
    d = copy.deepcopy(data)
    _wing(d)["geometry"]["params"].update({"part": "core", "hinge_frac": 0.75, "elevon_y": [200, 400], **extra})
    return d


def with_ailerons(data):
    d = copy.deepcopy(data)
    wing = _wing(d)
    for suffix, side, hid, loc in (("r", "right", "r-hinge", [400, 300, 40]), ("l", "left", "l-hinge", [400, -300, 40])):
        c = copy.deepcopy(wing)
        c["id"] = f"aileron-{suffix}"
        c["geometry"]["params"].pop("core_fill", None)  # core_fill belongs on the core only
        c["geometry"]["params"].update({"part": "elevon", "side": side})
        c["mass_g"] = 3
        d["components"].append(c)
        axis = [0, -1, 0]
        d["attachments"].append({"id": hid, "parent": "wing", "child": c["id"], "method": "hinge", "location": loc,
                                 "rated_load_n": 5,
                                 "articulation": {"type": "revolute", "pivot": loc, "axis": axis,
                                                  "range_deg": [-20, 20]}})
    return d


def test_full_wing_gets_no_row():
    assert ID not in rows(BASE)


def test_core_only_warns():
    r = rows(core_wing(BASE))[ID]
    assert r.status == "WARN"
    assert r.data["analytic_mm2"] == pytest.approx(204000, rel=1e-6)
    assert r.data["ratio"] == pytest.approx(0.75, abs=0.01)
    assert "core_fill: outside" in r.message


def test_ailerons_without_fill_still_warn():
    r = rows(with_ailerons(core_wing(BASE)))[ID]
    assert r.status == "WARN"
    assert r.data["ratio"] == pytest.approx(0.8333, abs=0.01)


def test_fill_without_ailerons_warns():
    r = rows(core_wing(BASE, core_fill="outside"))[ID]
    assert r.status == "WARN"
    assert r.data["ratio"] == pytest.approx(0.9167, abs=0.01)


def test_fill_and_ailerons_pass():
    r = rows(with_ailerons(core_wing(BASE, core_fill="outside")))[ID]
    assert r.status == "PASS"
    assert r.data["ratio"] == pytest.approx(1.0, abs=0.01)


def test_aileron_pieces_are_not_separate_surfaces():
    r = rows(with_ailerons(core_wing(BASE, core_fill="outside")))["T3.static_margin"]
    assert {s["id"] for s in r.data["surfaces"]} == {"wing", "tail"}
    assert r.data["x_np_mm"] == pytest.approx(rows(BASE)["T3.static_margin"].data["x_np_mm"], abs=1.0)


def test_threshold_entry():
    t = resolve_threshold("gate-thresholds.yaml#wing_area_complete_min")
    assert t["value"] == 0.97
    assert t["source"] == "pending"


def test_declared_planform_wings_get_no_row():
    d = core_wing(BASE)
    _wing(d)["planform"] = {"lifting_surface": {"span": 1200, "root_chord": 200, "tip_chord": 140},
                            "origin": [200, 0, 0]}
    assert ID not in rows(d)


def test_doc_sentence():
    assert "T3.wing_area_complete" in (ROOT / "docs" / "mechanisms.md").read_text(encoding="utf-8")
