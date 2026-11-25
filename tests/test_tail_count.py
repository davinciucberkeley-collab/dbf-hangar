"""U13.6-1: a stabiliser split into fixed, elevator and rudder components counts once in tier 3."""
import copy
from pathlib import Path

import pytest

from hangar.checks import validate
from hangar.design import Design, load_design
from hangar.geom.planform import generated_planform

FIX = Path(__file__).parent / "fixtures" / "derived-planform"
BASE = load_design(FIX).data


def rows(data):
    d = Design(data=copy.deepcopy(data), path=FIX / "plane.yaml")
    card = validate(d)
    return {r.check_id: r for tier in card.tiers for r in tier.results}


def _comp(data, cid):
    return next(c for c in data["components"] if c["id"] == cid)


def split_tail(data):
    d = copy.deepcopy(data)
    tail = _comp(d, "tail")
    tail["geometry"]["params"]["part"] = "fixed"
    for cid, part, mass in (("elevator", "elevator", 4), ("rudder", "rudder", 3)):
        c = copy.deepcopy(tail)
        c["id"] = cid
        c["geometry"]["params"]["part"] = part
        c["mass_g"] = mass
        c["manufacturing"] = {"method": "foamboard"}
        d["components"].append(c)
    return d


def x_np(data):
    return rows(data)["T3.static_margin"].data["x_np_mm"]


def test_single_tail_value():
    assert x_np(BASE) == pytest.approx(284.6, abs=3.0)


def test_split_tail_counts_once():
    x = x_np(split_tail(BASE))
    assert x == pytest.approx(284.6, abs=3.0)
    assert x == pytest.approx(x_np(BASE), abs=0.05)


def test_elevator_only_counts():
    d = copy.deepcopy(BASE)
    _comp(d, "tail")["geometry"]["params"]["part"] = "elevator"
    assert x_np(d) == pytest.approx(284.6, abs=3.0)


def test_rudder_alone_counts_nothing():
    d = copy.deepcopy(BASE)
    _comp(d, "tail")["geometry"]["params"]["part"] = "rudder"
    assert x_np(d) == pytest.approx(242.9, abs=3.0)


def test_two_different_tails_both_count():
    d = copy.deepcopy(BASE)
    c = copy.deepcopy(_comp(d, "tail"))
    c["id"] = "canard"
    c["position"] = [0, 0, 0]
    c["geometry"]["params"]["stab_x_le"] = 20
    d["components"].append(c)
    assert len(rows(d)["T3.static_margin"].data["surfaces"]) == 3


def test_surfaces_data():
    s = {e["id"]: e for e in rows(BASE)["T3.static_margin"].data["surfaces"]}
    assert sorted(s) == ["tail", "wing"]
    assert s["tail"]["source"] == "derived"
    assert s["tail"]["area_mm2"] == 42000.0
    assert s["wing"]["source"] == "measured"
    assert s["wing"]["area_mm2"] == pytest.approx(204000, rel=0.01)


def test_generated_planform_rudder_is_none():
    t = copy.deepcopy(_comp(BASE, "tail"))
    for part, want in (("rudder", False), ("fixed", True), ("elevator", True)):
        t["geometry"]["params"]["part"] = part
        gp = generated_planform(t)
        assert (gp is not None and "lifting_surface" in gp) is want
        if not want:
            assert gp is None
