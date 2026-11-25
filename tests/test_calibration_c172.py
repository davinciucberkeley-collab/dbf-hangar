"""U18.2: calibrate hangar's tier-3 mass, stall, wing loading and neutral point against the Cessna 172S."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from hangar import calibration
from hangar.design import PASS, WARN, Design
from test_discipline_gates import rows, run

FIX = Path(__file__).parent / "fixtures"
KT = 0.514444
MTOW_G = 1157000
AREA_M2 = 16.17
VS1 = 53 * KT  # flaps up, 2,550 lb, KCAS (POH Rev 5 p.124); the 48 is KIAS
VS0 = 48 * KT  # flaps 30 deg, KCAS (POH p.124)
CRUISE = 124 * KT
RHO = 1.225
G = 9.80665


def c172() -> Design:
    d = copy.deepcopy(yaml.safe_load((FIX / "c172s" / "plane.yaml").read_text(encoding="utf-8")))
    return Design(d, path=FIX / "c172s" / "plane.yaml")


def one(design, cid):
    rs = rows(run(design, tiers={3}), cid)
    assert len(rs) == 1, rs
    return rs[0]


def test_mass_matches_published():
    d = c172()
    assert one(d, "T3.mass").status == PASS
    mass = sum(c["mass_g"] for c in d.data["components"])
    assert calibration.within(mass, MTOW_G, "calibration_tol_mass_fraction")


def test_wing_loading_matches_published():
    d = c172()
    wl = one(d, "T3.stall").data["wing_loading_g_dm2"]
    assert wl == pytest.approx(715.52, abs=0.1)
    assert calibration.within(wl, MTOW_G / 1617.0, "calibration_tol_geometry_fraction")
    r = one(d, "T3.wing_loading")
    assert r.status == WARN and r.data["band"] == "above"


def test_stall_default_clmax_is_a_known_overestimate():
    """Pins the finding; a change here means CLmax handling changed."""
    stall = one(c172(), "T3.stall").data["stall_mps"]
    assert stall == pytest.approx(32.27, abs=0.05)
    assert calibration.error_fraction(stall, VS1) == pytest.approx(0.1835, abs=0.01)
    assert calibration.error_fraction(stall, VS0) == pytest.approx(0.3068, abs=0.01)


def test_stall_with_published_clmax_within_tolerance():
    d = c172()
    d.data["flight"] = {"cl_max": 1.54}  # implied by Vs1 = 53 KCAS: 2W / (rho S Vs1^2) = 1.541
    stall = one(d, "T3.stall").data["stall_mps"]
    assert stall == pytest.approx(27.27, abs=0.05)
    assert calibration.within(stall, VS1, "calibration_tol_stall_fraction")


def test_cruise_stall_ratio_default():
    assert one(c172(), "T3.cruise_stall_ratio").data["ratio"] == pytest.approx(1.977, abs=0.01)


def test_neutral_point_hand_calc():
    assert one(c172(), "T3.static_margin").data["x_np_mm"] == pytest.approx(2639.5, abs=5.0)


def test_cg_inside_published_range():
    sm = one(c172(), "T3.static_margin").data["static_margin"]
    assert sm > 0, f"static margin at the published aft CG limit is {sm}"


def test_tolerance_keys_exist_with_source():
    for key in calibration.KEYS:
        value, pending = calibration.tolerance(key)
        assert isinstance(value, float) and isinstance(pending, bool)
    with pytest.raises(KeyError):
        calibration.tolerance("nope")


def test_error_fraction():
    assert calibration.error_fraction(110, 100) == pytest.approx(0.1)
    with pytest.raises(ValueError):
        calibration.error_fraction(1, 0)
