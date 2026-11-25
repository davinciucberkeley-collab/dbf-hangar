"""U13.4-2: T6 warns when a servo drives no mechanism."""
import copy
from pathlib import Path

from hangar.checks import validate
from hangar.design import Design, load_design

FIX = Path(__file__).parent / "fixtures" / "mechanism-recipe"
BASE = load_design(FIX / "plane.yaml").data
PFX = "T6.servo_undriven"


def rows(data):
    d = Design(data=copy.deepcopy(data), path=FIX / "plane.yaml")
    card = validate(d)
    return [(r.check_id, r.status, r.message) for t in card.tiers for r in t.results]


def _no_mech():
    data = copy.deepcopy(BASE)
    del data["mechanisms"]
    return data


def test_driven_servo_has_no_warning():
    assert not [r for r in rows(BASE) if r[0].startswith(PFX)]


def test_servo_without_mechanism_warns():
    rs = rows(_no_mech())
    by_id = {r[0]: r for r in rs}
    r = by_id[f"{PFX}.servo"]
    assert r[1] == "WARN"
    assert "not the driver of any mechanism" in r[2] and "docs/mechanisms.md" in r[2]
    assert "T6.undriven.stab-elev" in by_id and "T6.undriven.servo-arm" in by_id


def test_second_idle_servo():
    data = copy.deepcopy(BASE)
    data["components"].append({"id": "servo2", "type": "servo",
        "geometry": {"generator": "plate", "params": {"plane": "xy", "size": [23, 24], "thickness": 11.5}},
        "position": [20, 60, -8.75], "mass_g": 12, "manufacturing": {"method": "purchased"}})
    data["attachments"].append({"id": "stab-servo2", "parent": "stab", "child": "servo2",
        "method": "glued", "location": [20, 60, -3], "embed_ok": True, "rated_load_n": 10})
    ids = [r[0] for r in rows(data) if r[0].startswith(PFX)]
    assert ids == [f"{PFX}.servo2"]
    assert [r[1] for r in rows(data) if r[0] == f"{PFX}.servo2"] == ["WARN"]


def test_tier6_appears_for_a_servo_only_design():
    data = _no_mech()
    for a in data["attachments"]:
        if a["id"] in ("stab-elev", "servo-arm"):
            a.pop("articulation", None)
        if a["id"] == "arm-rod":
            a.pop("kinematic_link", None)
    assert f"{PFX}.servo" in [r[0] for r in rows(data)]


def test_not_applicable_morphologies_get_no_row():
    for morph in ({"lift": "fixed-wing", "vtol_method": "lift-plus-cruise", "tail": "conventional", "propulsion_count": 1},
                  {"lift": "flying-wing", "vtol_method": "tailsitter", "tail": "none", "propulsion_count": 1}):
        data = _no_mech()
        data["morphology"] = morph
        assert not [r for r in rows(data) if r[0].startswith(PFX)]


def test_servo_that_drives_via_a_different_parent_still_counts_by_driver_parent():
    data = copy.deepcopy(BASE)
    for c in data["components"]:
        if c["id"] == "servo":
            c["id"] = "servo-b"
    for a in data["attachments"]:
        for k in ("parent", "child"):
            if a[k] == "servo":
                a[k] = "servo-b"
    assert not [r for r in rows(data) if r[0].startswith(PFX)]
