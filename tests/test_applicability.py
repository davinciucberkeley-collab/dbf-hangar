"""U4.30-1: applicability from morphology; not-applicable SKIP rows stay out of baselines."""
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


def test_vtol_design_unchanged():
    sc = card(vtol())
    for cid in IDS:
        assert not any((r.data or {}).get("not_applicable") for r in rows(sc, cid))


def test_baseline_ignores_not_applicable():
    snap = snapshot(card(fixed_wing()))
    assert not [k for k in snap["known"] if k["check_id"] in IDS]
