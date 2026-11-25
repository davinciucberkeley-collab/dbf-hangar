"""U18.4-1: tail volume coefficients."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from hangar.design import DESIGNS_DIR, PASS, SKIP, WARN, Design, load_design
from test_discipline_gates import rows, run

FIX = Path(__file__).parent / "fixtures"
CID = "T3.tail_volume"


def _base(morph=None) -> dict:
    d = copy.deepcopy(yaml.safe_load((FIX / "gates-base.yaml").read_text(encoding="utf-8")))
    for item in d["bom"]["items"]:
        item["verified"]["date"] = "2026-11-15"
    d["morphology"] = morph or {"lift": "fixed-wing", "vtol_method": "none"}
    return d


def tail_design(vt_span=150.0, ht_span=400.0) -> Design:
    d = _base()
    d["components"] += [
        {"id": "htail", "type": "tail_surface",
         "geometry": {"lifting_surface": {"span": ht_span, "root_chord": 100, "tip_chord": 80}},
         "position": [560, 0, 0], "mass_g": 5},
        {"id": "fin", "type": "tail_surface",
         "geometry": {"lifting_surface": {"span": vt_span, "root_chord": 100, "tip_chord": 60,
                                          "mirrored": False, "lifting": False}},
         "position": [560, 0, 0], "rotation_deg": [90, 0, 0], "mass_g": 5},
    ]
    for cid in ("htail", "fin"):
        d["attachments"].append({"id": f"{cid}-body", "parent": "body", "child": cid, "method": "bolted",
                                 "location": [560, 0, 0], "rated_load_n": 20})
    return Design(d, path=FIX / "gates-base.yaml")


def by_coef(design):
    rs = rows(run(design, tiers={3}), CID)
    return {r.data["coefficient"]: r for r in rs}


def test_vh_vv_hand_calc():
    r = by_coef(tail_design())
    assert len(r) == 2
    assert r["Vh"].status == PASS and r["Vh"].data["value"] == pytest.approx(0.4157, abs=0.002)
    assert r["Vh"].data["band"] == "within"
    assert r["Vv"].status == PASS and r["Vv"].data["value"] == pytest.approx(0.02816, abs=0.001)


def test_vh_below_band_warns_pending():
    r = by_coef(tail_design(ht_span=100))["Vh"]
    assert r.status == WARN and r.data["band"] == "below" and r.message.endswith("pending")
    assert r.data["value"] == pytest.approx(0.1039, abs=0.002)


def test_vv_above_band_warns_pending():
    r = by_coef(tail_design(vt_span=300))["Vv"]
    assert r.status == WARN and r.data["band"] == "above"
    assert r.data["value"] == pytest.approx(0.05633, abs=0.002)


def test_flying_wing_not_applicable():
    d = Design(_base({"lift": "flying-wing", "vtol_method": "tailsitter"}), path=FIX / "gates-base.yaml")
    rs = rows(run(d, tiers={3}), CID)
    assert len(rs) == 1 and rs[0].status == SKIP and rs[0].data["not_applicable"] is True


def test_no_tail_skips():
    d = Design(_base(), path=FIX / "gates-base.yaml")
    r = by_coef(d)
    assert set(r) == {"Vh", "Vv"} and all(x.status == SKIP for x in r.values())


def test_main_and_tails_selection():
    from hangar.gates import stability
    main, h, v = stability.main_and_tails(stability.declared_surfaces(tail_design()))
    assert main["id"] == "wing"
    assert [t["id"] for t in h] == ["htail"]
    assert [t["id"] for t in v] == ["fin"]


def test_new_keys_all_have_source():
    data = yaml.safe_load((Path(__file__).parent.parent / "standards" / "stability.yaml").read_text(encoding="utf-8"))
    for k, v in data.items():
        if k != "version":
            assert "source" in v, k


def test_c0_a1_hand_calc():
    r = by_coef(load_design(DESIGNS_DIR / "c0-a1"))
    assert r["Vh"].data["value"] == pytest.approx(0.370, abs=0.005)
    assert r["Vv"].data["value"] == pytest.approx(0.0223, abs=0.001)
