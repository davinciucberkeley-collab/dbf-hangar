"""T6 mechanism gate (U3.6e): 1-degree sampling with range ends and 0, declared link pairs, ratio checked against the link geometry.

Collision volumes are faked (tests/fixtures/mech-good.yaml plus three boxes); only the sampling and the pair
logic are under test, not the mesh boolean."""
from __future__ import annotations

import copy
import datetime
from pathlib import Path

import pytest
import yaml

import hangar.checks
import hangar.geometry
from hangar.design import FAIL, PASS, SKIP, WARN, Design
from hangar.gates import run_gates

FIX = Path(__file__).parent / "fixtures"
ROW = "T6.mechanism.flap_l"


def _box(cid: str, x: float) -> dict:
    return {"id": cid, "type": "other", "geometry": {"box": {"size": [4, 4, 4]}}, "position": [x, 20, 60], "mass_g": 1}


def make_design(*, link: bool = True, ratio: float = 1.0, input_range=(0, 20), joint_range=(0, 40)) -> Design:
    """mech-good (driver servo_arm -> arm; follower flap_hinge -> flap) plus rod (child of arm, kinematic_link), horn
    (child of flap), blocker (child of wing). link=True declares mechanisms[0].link = arm-rod -> flap-horn.
    The link points are rod (30, 20, 60) and horn (260, 20, 60): levers 60-40 = 20 and 60-46 = 14, ratio 20/14 = 1.43."""
    data = copy.deepcopy(yaml.safe_load((FIX / "mech-good.yaml").read_text(encoding="utf-8")))
    data["components"] += [_box("rod", 30), _box("horn", 260), _box("blocker", 150)]
    data["attachments"] += [
        {"id": "arm-rod", "parent": "arm", "child": "rod", "method": "hinge", "location": [30, 20, 60],
         "rated_load_n": 5, "kinematic_link": True},
        {"id": "flap-horn", "parent": "flap", "child": "horn", "method": "glued", "location": [260, 20, 60],
         "rated_load_n": 5},
        {"id": "wing-blocker", "parent": "wing", "child": "blocker", "method": "glued", "location": [150, 20, 60],
         "rated_load_n": 5},
    ]
    for a in data["attachments"]:
        if a["id"] in ("flap_hinge", "servo_arm"):
            a["articulation"]["range_deg"] = list(joint_range)
    data["mechanisms"][0]["input_range_deg"] = list(input_range)
    data["mechanisms"][0]["expect"][0]["ratio"] = ratio
    if link:
        data["mechanisms"][0]["link"] = {"driver_end": "arm-rod", "follower_end": "flap-horn"}
    return Design(data, path=FIX / "mech-good.yaml")


def run_t6(monkeypatch, design: Design, volume_of):
    """Run tier 6 with fake overlap volumes. volume_of(frozenset({a, b}), driver_deg) -> mm3.
    Returns (T6.mechanism row, driver angles posed in order, {check_id: row} of every T6 row). Rest-pose overlaps are 0."""
    state = {"owner": {}, "rest": set(), "driver": None, "posed": []}
    real_posed = hangar.geometry.posed_component_parts

    def posed(d, angles=None):
        out = real_posed(d, angles)
        for cid, parts in out.items():
            state["owner"][id(parts)] = cid
            if not angles:
                state["rest"].add(id(parts))
        if angles:
            state["driver"] = angles["servo_arm"]
            state["posed"].append(angles["servo_arm"])
        return out

    def overlap(a, b):
        if id(a) in state["rest"] or id(b) in state["rest"]:
            return 0.0
        return volume_of(frozenset((state["owner"][id(a)], state["owner"][id(b)])), state["driver"])

    monkeypatch.setattr(hangar.geometry, "posed_component_parts", posed)
    monkeypatch.setattr(hangar.checks, "_overlap_volume", overlap)
    card = run_gates(design, only_tiers={6}, today=datetime.date(2026, 11, 20))
    rows = {r.check_id: r for t in card.tiers for r in t.results if r.check_id.startswith("T6.")}
    return rows[ROW], state["posed"], rows


def test_one_degree_collision_is_found(monkeypatch):
    # collides only at input 3 deg (1.1 mm3 > the 1.0 limit): off a 5-degree grid
    row, _, _ = run_t6(monkeypatch, make_design(link=False),
                       lambda pair, drv: 1.1 if pair == {"flap", "blocker"} and drv == 3.0 else 0.0)
    assert row.status == FAIL
    assert "flap and blocker collide at input 3 deg" in row.message


def test_declared_link_pair_is_not_counted_and_is_named(monkeypatch):
    row, _, rows = run_t6(monkeypatch, make_design(), lambda pair, drv: 5.0 if pair == {"rod", "horn"} else 0.0)
    assert row.status == PASS
    assert row.data["link_pairs"] == [["horn", "rod"]]
    warn = rows["T6.link.flap_l"]
    assert warn.status == WARN and "not checked (pinned by declared link)" in warn.message and "horn & rod" in warn.message


@pytest.mark.parametrize("other", ["blocker", "flap"])
def test_unlinked_pairs_still_count(monkeypatch, other):
    row, _, _ = run_t6(monkeypatch, make_design(), lambda pair, drv: 5.0 if pair == {"rod", other} else 0.0)
    assert row.status == FAIL
    assert f"rod and {other}" in row.message or f"{other} and rod" in row.message


def test_pair_without_link_still_counts(monkeypatch):
    row, _, rows = run_t6(monkeypatch, make_design(link=False), lambda pair, drv: 5.0 if pair == {"rod", "horn"} else 0.0)
    assert row.status == FAIL
    assert "rod and horn" in row.message
    assert row.data["link_pairs"] == []
    assert "T6.link.flap_l" not in rows


def test_link_end_on_the_wrong_side_fails(monkeypatch):
    d = make_design()
    d.data["mechanisms"][0]["link"]["driver_end"] = "wing-blocker"  # not kinematic_link, not on the driver side
    row, _, _ = run_t6(monkeypatch, d, lambda pair, drv: 0.0)
    assert row.status == FAIL and "link.driver_end wing-blocker" in row.message
    d = make_design()
    d.data["mechanisms"][0]["link"]["follower_end"] = "wing-blocker"
    row, _, _ = run_t6(monkeypatch, d, lambda pair, drv: 0.0)
    assert row.status == FAIL and "link.follower_end wing-blocker" in row.message


def test_ratio_measured(monkeypatch):
    _, _, rows = run_t6(monkeypatch, make_design(ratio=1.0), lambda pair, drv: 0.0)
    r = rows["T6.ratio.flap_l"]
    assert r.status == FAIL and "declared ratio 1" in r.message and "1.429" in r.message
    _, _, rows = run_t6(monkeypatch, make_design(ratio=1.43), lambda pair, drv: 0.0)
    r = rows["T6.ratio.flap_l"]
    assert r.status == PASS and r.data["ratios"]["flap_hinge"]["geometric"] == 1.4286


def test_ratio_skips_without_link(monkeypatch):
    _, _, rows = run_t6(monkeypatch, make_design(link=False), lambda pair, drv: 0.0)
    r = rows["T6.ratio.flap_l"]
    assert r.status == SKIP and "declared, not measured: mechanisms[].link missing" in r.message


def test_range_ends_zero_and_every_degree_are_sampled(monkeypatch):
    row, posed, _ = run_t6(monkeypatch, make_design(link=False, input_range=(-3.5, 7.5), joint_range=(-10, 40)), lambda pair, drv: 0.0)
    assert row.status == PASS
    assert sorted(set(posed)) == [-3.5, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 7.5]
