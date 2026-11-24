from hangar.design import REPO_ROOT, load_design
from hangar.ops import call
import pytest
A = REPO_ROOT / "designs" / "concept-a"
def test_concept_a_has_the_u25d_blocks():
    d = load_design(A).data
    assert d["schema_version"] == "1.0"
    assert len(d["bom"]["items"]) == 42 and len(d["assembly"]["sequence"]) == 44
    assert len(d["wiring"]["harnesses"]) == 14 and d["transport"]["disassembly"][0]["group"] == "packed-airframe"
    assert d["requirements"]["transport_box_mm"] == [1200, 500, 400]
def test_concept_a_bom_total():
    assert call("bom.cost", path=str(A)).data["total_usd"] == pytest.approx(1262.50, abs=0.01)
def test_every_verified_bom_line_keeps_url_and_date():
    items = load_design(A).data["bom"]["items"]
    assert all(i["url"] and i["verified"]["date"] for i in items if i.get("verified"))
def test_budget_and_d21_data_survived_the_reimport():
    d = load_design(A).data
    assert d["requirements"]["budget_usd"] == 2000
    pwr = next(c for c in d["components"] if c["id"] == "pwr-001")
    assert pwr["battery"]["capacity_mah"] == 2300 and d["flight"]["cruise_ld"] == 7.19
    assert next(h for h in d["wiring"]["harnesses"] if h["id"] == "hrn-bat")["gauge_awg"] == 10  # T60, D57: re-gauged from the imported 14 AWG
def test_elevon_mechanisms_survived_the_reimport():
    ms = {m["id"]: m for m in load_design(A).data["mechanisms"]}
    assert ms["elevon-r"]["driver"] == "E-MEC-02" and ms["elevon-l"]["driver"] == "E-MEC-07"
    assert ms["elevon-r"]["expect"][0]["ratio"] == -1.33
