"""U4.39-3: T1 warns when a part touches no other part (conventional designs only)."""
import copy
from pathlib import Path

from hangar.checks import validate
from hangar.design import Design, load_design

FIX = Path(__file__).parent / "fixtures" / "mechanism-recipe"
BASE = load_design(FIX / "plane.yaml").data


def rows(data):
    d = Design(data=copy.deepcopy(data), path=FIX / "plane.yaml")
    card = validate(d)
    return [(r.check_id, r.status, r.message) for t in card.tiers for r in t.results]


def _comp(data, cid):
    return next(c for c in data["components"] if c["id"] == cid)


def _displaced_pin():
    data = copy.deepcopy(BASE)
    _comp(data, "pin")["position"] = [75, 40, -15.25]
    return data


def _floating(data):
    return [r for r in rows(data) if r[0].startswith("T1.floating")]


def test_recipe_has_no_floating_part():
    assert _floating(BASE) == []


def test_displaced_pin_floats():
    hits = _floating(_displaced_pin())
    assert [h[0] for h in hits] == ["T1.floating.pin"]
    assert hits[0][1] == "WARN"
    assert "touches no other part" in hits[0][2] and "nearest:" in hits[0][2]


def test_link_only_part_far_away_floats():
    data = copy.deepcopy(BASE)
    p = _comp(data, "rod")["geometry"]["params"]
    p["start"] = [20, 6, -45.25]
    p["end"] = [73, 6, -45.25]
    by_id = {r[0]: r for r in rows(data)}
    assert by_id["T1.floating.rod"][1] == "WARN"


def test_not_conventional_gets_no_row():
    data = _displaced_pin()
    data["morphology"] = {"lift": "flying-wing", "vtol_method": "tailsitter", "tail": "none",
                          "propulsion_count": 1}
    assert _floating(data) == []


def test_lonely_design():
    data = copy.deepcopy(BASE)
    data["components"] = [c for c in data["components"] if c["id"] == "stab"]
    data["attachments"] = []
    data["mechanisms"] = []
    hits = {r[0]: r for r in rows(data)}
    assert hits["T1.floating.stab"][1] == "WARN"
    assert "no other part" in hits["T1.floating.stab"][2]
