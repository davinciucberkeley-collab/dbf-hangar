"""U18.3: wing spar bending by beam theory (T3.spar_bending, report-only); hand-calculated values from the brief."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from hangar.calcs.spar import root_moment_nmm, spanwise_load, tip_deflection_mm, tube_section
from hangar.design import FAIL, PASS, SKIP, Design
from hangar.design import REPO_ROOT
from test_discipline_gates import rows, run

FIX = Path(__file__).parent / "fixtures"


def spar_design(od=20, idd=16, material="petg-printed"):
    d = copy.deepcopy(yaml.safe_load((FIX / "gates-base.yaml").read_text(encoding="utf-8")))
    for item in d["bom"]["items"]:
        item["verified"]["date"] = "2026-11-15"
    d["morphology"] = {"lift": "fixed-wing", "vtol_method": "none"}
    d["schema_version"] = "1.2"
    d["components"].append({
        "id": "spar", "type": "structure",
        "geometry": {"generator": "tube",
                     "params": {"axis": "y", "center": [60, 0, 0], "length": 1000, "outer_d": od, "inner_d": idd}},
        "position": [0, 0, 0], "mass_g": 30, "material": material})
    d["attachments"].append({"id": "spar-wing", "parent": "wing", "child": "spar", "method": "glued",
                             "location": [60, 0, 0], "rated_load_n": 50})
    return Design(d, path=FIX / "gates-base.yaml")


def test_root_moment_elliptic():
    y, dy, w = spanwise_load(1000, 250, 150, 24.2224, "elliptic")
    assert root_moment_nmm(y, dy, w) == pytest.approx(2570.08, rel=3e-3)


def test_root_moment_schrenk():
    y, dy, w = spanwise_load(1000, 250, 150, 24.2224, "schrenk")
    assert root_moment_nmm(y, dy, w) == pytest.approx(2672.8, rel=3e-3)


def test_unknown_distribution_raises():
    with pytest.raises(ValueError):
        spanwise_load(1000, 250, 150, 24.2224, "rectangular")


def test_tube_section():
    assert tube_section(20, 16) == (pytest.approx(4637.0, rel=1e-3), 10.0)


def test_tip_deflection_uniform_load():
    n = 400
    dy = 500 / n
    y = [(i + 0.5) * dy for i in range(n)]
    w = [0.01] * n
    assert tip_deflection_mm(y, dy, w, 1000, 9273981.0) == pytest.approx(8.424, rel=1e-3)
    assert root_moment_nmm(y, dy, w) == pytest.approx(1250.0, rel=1e-3)


def test_gate_pass():
    rs = rows(run(spar_design(), tiers={3}), "T3.spar_bending")
    assert len(rs) == 1, rs
    r = rs[0]
    assert r.status == PASS
    assert r.data["root_moment_nmm"] == pytest.approx(2672.8, rel=0.01)
    assert r.data["stress_ultimate_mpa"] == pytest.approx(8.646, rel=0.01)
    assert r.data["reserve_factor"] == pytest.approx(1.457, rel=0.01)
    assert r.data["distribution"] == "schrenk"
    assert r.data["component"] == "spar"


def test_gate_fail_thin_tube():
    rs = rows(run(spar_design(12, 10), tiers={3}), "T3.spar_bending")
    assert len(rs) == 1, rs
    r = rs[0]
    assert r.status == FAIL
    assert r.data["reserve_factor"] == pytest.approx(0.276, rel=0.02)
    assert r.data["band"] == "below"


def test_gate_skip_without_allowable():
    rs = rows(run(spar_design(material="cfrp-tube"), tiers={3}), "T3.spar_bending")
    assert len(rs) == 1, rs
    r = rs[0]
    assert r.status == SKIP
    assert "no sourced allowable" in r.message
    assert r.data["root_moment_nmm"] == pytest.approx(2672.8, rel=0.01)


def test_gate_skip_without_spar():
    d = spar_design()
    d.data["components"] = [c for c in d.data["components"] if c["id"] != "spar"]
    d.data["attachments"] = [a for a in d.data["attachments"] if a["id"] != "spar-wing"]
    rs = rows(run(d, tiers={3}), "T3.spar_bending")
    assert len(rs) == 1, rs
    assert rs[0].status == SKIP
    assert "no spar tube found" in rs[0].message


def test_new_keys_all_have_source():
    data = yaml.safe_load((REPO_ROOT / "standards" / "spar.yaml").read_text(encoding="utf-8"))
    keys = [k for k in data if k != "version"]
    assert keys
    for k in keys:
        assert data[k].get("source"), k
