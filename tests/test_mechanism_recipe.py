"""U13.4-1: the servo, horn and pushrod recipe in docs/mechanisms.md stays verified."""
import copy
from pathlib import Path

from hangar.checks import validate
from hangar.design import Design, load_design

FIX = Path(__file__).parent / "fixtures" / "mechanism-recipe"
DOC = Path(__file__).parent.parent / "docs" / "mechanisms.md"
BASE = load_design(FIX / "plane.yaml").data


def rows(data):
    d = Design(data=copy.deepcopy(data), path=FIX / "plane.yaml")
    card = validate(d)
    return [(r.check_id, r.status, r.message) for t in card.tiers for r in t.results]


def test_recipe_has_no_failures_in_tiers_0_1_6():
    bad = [r for r in rows(BASE)
           if r[0].startswith(("T0", "T1", "T6")) and r[1] == "FAIL"]
    assert bad == []


def test_t6_rows_pass():
    by_id = {r[0]: r for r in rows(BASE)}
    assert by_id["T6.mechanism.elevator-drive"][1] == "PASS"
    ratio = by_id["T6.ratio.elevator-drive"]
    assert ratio[1] == "PASS"
    assert "-0.393" in ratio[2]


def test_wrong_ratio_is_caught():
    data = copy.deepcopy(BASE)
    data["mechanisms"][0]["expect"][0]["ratio"] = -1.2
    by_id = {r[0]: r for r in rows(data)}
    assert by_id["T6.ratio.elevator-drive"][1] == "FAIL"


def test_rod_attached_at_both_ends_is_refused():
    data = copy.deepcopy(BASE)
    data["attachments"].append({"id": "horn-rod", "parent": "horn", "child": "rod",
                                "method": "hinge", "location": [73, 6, -15.25],
                                "embed_ok": True, "rated_load_n": 10})
    hits = [r for r in rows(data) if r[0].startswith("T1.articulation") and r[1] == "FAIL"]
    assert hits, "expected a T1.articulation FAIL"
    assert any("loop" in r[2] for r in hits)


def test_doc_mentions_what_the_fixture_uses():
    text = DOC.read_text(encoding="utf-8")
    for needle in ["kinematic_link: true", "link: {driver_end, follower_end}", "T6.ratio",
                   "embed_ok", "strut", "plate", "tests/test_mechanism_recipe.py"]:
        assert needle in text, needle
