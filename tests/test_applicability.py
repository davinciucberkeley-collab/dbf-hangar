"""U12.1-1: applicability from morphology; not-applicable SKIP rows stay out of baselines."""
from __future__ import annotations

import copy
import datetime
from pathlib import Path

import yaml

from hangar.baseline import snapshot
from hangar.design import SKIP, Design
from hangar.gates import run_gates
from hangar.gates.applicability import NEEDS, load_table
from tests.test_discipline_gates import vtol

FIX = Path(__file__).parent / "fixtures"
TODAY = datetime.date(2026, 11, 20)
IDS = ("T2.hover_moment", "T3.hover_tw", "T3.control_authority", "T3.transition_margin")


def fixed_wing() -> Design:
    d = copy.deepcopy(yaml.safe_load((FIX / "gates-base.yaml").read_text(encoding="utf-8")))
    for item in d["bom"]["items"]:
        item["verified"]["date"] = "2026-11-15"
    d["morphology"] = {"lift": "fixed-wing", "vtol_method": "none"}
    return Design(d, path=FIX / "gates-base.yaml")


def card(design):
    return run_gates(design, 9, strict=True, today=TODAY)


def rows(sc, cid):
    return [r for t in sc.tiers for r in t.results if r.check_id == cid]


def test_table_rows_use_known_needs():
    assert all(r["needs"] in NEEDS for r in load_table().values())


def test_applicable_values():
    for m, want in [({"lift": "fixed-wing", "vtol_method": "none"}, (False, False, True, True)),
                    ({"lift": "flying-wing", "vtol_method": "tailsitter"}, (True, True, True, False)),
                    ({"lift": "multirotor", "vtol_method": "none"}, (True, False, False, False))]:
        got = tuple(NEEDS[k](m) for k in ("hovers", "transitions", "winged", "conventional"))
        assert got == want


def test_fixed_wing_gets_not_applicable_rows():
    sc = card(fixed_wing())
    for cid in IDS:
        rs = rows(sc, cid)
        assert rs, cid
        for r in rs:
            assert r.status == SKIP and r.message.startswith("not applicable:") and r.data["not_applicable"] is True


def test_not_applicable_stays_skip_in_report_only_mode():
    sc = run_gates(fixed_wing(), 9, today=TODAY)
    for cid in IDS:
        rs = rows(sc, cid)
        assert rs and all(r.status == SKIP and r.message.startswith("not applicable:") for r in rs), cid


def test_vtol_design_unchanged():
    sc = card(vtol())
    for cid in IDS:
        assert not any((r.data or {}).get("not_applicable") for r in rows(sc, cid))


def test_baseline_ignores_not_applicable():
    snap = snapshot(card(fixed_wing()))
    assert not [k for k in snap["known"] if k["check_id"] in IDS]


# ---- not-applicable rows are not results (TierReport.status, accepted, validate_op) ----
def _cr(status, na=False):
    from hangar.design import CheckResult
    return CheckResult("X.y", status, "m", "", {"not_applicable": True} if na else {})


def test_tier_status_ignores_not_applicable_rows():
    from hangar.design import PASS, TierReport
    assert TierReport(3, "t", [_cr(PASS), _cr(SKIP, na=True)]).status == PASS
    assert TierReport(3, "t", [_cr(SKIP, na=True)]).status == SKIP
    assert TierReport(3, "t", [_cr(PASS), _cr(SKIP)]).status == SKIP


def test_design_verdicts_unchanged_against_main():
    """Verdicts are recorded for a pinned date (fixture key _recorded). To regenerate after a standards flip: for each design id in the fixture, run_gates(load_design(DESIGNS_DIR / id), 9, today=<recorded date>) and write {"accepted": sc.accepted, "tiers": {str(t.tier): t.status for t in sc.tiers}}; review the diff by hand."""
    import json
    from hangar.design import DESIGNS_DIR, load_design
    want = json.loads((FIX / "design-verdicts.json").read_text(encoding="utf-8"))
    rec = want.pop("_recorded")
    today = datetime.date.fromisoformat(rec["today"])
    for name, exp in want.items():
        sc = run_gates(load_design(DESIGNS_DIR / name), 9, today=today)
        assert {str(t.tier): t.status for t in sc.tiers} == exp["tiers"], name
        assert sc.accepted == exp["accepted"], name


def test_verdict_fixture_records_its_date():
    import json
    from hangar.design import DESIGNS_DIR
    want = json.loads((FIX / "design-verdicts.json").read_text(encoding="utf-8"))
    rec = want.pop("_recorded")
    assert datetime.date.fromisoformat(rec["today"])
    # every recorded design still exists; a NEW design needs no entry (the verdict test below iterates the fixture only)
    assert set(want) <= {p.name for p in DESIGNS_DIR.iterdir() if (p / "plane.yaml").is_file()}


def test_validate_op_leaves_not_applicable_out_of_messages():
    from hangar.design import DESIGNS_DIR
    from hangar.ops import call
    r = call("design.validate", path=str(DESIGNS_DIR / "example-tailsitter-wing"))
    assert not any("not applicable" in m for m in list(r.messages) + list(r.skipped))
    assert "not_applicable" in r.data
