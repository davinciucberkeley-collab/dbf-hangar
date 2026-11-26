"""U18.4-3: dynamic modes (pure maths always; AeroSandbox part only where the tool is installed)."""
from __future__ import annotations

import importlib.util
import math

import pytest
import yaml

from hangar import baseline
from hangar.calcs import modes
from hangar.design import DESIGNS_DIR, SKIP, Design
from test_discipline_gates import rows, run
from test_tail_volume import FIX, _base, tail_design

CID = "T3.dynamic_modes"


def test_short_period():
    w, z = modes.short_period(-20, -3, -2)
    assert w == pytest.approx(5.0990, abs=1e-3) and z == pytest.approx(0.4903, abs=1e-3)


def test_dutch_roll():
    w, z = modes.dutch_roll(-0.5, -1.0, 8.0)
    assert w == pytest.approx(2.9155, abs=1e-3) and z == pytest.approx(0.2572, abs=1e-3)


def test_phugoid():
    w, z = modes.phugoid_lanchester(20, 10)
    assert w == pytest.approx(0.6934, abs=1e-3) and z == pytest.approx(0.07071, abs=1e-3)


def test_lateral_modes():
    r = modes.lateral_modes([[-0.5, 0, -1, 0], [0, -10, 0, 0], [8, 0, -1, 0], [0, 1, 0, 0.02]])
    assert r["dutch_roll"]["omega"] == pytest.approx(2.9155, abs=1e-3)
    assert r["dutch_roll"]["zeta"] == pytest.approx(0.2572, abs=1e-3)
    assert r["roll_tau_s"] == pytest.approx(0.1, abs=1e-3)
    assert r["spiral_lambda"] == pytest.approx(0.02, abs=1e-3)
    assert r["spiral_time_to_double_s"] == pytest.approx(math.log(2) / 0.02, abs=0.01)


def test_lateral_matrix_first_row():
    assert modes.lateral_matrix(-0.5, 0, 0, 0, 8, 0, -1, 20)[0] == pytest.approx([-0.5, 0, -1, 0.490333], abs=1e-6)


def test_short_period_unstable_raises():
    with pytest.raises(ValueError):
        modes.short_period(10, -3, -2)


def _design(**req):
    d = tail_design()
    d.data.setdefault("requirements", {})["cruise_speed_mps"] = 18
    return d


def test_missing_tool_skips(monkeypatch):
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec",
                        lambda name, *a, **k: None if name == "aerosandbox" else real(name, *a, **k))
    rs = rows(run(_design(), tiers={3}), CID)
    assert len(rs) == 1 and rs[0].status == SKIP
    assert rs[0].message.startswith("aerosandbox not installed; run: python -m pip install aerosandbox")


def test_baseline_ignores_missing_tool_skip():
    assert baseline.is_blocking(CID, SKIP, "aerosandbox not installed; run: python -m pip install aerosandbox "
                                           "(dynamic modes not computed)") is True


def test_flying_wing_tailsitter_applicable_multirotor_not():
    d = Design(_base({"lift": "multirotor", "vtol_method": "lift-plus-cruise"}), path=FIX / "gates-base.yaml")
    try:
        rs = rows(run(d, tiers={3}), CID)
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"tier 3 raises on the multirotor fixture: {type(e).__name__}")
    assert len(rs) == 1 and rs[0].status == SKIP and rs[0].data["not_applicable"] is True


def test_thresholds_have_source_and_phugoid_pending():
    data = yaml.safe_load((DESIGNS_DIR.parent / "standards" / "stability.yaml").read_text(encoding="utf-8"))
    for k, v in data.items():
        if k != "version":
            assert v.get("source"), k
    assert data["phugoid_damping_min"]["source"] == "pending"
    for k in ("short_period_damping_min", "dutch_roll_damping_min", "spiral_time_to_double_min_s"):
        assert "std-mil-f-8785c-damping" in data[k]["source"]


def test_derivatives_sanity_with_tool():
    pytest.importorskip("aerosandbox")
    from hangar.calcs.asb_derivatives import stability_derivatives
    d = tail_design()
    comp = {c["id"]: c for c in d.data["components"]}
    wing = next(c for c in d.data["components"] if (c.get("geometry") or {}).get("lifting_surface")
                and c["id"] not in ("htail", "fin"))
    r = stability_derivatives({"main": wing, "h": comp["htail"], "v": comp["fin"]}, [0.1, 0, 0], 18, 1.225)
    assert set(r) == {"CLa", "Cma", "Cmq", "CYb", "Clb", "Cnb", "Clp", "Clr", "Cnp", "Cnr"}
    assert r["Cma"] < 0 and r["CLa"] > 0 and r["Cnb"] > 0 and r["Clb"] < 0 and r["Cmq"] < 0


def test_gate_rows_with_tool():
    pytest.importorskip("aerosandbox")
    d = _design()
    d.data.setdefault("flight", {})["cruise_ld"] = 8
    rs = rows(run(d, tiers={3}), CID)
    assert [r.data["mode"] for r in rs] == ["short_period", "phugoid", "dutch_roll", "spiral"]
    for r in rs:
        assert r.status in ("PASS", "WARN", "SKIP")
        assert r.data.get("zeta") is None or isinstance(r.data["zeta"], float)
