"""U18.4-4 (T153): T3.tail_volume and T3.trim read the generated main wing and generated tail (c172-rc)."""
from __future__ import annotations

import copy

import pytest
from pytest import approx
from test_discipline_gates import rows, run

from hangar import yamlfast
from hangar.design import DESIGNS_DIR, PASS, SKIP, WARN, load_design, load_standards
from hangar.gates.stability import all_surfaces, declared_surfaces, generated_surfaces
from hangar.geom.planform import generated_fin


@pytest.fixture(scope="module")
def design():
    return load_design(DESIGNS_DIR / "c172-rc")


@pytest.fixture(scope="module")
def card(design):
    return run(design, tiers=(3,))


def test_generated_fin_params():
    data = yamlfast.safe_load((DESIGNS_DIR / "c172-rc" / "plane.yaml").read_text(encoding="utf-8"))
    comps = {c["id"]: c for c in data["components"]}
    fin = generated_fin(comps["tail-fixed"])
    assert fin["lifting_surface"] == {"span": 116.0, "root_chord": 225.0, "tip_chord": 86.0, "sweep_le_deg": 44.0,
                                      "mirrored": False, "lifting": False}
    assert fin["offset"] == [-104.0, 0.0, 16.0]
    assert fin["rotation_deg"] == [90.0, 0.0, 0.0]
    assert generated_fin(comps["elevator"]) is None
    assert generated_fin(comps["rudder"]) is None
    v = copy.deepcopy(comps["tail-fixed"])
    v["geometry"]["params"]["layout"] = "v"
    assert generated_fin(v) is None
    assert generated_fin(comps["fuselage"]) is None


def test_generated_surfaces_c172_rc(design):
    std = load_standards()
    gs = generated_surfaces(design, std)
    by = {s["id"]: s for s in gs}
    assert set(by) == {"wing-core", "tail-fixed", "tail-fixed:fin"} and len(gs) == 3
    w = by["wing-core"]
    assert w["area_mm2"] == approx(161458.8, rel=1e-3)
    assert w["mac_mm"] == approx(149.07, rel=2e-3)
    assert w["x_ac_mm"] == approx(239.33, abs=0.5)
    assert w["span_mm"] == approx(1100.0)
    assert w["vertical"] is False
    t = by["tail-fixed"]
    assert t["area_mm2"] == approx(34450.0, abs=0.01)
    assert t["mac_mm"] == approx(106.616, abs=0.01)
    assert t["x_ac_mm"] == approx(680.350, abs=0.01)
    assert t["aspect_ratio"] == approx(3.066, abs=0.001)
    assert t["vertical"] is False
    f = by["tail-fixed:fin"]
    assert f["area_mm2"] == approx(18038.0, abs=0.01)
    assert f["mac_mm"] == approx(165.854, abs=0.01)
    assert f["x_ac_mm"] == approx(625.129, abs=0.01)
    assert f["vertical"] is True
    assert f["lifting"] is False
    assert all_surfaces(design, std) == declared_surfaces(design) + gs


def test_tail_volume_rows_c172_rc(card):
    rs = rows(card, "T3.tail_volume")
    assert len(rs) == 2
    r = {x.data["coefficient"]: x for x in rs}
    h = r["Vh"]
    assert h.status == WARN
    assert h.data["value"] == approx(0.6313, abs=0.002)
    assert h.data["band"] == "above"
    assert h.data["surfaces"] == ["tail-fixed"]
    assert h.message.endswith("provisional: stability.yaml#tail_volume_h_min pending")
    v = r["Vv"]
    assert v.status == PASS
    assert v.data["value"] == approx(0.0392, abs=0.001)
    assert v.data["band"] == "within"
    assert v.data["surfaces"] == ["tail-fixed:fin"]


def test_trim_rows_c172_rc(card):
    rs = rows(card, "T3.trim")
    assert [r.data["condition"] for r in rs] == ["cruise", "stall"]
    assert rs[0].status == SKIP and rs[0].message == "cruise: requirements.cruise_speed_mps missing"
    s = rs[1]
    assert s.status == PASS
    d = s.data
    assert d["tail"] == "tail-fixed"
    assert d["speed_mps"] == approx(8.05, abs=0.02)
    assert d["tail_lift_n"] == approx(0.296, abs=0.005)
    assert d["tail_cl"] == approx(0.2176, abs=0.003)
    assert d["elevator_deg"] == approx(8.15, abs=0.1)
    assert d["x_cg_mm"] == approx(257.95, abs=0.1)
    assert d["band"] == "within"
    assert "(the T3.stall speed)" in s.message


def test_tier3_rows_unchanged(card):
    assert rows(card, "T3.stall")[0].message == "wing loading 44.6 g/dm^2, stall 8.1 m/s (CLmax 1.1)"
    assert rows(card, "T3.static_margin")[0].message.startswith("9.5% MAC (NP x=272 mm, CG x=258 mm")


def test_tailsitter_still_not_applicable():
    d = load_design(DESIGNS_DIR / "example-tailsitter-wing")
    card = run(d, tiers=(3,))
    for cid in ("T3.tail_volume", "T3.trim"):
        rs = rows(card, cid)
        assert len(rs) == 1 and rs[0].status == SKIP and rs[0].data["not_applicable"] is True
