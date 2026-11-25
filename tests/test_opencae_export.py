"""U18.1-2: export a design to an OpenCAE drone project. None of these needs OpenCAE."""
import json
import shutil

import pytest
import trimesh
import yaml

from hangar.design import DESIGNS_DIR, load_design
from hangar.geometry import is_point_mass
from hangar.mass import mass_properties
from hangar.opencae_export import (INPUTS_FILE, drone_spec, export_project, load_inputs, solid_name,
                                   write_airframe_stl)

SOLVERS_OK = {"ccx": (True, "ok"), "cfd": (True, "ok")}
SOLVERS_NO = {"ccx": (False, "no ccx"), "cfd": (False, "no CFD solver: reason")}
BASIC = ("mass", "propulsion")


def _design(tmp_path):
    shutil.copytree(DESIGNS_DIR / "example-tailsitter-wing", tmp_path / "d")
    design = load_design(tmp_path / "d" / "plane.yaml")
    for c in design.data["components"]:
        if c["id"] == "motor_l":
            c["propulsion"]["max_current_a"] = 11.2
            c["propulsion"]["prop_diameter_mm"] = 254.0
        if c["id"] == "battery":
            c["battery"] = {"capacity_mah": 2200, "cells_s": 3, "max_discharge_c": 30}
            c["provenance"] = {"mass_source": "measured"}
    design.data["bom"] = [{"id": "b1", "component_ids": ["motor_l"], "qty": 1,
                           "verified": {"by": "t", "date": "2026-11-25", "method": "datasheet"}}]
    return design


def _spec(design, analyses=BASIC, solvers=SOLVERS_OK, inputs=None):
    inputs = inputs if inputs is not None else load_inputs(design)
    solids = {c["id"]: solid_name(c) for c in design.components if not is_point_mass(c)}
    return drone_spec(design, inputs, analyses, solvers, solids)


def _write_sidecar(design, text):
    (design.base_dir / INPUTS_FILE).write_text(text, encoding="utf-8")


def test_solid_names(tmp_path):
    d = _design(tmp_path)
    for cid, want in [("center_body", "frame_center_body"), ("motor_l", "motor_motor_l"), ("prop_l", "prop_prop_l"),
                      ("fin_l", "fin_fin_l"), ("battery", "battery"),
                      ("flight_controller", "electronics_flight_controller")]:
        assert solid_name(d.component(cid)) == want


def test_airframe_stl_is_ascii_named_solids(tmp_path):
    d = _design(tmp_path)
    path = tmp_path / "airframe.stl"
    res = write_airframe_stl(d, path)
    assert len(res["solids"]) == len(d.components) == 12
    assert res["point_masses"] == []
    text = path.read_text(encoding="ascii")
    assert text.startswith("solid frame_center_body")
    names = [ln.split(None, 1)[1].strip() for ln in text.splitlines() if ln.startswith("solid ")]
    ends = [ln.split(None, 1)[1].strip() for ln in text.splitlines() if ln.startswith("endsolid ")]
    assert len(names) == 12 and names == ends
    assert trimesh.load(path, force="mesh") is not None


def test_drone_spec_mapping(tmp_path):
    s = _spec(_design(tmp_path))
    assert s["format"] == "opencae-drone/1"
    assert s["type"] == "tailsitter"
    assert s["geometry"]["forward"] == "-x"
    assert s["mass"]["parts"]["battery"] == {"value": 250.0, "unit": "g", "status": "measured",
                                              "source": "plane design mass"}
    assert s["mass"]["parts"]["frame_center_body"]["status"] == "estimate"
    assert s["propulsion"]["motor"]["i_max_a"]["value"] == 11.2
    assert s["propulsion"]["motor"]["i_max_a"]["status"] == "datasheet"
    assert s["propulsion"]["prop"]["diameter_in"]["value"] == 10.0
    b = s["propulsion"]["battery"]
    assert b["cells"]["value"] == 3 and b["capacity_mah"]["value"] == 2200 and b["c_rating"]["value"] == 30
    assert s["propulsion"]["motor"]["kv"] is None
    assert s["propulsion"]["esc"]["i_cont_a"] is None
    assert s["aero"]["cruise_speed_ms"]["value"] == 14
    assert s["mission"]["hover_s"]["status"] == "user"
    assert s["analyses"]["cfd"]["enabled"] is False
    assert "requirements" not in s


def test_drone_spec_enables_by_request_and_solver(tmp_path):
    d = _design(tmp_path)
    full = ("mass", "propulsion", "structure", "cfd", "flight")
    a = _spec(d, full, SOLVERS_OK)["analyses"]
    assert a["structure"]["enabled"] and a["cfd"]["enabled"] and a["flight"]["enabled"]
    a = _spec(d, full, SOLVERS_NO)["analyses"]
    assert a["structure"]["enabled"] is False and a["cfd"]["enabled"] is False and a["flight"]["enabled"] is True


def test_export_project_skips_unavailable_solvers(tmp_path):
    d = _design(tmp_path)
    out = tmp_path / "p"
    r = export_project(d, out, ("mass", "structure", "cfd"), SOLVERS_NO)
    assert (out / "airframe.stl").is_file()
    assert r["skipped"] == {"structure": "no ccx", "cfd": "no CFD solver: reason"}
    assert json.loads((out / "drone.json").read_text(encoding="utf-8")) == r["spec"]


def test_sidecar_values_fill_nulls(tmp_path):
    d = _design(tmp_path)
    _write_sidecar(d, 'format: opencae-inputs/1\nvalues:\n  propulsion.motor.kv: '
                      '{value: 1000, unit: "rpm/V", status: datasheet, source: "test sheet"}\n')
    s = _spec(d)
    assert s["propulsion"]["motor"]["kv"] == {"value": 1000, "unit": "rpm/V", "status": "datasheet",
                                               "source": "test sheet"}


def test_sidecar_rejects_bad_input(tmp_path):
    d = _design(tmp_path)
    ok = {"value": 1, "unit": "", "status": "user", "source": "x"}
    cases = [({"values": {"propulsion.motor.foo": ok}}, "propulsion.motor.foo"),
             ({"values": {"propulsion.motor.kv": {**ok, "status": "guess"}}}, "guess"),
             ({"values": {"propulsion.motor.kv": {**ok, "source": ""}}}, "propulsion.motor.kv"),
             ({"role_materials": {"frame": "unobtainium"}}, "unobtainium")]
    for doc, word in cases:
        _write_sidecar(d, yaml.safe_dump({"format": "opencae-inputs/1", **doc}))
        with pytest.raises(ValueError, match=word):
            load_inputs(d)


def test_load_inputs_absent_file(tmp_path):
    shutil.copytree(DESIGNS_DIR / "example-tailsitter-wing", tmp_path / "d")
    d = load_design(tmp_path / "d" / "plane.yaml")
    assert load_inputs(d) == {"values": {}, "materials": {}, "role_materials": {}}


def test_mass_total_matches_plane_mass_for_meshed_design(tmp_path):
    d = _design(tmp_path)
    s = _spec(d)
    total = sum(p["value"] for p in s["mass"]["parts"].values())
    assert abs(total - mass_properties(d)["mass_g"]) < 1e-6


def test_point_masses_are_listed_not_exported(tmp_path):
    d = _design(tmp_path)
    d.data["components"].append({"id": "hrd_x", "type": "other", "geometry": {"point_mass": {}},
                                 "position": [0, 0, 0], "mass_g": 5, "manufacturing": {"method": "purchased"}})
    res = write_airframe_stl(d, tmp_path / "a.stl")
    assert res["point_masses"] == ["hrd_x"] and "hrd_x" not in res["solids"]
    assert "other_hrd_x" not in (tmp_path / "a.stl").read_text(encoding="ascii")
    assert "other_hrd_x" not in _spec(d)["mass"]["parts"]
