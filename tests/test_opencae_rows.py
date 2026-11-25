"""U18.1-3: tier-2 rows from stored OpenCAE results. Recorded fixture only; OpenCAE is not needed."""
import copy
import json
import shutil
from pathlib import Path

from hangar import opencae_cli
from hangar.design import DESIGNS_DIR, load_design
from hangar.geometry import is_point_mass
from hangar.mass import mass_properties
from hangar.opencae_rows import tier2_opencae

FIXTURE = Path(__file__).parent / "fixtures" / "opencae" / "quad250_cfd_su2.json"
ALL = ("mass", "propulsion", "structure", "cfd", "flight")


def _design(tmp_path):
    shutil.copytree(DESIGNS_DIR / "example-tailsitter-wing", tmp_path / "d")
    return load_design(tmp_path / "d" / "plane.yaml")


def _fixture():
    return copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _store(design, result=None, analyses=ALL):
    result = result if result is not None else _fixture()
    opencae_cli.store_result(design, "h", opencae_cli.design_fingerprint(design, analyses), analyses, "abc1234", result)


def _match_mass(design, result):
    # the fixture quad250 mass (472 g) is not this design mass: set it so the mass row can match.
    # Point masses are not in OpenCAE mass.parts, so the plane total minus point masses is what OpenCAE reports.
    result["analyses"]["mass"]["metrics"]["mass_kg"]["value"] = (mass_properties(design)["mass_g"] - _point_g(design)) / 1000


def _point_g(design):
    return sum(c["mass_g"] for c in design.components if is_point_mass(c))


def _rows(design, rid):
    return [r for r in tier2_opencae(design) if r.check_id == rid]


def test_no_rows_without_results_or_sidecar(tmp_path):
    assert tier2_opencae(_design(tmp_path)) == []


def test_skip_row_when_sidecar_but_no_results(tmp_path):
    d = _design(tmp_path)
    (d.base_dir / "opencae-inputs.yaml").write_text("format: opencae-inputs/1\n", encoding="utf-8")
    rows = tier2_opencae(d)
    assert len(rows) == 1 and rows[0].check_id == "T2.opencae" and rows[0].status == "SKIP"
    assert "plane opencae run" in rows[0].message


def test_stale_results_skip(tmp_path):
    d = _design(tmp_path)
    _store(d)
    d.data["components"][0]["mass_g"] += 1
    rows = tier2_opencae(d)
    assert len(rows) == 1 and rows[0].check_id == "T2.opencae" and rows[0].status == "SKIP"
    assert "out of date" in rows[0].message


def test_hover_tw_pass_and_fail(tmp_path):
    d = _design(tmp_path)
    _store(d)
    (r,) = _rows(d, "T2.opencae_hover_tw")
    assert r.status == "PASS" and "6.65" in r.message and r.message.endswith("; OpenCAE basis " + r.data["basis"])
    res = _fixture()
    res["analyses"]["propulsion"]["metrics"]["tw_ratio"]["value"] = 1.0
    _store(d, res)
    assert _rows(d, "T2.opencae_hover_tw")[0].status == "FAIL"


def test_current_margin_three_rows(tmp_path):
    d = _design(tmp_path)
    _store(d)
    rows = _rows(d, "T2.opencae_current_margin")
    assert len(rows) == 3 and all(r.status == "PASS" for r in rows)
    res = _fixture()
    res["analyses"]["propulsion"]["metrics"]["esc_current_margin"]["value"] = 0.9
    _store(d, res)
    rows = _rows(d, "T2.opencae_current_margin")
    assert [r.status for r in rows].count("FAIL") == 1 and "ESC" in [r for r in rows if r.status == "FAIL"][0].message


def test_endurance(tmp_path):
    d = _design(tmp_path)
    _store(d)
    assert _rows(d, "T2.opencae_endurance")[0].status == "PASS"
    res = _fixture()
    res["analyses"]["propulsion"]["metrics"]["hover_endurance_min"]["value"] = 2.0
    _store(d, res)
    assert _rows(d, "T2.opencae_endurance")[0].status == "FAIL"


def test_structure_sf_is_skip_with_would_be_while_pending(tmp_path):
    d = _design(tmp_path)
    _store(d)
    (r,) = _rows(d, "T2.opencae_structure_sf")
    assert r.status == "SKIP" and r.data["would_be"] == "PASS"
    assert "not judged" in r.message and "12.26" in r.message
    assert r.message.endswith("; OpenCAE basis estimate")


def test_cfd_ld_skip_without_declared_ld_and_judged_with_it(tmp_path):
    d = _design(tmp_path)
    _store(d)
    (r,) = _rows(d, "T2.opencae_cfd_ld")
    assert r.status == "SKIP" and "flight.cruise_ld missing" in r.message
    d.data.setdefault("flight", {})["cruise_ld"] = 10.0
    _store(d)
    (r,) = _rows(d, "T2.opencae_cfd_ld")
    assert r.status == "SKIP" and r.data["would_be"] == "FAIL"


def test_flight_row(tmp_path):
    d = _design(tmp_path)
    _store(d)
    (r,) = _rows(d, "T2.opencae_flight")
    assert r.status == "SKIP" and r.data["would_be"] == "PASS" and "settled in 1.5 s" in r.message


def test_mass_cross(tmp_path):
    d = _design(tmp_path)
    res = _fixture()
    _match_mass(d, res)
    _store(d, res)
    (r,) = _rows(d, "T2.opencae_mass_cross")
    assert r.status == "SKIP" and r.data["would_be"] == "PASS"
    _store(d)
    assert _rows(d, "T2.opencae_mass_cross")[0].data["would_be"] == "FAIL"


def test_not_evaluated_and_error_analyses(tmp_path):
    d = _design(tmp_path)
    res = _fixture()
    res["analyses"]["structure"]["status"] = "not_evaluated"
    res["analyses"]["structure"]["missing"] = ["materials.carbon_plate.yield_strength_mpa"]
    res["analyses"]["propulsion"]["status"] = "error"
    _store(d, res)
    rows = tier2_opencae(d)
    assert any(r.status == "SKIP" and "materials.carbon_plate.yield_strength_mpa" in r.message for r in rows)
    assert any(r.status == "FAIL" and "failed" in r.message for r in rows)


def test_multirotor_only_rows_absent_for_non_vtol_design(tmp_path):
    d = _design(tmp_path)
    d.data["morphology"]["vtol_method"] = "none"
    d.data["morphology"]["lift"] = "fixed-wing"
    _store(d)
    ids = {r.check_id for r in tier2_opencae(d)}
    assert not ids & {"T2.opencae_hover_tw", "T2.opencae_endurance", "T2.opencae_flight"}


def test_validate_unchanged_for_designs_without_results():
    for p in DESIGNS_DIR.iterdir():
        if p.is_dir() and (p / "plane.yaml").is_file() and not (p / "opencae").exists() \
                and not (p / "opencae-inputs.yaml").exists():
            assert tier2_opencae(load_design(p / "plane.yaml")) == [], p.name


def test_mass_cross_adds_point_masses_back(tmp_path):
    d = _design(tmp_path)
    d.data["components"].append({"id": "hrd_x", "type": "other", "geometry": {"point_mass": {}},
                                 "position": [0, 0, 0], "mass_g": 50, "manufacturing": {"method": "purchased"}})
    res = _fixture()
    _match_mass(d, res)          # OpenCAE mass = plane total minus the 50 g point mass
    _store(d, res)
    (r,) = _rows(d, "T2.opencae_mass_cross")
    assert r.data["would_be"] == "PASS"
