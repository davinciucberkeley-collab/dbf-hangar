"""U4.30-2: fixed-wing standards and the checks that read them (conventional designs only)."""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

from hangar.design import FAIL, PASS, REPO_ROOT, SKIP, WARN, Design
from test_discipline_gates import rows, run

FIX = Path(__file__).parent / "fixtures"


def fw(**req) -> Design:
    d = copy.deepcopy(yaml.safe_load((FIX / "gates-base.yaml").read_text(encoding="utf-8")))
    for item in d["bom"]["items"]:
        item["verified"]["date"] = "2026-11-15"
    d["morphology"] = {"lift": "fixed-wing", "vtol_method": "none"}
    d["requirements"]["cruise_speed_mps"] = req.get("cruise", 18)
    return Design(d, path=FIX / "gates-base.yaml")


def one(design, cid):
    rs = rows(run(design, tiers={3}), cid)
    assert len(rs) == 1, rs
    return rs[0]


def test_wing_loading_pass():
    r = one(fw(), "T3.wing_loading")
    assert r.status == PASS and "within 100.0" in r.message
    stall = one(fw(), "T3.stall")
    mass = sum(c.get("mass_g", 0) for c in fw().data["components"])
    assert abs(stall.data["wing_loading_g_dm2"] - mass / 20.0) <= 1


def test_wing_loading_warn_when_pending():
    d = fw()
    d.component("battery")["mass_g"] = 2500
    r = one(d, "T3.wing_loading")
    assert r.status == WARN and r.message.endswith("pending") and r.data["band"] == "above"


def test_cruise_stall_ratio_fail():
    assert one(fw(cruise=8), "T3.cruise_stall_ratio").status == FAIL
    stall = one(fw(), "T3.stall").data["stall_mps"]
    r = one(fw(), "T3.cruise_stall_ratio")
    assert r.status == (PASS if 18 / stall >= 1.3 else FAIL)


def _vtol():
    d = fw()
    d.data["morphology"] = {"lift": "flying-wing", "vtol_method": "tailsitter"}
    return d


def test_static_margin_band_for_conventional():
    assert one(fw(), "T3.static_margin").criterion == "fixed-wing.yaml#fw_static_margin_min"
    assert one(_vtol(), "T3.static_margin").criterion == "design-standards.yaml#static_margin"


def test_not_applicable_for_vtol():
    card = run(_vtol(), tiers={3})
    for cid in ("T3.wing_loading", "T3.cruise_stall_ratio"):
        r = rows(card, cid)[0]
        assert r.status == SKIP and r.data["not_applicable"] is True


def test_new_keys_all_have_source():
    data = yaml.safe_load((REPO_ROOT / "standards" / "fixed-wing.yaml").read_text(encoding="utf-8"))
    assert all("source" in v for k, v in data.items() if k != "version")


def test_accepted_ignores_not_applicable_skip():
    from hangar.design import Scorecard, TierReport, CheckResult
    ok = CheckResult("A.x", PASS, "ok", "c")
    na = CheckResult("A.y", SKIP, "na", "c", {"not_applicable": True})
    assert Scorecard("d", [TierReport(0, "t", [ok, na])]).accepted
    assert not Scorecard("d", [TierReport(0, "t", [ok, CheckResult("A.z", SKIP, "s", "c")])]).accepted
