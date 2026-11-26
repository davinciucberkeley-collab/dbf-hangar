"""U18.4-2: elevator deflection to trim (T3.trim)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from hangar.calcs import trim as tc
from hangar.design import PASS, SKIP, WARN, Design
from hangar.gates import stability
from test_discipline_gates import rows, run
from test_tail_volume import FIX, _base, tail_design

CID = "T3.trim"


def test_trim_tail_lift():
    assert tc.trim_tail_lift_n(10, 1, 100, 120, 520, 0.0) == pytest.approx(-0.5, abs=1e-9)
    assert tc.trim_tail_lift_n(10, 1, 100, 120, 520, -200.0) == pytest.approx(-1.0, abs=1e-9)
    with pytest.raises(ValueError):
        tc.trim_tail_lift_n(10, 1, 100, 120, 120)


def test_tail_cl():
    assert tc.tail_lift_coefficient(-0.5, 137.8125, 0.02) == pytest.approx(-0.18141, abs=1e-4)


def test_helmbold():
    assert tc.helmbold_slope(4) == pytest.approx(3.88322, abs=1e-4)


def test_elevator_deflection():
    assert tc.elevator_deflection_deg(-0.18141, 4, 0.9, 0.5) == pytest.approx(-5.948, abs=0.01)


def _rows():
    d = tail_design()
    d.data.setdefault("requirements", {})["cruise_speed_mps"] = 18
    return d, rows(run(d, tiers={3}), CID)


def test_gate_rows_cruise_and_stall():
    d, rs = _rows()
    assert [r.data["condition"] for r in rs] == ["cruise", "stall"]
    main, h, _ = stability.main_and_tails(stability.declared_surfaces(d))
    t = h[0]
    for r in rs:
        assert r.status in (PASS, WARN)
        q = 0.5 * 1.225 * r.data["speed_mps"] ** 2
        cl = tc.tail_lift_coefficient(r.data["tail_lift_n"], q, t["area_mm2"] / 1e6)
        de = tc.elevator_deflection_deg(cl, t["aspect_ratio"], 0.9, 0.5)
        assert r.data["elevator_deg"] == pytest.approx(de, abs=0.02)


def test_gate_sign_cg_ahead_of_ac():
    _, rs = _rows()
    c = rs[0].data
    assert (c["tail_lift_n"] < 0) == (c["x_cg_mm"] < 111.04)


def test_flying_wing_not_applicable():
    d = Design(_base({"lift": "flying-wing", "vtol_method": "tailsitter"}), path=FIX / "gates-base.yaml")
    rs = rows(run(d, tiers={3}), CID)
    assert len(rs) == 1 and rs[0].status == SKIP and rs[0].data["not_applicable"] is True


def test_no_tail_skips():
    d = Design(_base(), path=FIX / "gates-base.yaml")
    rs = rows(run(d, tiers={3}), CID)
    assert len(rs) == 1 and rs[0].status == SKIP and rs[0].data["condition"] == "all"


def test_new_keys_all_have_source():
    data = yaml.safe_load((Path(__file__).parent.parent / "standards" / "stability.yaml").read_text(encoding="utf-8"))
    for k, v in data.items():
        if k != "version":
            assert "source" in v, k
