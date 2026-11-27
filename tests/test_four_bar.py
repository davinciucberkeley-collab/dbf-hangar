import copy

import numpy as np
import pytest
from pathlib import Path

from hangar.checks import validate
from hangar.design import Design, load_design
from hangar.gates.mechanisms import consistent_four_bar_pose, solve_four_bar, transmission_angle_deg, rod_transform, simulate_mechanism
from hangar.index import mechanism_sweeps, dumps

FIX = Path(__file__).parent / "fixtures" / "four-bar"
RECIPE = Path(__file__).parent / "fixtures" / "mechanism-recipe"
ROOT = Path(__file__).parent.parent

A = {"axis": [0, 1, 0], "pivot": [0, 0, 0]}
B = {"axis": [0, 1, 0], "pivot": [40, 0, 0]}
TIP0 = np.array([0, 0, 10.0])


def rows(data, base):
    d = Design(data=copy.deepcopy(data), path=base / "plane.yaml")
    return [(r.check_id, r.status, r.message) for t in validate(d).tiers for r in t.results]


def fix():
    return load_design(FIX / "plane.yaml")


def row(rs, cid):
    return next(r for r in rs if r[0] == cid)


def test_parallelogram_follows_one_to_one():
    pin0 = np.array([40, 0, 10.0])
    for a in (-30, -10, 5, 20):
        assert abs(solve_four_bar(TIP0, pin0, A, B, a, (-60, 60)) - a) < 1e-6


def test_unequal_arms():
    pin0 = np.array([40, 0, 20.0])
    for a, want in ((-10, -5.0349), (5, 2.4838), (10, 4.9246), (20, 9.6082)):
        assert abs(solve_four_bar(TIP0, pin0, A, B, a, (-60, 60)) - want) < 2e-3
    assert solve_four_bar(TIP0, pin0, A, B, 0.0, (-60, 60)) == 0.0


def test_no_root_is_none():
    assert solve_four_bar(TIP0, np.array([40, 0, 20.0]), A, B, 10, (-1, 1)) is None


def test_transmission_angle():
    pin = np.array([40, 0, 10.0])
    assert abs(transmission_angle_deg(np.array([40, 0, 0.0]), B, pin) - 90.0) < 1e-9
    assert abs(transmission_angle_deg(np.array([0, 0, 5.0]), B, pin)) < 1e-9
    fol = {"axis": [0, -1, 0], "pivot": [60, 0, 0]}
    mu = transmission_angle_deg(np.array([55, 0, 0.0]), fol, np.array([75, 6, -15.25]))
    assert abs(mu - 45.4735) < 1e-3


def test_rod_transform_pose():
    t = rod_transform(np.zeros(3), np.array([10, 0, 0.0]), np.array([1, 2, 3.0]), np.array([1, 2, 13.0]))
    assert np.allclose(t @ [0, 0, 0, 1], [1, 2, 3, 1], atol=1e-9)
    assert np.allclose(t @ [10, 0, 0, 1], [1, 2, 13, 1], atol=1e-9)
    i = rod_transform(TIP0, np.array([40, 0, 10.0]), TIP0, np.array([40, 0, 10.0]))
    assert np.allclose(i, np.eye(4))


def test_solved_angles_on_the_recipe_layout():
    d = fix()
    sim = simulate_mechanism(d, d.data["mechanisms"][0])
    got = {s["input_deg"]: s["followers"]["stab-elev"] for s in sim["steps"]}
    for inp, want in ((-20, 8.1215), (-10, 4.0154), (0, 0.0), (10, -3.8240), (20, -7.3789)):
        assert abs(got[inp] - want) < 2e-3
    assert abs(got[1] / 1 - (-0.392)) < 0.01


def _T(tf, cid):
    return np.array(tf[cid]).reshape(4, 4) if cid in tf else np.eye(4)


def test_rod_stays_pinned():
    d = fix()
    for s in mechanism_sweeps(d)["mechanisms"][0]["steps"]:
        tf = s["transforms"]
        tip = _T(tf, "rod") @ [20, 6, -15.25, 1]
        pin = _T(tf, "pin") @ [75, 6, -15.25, 1]
        end = _T(tf, "rod") @ [73, 6, -15.25, 1]
        assert abs(np.linalg.norm(pin[:3] - tip[:3]) - 55) < 1e-6
        assert abs(np.linalg.norm(end[:3] - tip[:3]) - 53) < 1e-6
        assert np.linalg.norm(np.cross(end[:3] - tip[:3], pin[:3] - tip[:3])) < 1e-6
    r = load_design(RECIPE / "plane.yaml")
    st = next(s for s in mechanism_sweeps(r)["mechanisms"][0]["steps"] if s["input_deg"] == 20)
    tip = _T(st["transforms"], "rod") @ [20, 6, -15.25, 1]
    pin = _T(st["transforms"], "pin") @ [75, 6, -15.25, 1]
    assert abs(np.linalg.norm(pin[:3] - tip[:3]) - 54.8776) < 1e-3


def test_without_the_field_nothing_changes():
    d = fix()
    data = copy.deepcopy(d.data)
    del data["mechanisms"][0]["kinematics"]
    mine = Design(data=data, path=FIX / "plane.yaml")
    rec = load_design(RECIPE / "plane.yaml")
    t6 = lambda rs: [r for r in rs if r[0].startswith("T6.")]
    assert t6(rows(data, FIX)) == t6(rows(rec.data, RECIPE))
    assert dumps(mechanism_sweeps(mine)).replace("four-bar", "x") == dumps(mechanism_sweeps(rec)).replace("mechanism-recipe", "x")


def test_t6_rows():
    d = fix()
    rs = rows(d.data, FIX)
    m = row(rs, "T6.mechanism.elevator-drive")
    assert m[1] == "PASS" and "four_bar" in m[2]
    assert row(rs, "T6.link.elevator-drive")[1] == "PASS"
    rec = rows(load_design(RECIPE / "plane.yaml").data, RECIPE)
    assert row(rs, "T6.ratio.elevator-drive")[1:] == row(rec, "T6.ratio.elevator-drive")[1:]
    assert row(rs, "T6.ratio.elevator-drive")[1] == "PASS"


def _att(data, aid):
    return next(a for a in data["attachments"] if a["id"] == aid)


def test_jam_is_a_fail():
    data = copy.deepcopy(fix().data)
    _att(data, "stab-elev")["articulation"]["range_deg"] = [-3, 3]
    m = row(rows(data, FIX), "T6.mechanism.elevator-drive")
    assert m[1] == "FAIL" and "four_bar jam at input 8 deg" in m[2]


def test_rod_clash_is_found():
    data = copy.deepcopy(fix().data)
    data["components"].append({"id": "blocker", "type": "other", "geometry": {"box": {"size": [6, 4, 1.5]}},
                               "position": [60, 6, -17.55], "mass_g": 1, "manufacturing": {"method": "foamboard"}})
    m = row(rows(data, FIX), "T6.mechanism.elevator-drive")
    assert m[1] == "FAIL" and "rod and blocker collide at input" in m[2]


def test_two_driven_is_refused():
    data = copy.deepcopy(fix().data)
    data["mechanisms"][0]["driven"] = ["stab-elev", "servo-arm"]
    m = row(rows(data, FIX), "T6.mechanism.elevator-drive")
    assert m[1] == "FAIL" and "four_bar needs exactly one driven attachment" in m[2]


def test_nested_motion_is_refused():
    data = copy.deepcopy(fix().data)
    _att(data, "stab-servo")["articulation"] = {"type": "revolute", "pivot": [20, 0, -3], "axis": [0, 1, 0],
                                                  "range_deg": [-5, 5]}
    m = row(rows(data, FIX), "T6.mechanism.elevator-drive")
    assert m[1] == "FAIL" and "four_bar needs" in m[2] and "not to move with another articulated joint" in m[2]


def test_version_gate():
    data = copy.deepcopy(fix().data)
    data["schema_version"] = "1.2"
    v = [r for r in rows(data, FIX) if r[0] == "T0.version"]
    assert any(r[1] == "FAIL" and "kinematics" in r[2] for r in v)
    rec = rows(load_design(RECIPE / "plane.yaml").data, RECIPE)
    assert not [r for r in rec if r[0] == "T0.version"]
    data = copy.deepcopy(fix().data)
    data["mechanisms"][0]["kinematics"] = "spiral"
    assert any(r[0] == "T0.schema" and r[1] == "FAIL" for r in rows(data, FIX))
    assert "kinematics" in (ROOT / "docs/pdl/reference.md").read_text(encoding="utf-8")
    assert "four_bar" in (ROOT / "docs/mechanisms.md").read_text(encoding="utf-8")
    th = (ROOT / "standards/gate-thresholds.yaml").read_text(encoding="utf-8")
    assert "four_bar_min_transmission_deg" in th and "four_bar_max_follower_step_deg" in th


def test_consistent_pose_hand_values():
    d = fix()
    for given, other, want in (({"servo-arm": 10.0}, "stab-elev", -3.8240),
                               ({"servo-arm": 30.0}, "stab-elev", -10.6048),
                               ({"stab-elev": 5.0}, "servo-arm", -12.4075)):
        ang, ov = consistent_four_bar_pose(d, given)
        assert abs(ang[other] - want) < 5e-3
        for k, v in given.items():
            assert ang[k] == v
        assert set(ov) == {"rod"}
        tip = ov["rod"] @ [20, 6, -15.25, 1]
        end = ov["rod"] @ [73, 6, -15.25, 1]
        assert abs(np.linalg.norm(end[:3] - tip[:3]) - 53) < 1e-6


def test_consistent_pose_leaves_other_cases_alone():
    d = fix()
    assert consistent_four_bar_pose(d, {}) == ({}, {})
    assert consistent_four_bar_pose(d, {"stab-elev": 25.0}) == ({"stab-elev": 25.0}, {})
    both = {"servo-arm": 10.0, "stab-elev": 5.0}
    assert consistent_four_bar_pose(d, both) == (both, {})
    data = copy.deepcopy(fix().data)
    del data["mechanisms"][0]["kinematics"]
    d2 = Design(data=data, path=FIX / "plane.yaml")
    assert consistent_four_bar_pose(d2, {"servo-arm": 10.0}) == ({"servo-arm": 10.0}, {})


def test_t1_checks_the_posed_rod():
    rs = rows(fix().data, FIX)
    skips = [r for r in rs if r[0] == "T1.kinematic_link"]
    assert len(skips) == 1 and skips[0][2].startswith("range min of stab-elev")
    assert any(r[0] == "T1.pose" and r[1] == "PASS" and r[2].startswith("sweep stab-elev -10") for r in rs)


def test_t1_posed_rod_clash_is_a_fail():
    data = copy.deepcopy(fix().data)
    data["components"].append({"id": "blocker", "type": "other", "geometry": {"box": {"size": [6, 4, 1.5]}},
                               "position": [60, 6, -17.55], "mass_g": 1, "manufacturing": {"method": "foamboard"}})
    clips = [r for r in rows(data, FIX) if r[0] == "T1.interference" and r[1] == "FAIL" and "rod and blocker" in r[2]]
    assert {r[2].split(":")[0] for r in clips} == {"range max of servo-arm (30\u00b0)", "sweep stab-elev -10\u00b0",
                                                     "sweep servo-arm 15\u00b0"}


@pytest.mark.slow
def test_c172_t1_kinematic_link_rows():
    from hangar.checks import tier1_geometry
    from hangar.design import load_standards
    rs = tier1_geometry(load_design(ROOT / "designs" / "c172-rc"), load_standards()).results
    sk = [r for r in rs if r.check_id == "T1.kinematic_link"]
    assert len(sk) == 6
    assert {r.message.split(":")[0] for r in sk} == {
        "range max of wing-aileron-r (25°)", "range max of wing-aileron-l (25°)",
        "range min of tail-elevator (-30°)", "range min of tail-rudder (-30°)",
        "sweep wing-aileron-r 20°", "sweep wing-aileron-l 20°"}
    assert len([r for r in rs if r.check_id == "T1.pose" and r.status == "PASS"
                and r.message.startswith("sweep wing-aileron-r 5\u00b0")]) == 1
    assert not [r for r in rs if r.status == "FAIL"]
