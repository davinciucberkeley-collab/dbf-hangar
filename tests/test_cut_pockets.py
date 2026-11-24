"""U4.28: wing_panel pockets follow the neighbours' current placement; T1.pocket flags a part in uncut core."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from hangar.checks import tier1_geometry
from hangar.design import load_design, load_standards
from hangar.geom import registry
from hangar.geom.kernel import box
from hangar.geom.registry import get, validate_params
from hangar.geom.resolve import resolve_design_data
from hangar.geometry import component_parts
from hangar.ops import call

FIXTURE = Path(__file__).parent / "fixtures" / "pdl-gen"
DAT = "airfoils/diamond.dat"
REPO = Path(__file__).resolve().parent.parent
MSG_STALE = "{c}: {v} mm^3 of it sits in uncut core of wing; its pocket is not cut where the part is now"


def wing(**kw):
    p = {"airfoil_file": DAT, "span": 400, "root_chord": 100, "tip_chord": 100, "part": "core", "hinge_frac": 0.75}
    p.update(kw)
    return p


def vol(m):
    return abs(float(m.volume))


def build(params, base):
    return registry.build_component({"id": "t", "geometry": {"generator": "wing_panel", "params": params}}, base)


def _design(tmp_path, flap_pos=(0, 0, 0), horn=False) -> Path:
    d = tmp_path / "d"
    (d / "airfoils").mkdir(parents=True)
    (d / "meshes").mkdir()
    shutil.copy(FIXTURE / DAT, d / DAT)
    box((20, 30, 10), (100, 0, 0)).export(d / "meshes" / "flap.stl")
    comps = [
        {"id": "wing", "type": "structure",
         "geometry": {"generator": "wing_panel", "params": {
             "airfoil_file": DAT, "span": 400, "root_chord": 200, "tip_chord": 200, "part": "core",
             "hinge_frac": 0.75, "cut_files": ["meshes/flap.stl"]}},
         "position": [0, 0, 0], "mass_model": {"density_g_cm3": 0.025}},
        {"id": "flap", "type": "other", "geometry": {"mesh": {"file": "meshes/flap.stl"}},
         "position": list(flap_pos), "mass_g": 1},
    ]
    atts = [{"id": "A-flap", "parent": "wing", "child": "flap", "method": "glued", "location": [100, 0, 0],
             "rated_load_n": 1}]
    if horn:
        box((10, 10, 4), (50, 0, 0)).export(d / "meshes" / "horn.stl")
        comps.append({"id": "horn", "type": "other", "geometry": {"mesh": {"file": "meshes/horn.stl"}},
                      "position": [0, 0, 0], "mass_g": 1})
        atts.append({"id": "A-horn", "parent": "wing", "child": "horn", "method": "glued", "location": [50, 0, 0],
                     "rated_load_n": 1})
    doc = {"schema_version": "1.2", "id": "pocket-fixture", "name": "Pocket fixture", "status": "concept",
           "morphology": {"lift": "flying-wing", "vtol_method": "none"}, "root": "wing",
           "components": comps, "attachments": atts}
    (d / "plane.yaml").write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return d


def _rows(design):
    rep = tier1_geometry(design, load_standards())
    return [r for r in rep.results if r.check_id == "T1.pocket"]


def test_cut_poses_move_the_pocket(tmp_path):
    (tmp_path / "airfoils").mkdir()
    shutil.copy(FIXTURE / DAT, tmp_path / DAT)
    box((20, 30, 10), (100, 0, 0)).export(tmp_path / "cutter.stl")
    base = wing(root_chord=200, tip_chord=200, cut_files=["cutter.stl"])
    (m0,) = build(base, tmp_path)
    assert vol(m0) == pytest.approx(694000, rel=1e-6)
    p = dict(base, cut_poses=[{"file": "cutter.stl", "matrix": [1, 0, 0, 35, 0, 1, 0, 0, 0, 0, 1, 0]}])
    (m1,) = build(p, tmp_path)
    assert vol(m1) == pytest.approx(694000, rel=1e-6)
    assert m1.bounds == pytest.approx(m0.bounds)
    p = dict(base, cut_poses=[{"file": "cutter.stl", "matrix": [1, 0, 0, 60, 0, 1, 0, 0, 0, 0, 1, 0]}])
    (m2,) = build(p, tmp_path)
    assert vol(m2) == pytest.approx(700000, rel=1e-6)


def test_cut_poses_check_messages():
    g = get("wing_panel")
    for e in ({"file": "b.stl", "matrix": [0] * 12}, {"file": "a.stl", "matrix": [0] * 11}, "x",
              {"file": "a.stl", "matrix": [True] * 12}):
        msgs = validate_params(g, wing(cut_files=["a.stl"], cut_poses=[e]))
        assert len(msgs) == 1 and "cut_poses" in msgs[0]
    assert validate_params(g, wing(cut_files=["a.stl"], cut_poses=[{"file": "a.stl", "matrix": [0] * 12}])) == []


def _raw(wpos, fpos, frot=None):
    wingc = {"id": "wing", "type": "structure",
             "geometry": {"generator": "wing_panel", "params": {
                 "airfoil_file": DAT, "span": 400, "root_chord": 200, "tip_chord": 200, "part": "core",
                 "hinge_frac": 0.75, "cut_files": ["meshes/flap.stl", "meshes/gone.stl"]}},
             "position": wpos}
    flapc = {"id": "flap", "type": "other", "geometry": {"mesh": {"file": "meshes/flap.stl"}}, "position": fpos,
             "mass_g": 1}
    if frot:
        flapc["rotation_deg"] = frot
    return {"components": [wingc, flapc]}


def test_resolver_derives_cut_poses(tmp_path):
    raw = _raw([0, 0, 0], [10, 20, 30], [0, 0, 90])
    data, _ = resolve_design_data(raw, tmp_path)
    (e,) = data["components"][0]["geometry"]["params"]["cut_poses"]
    assert e["file"] == "meshes/flap.stl"
    assert e["matrix"] == pytest.approx([0, -1, 0, 10, 1, 0, 0, 20, 0, 0, 1, 30], abs=1e-9)
    assert "cut_poses" not in raw["components"][0]["geometry"]["params"]
    data, _ = resolve_design_data(_raw([0, 0, 0], [0, 0, 0]), tmp_path)
    assert "cut_poses" not in data["components"][0]["geometry"]["params"]
    data, _ = resolve_design_data(_raw([5, 0, 0], [10, 20, 30]), tmp_path)
    (e,) = data["components"][0]["geometry"]["params"]["cut_poses"]
    assert e["matrix"] == pytest.approx([1, 0, 0, 5, 0, 1, 0, 20, 0, 0, 1, 30], abs=1e-9)


def test_moving_a_neighbour_moves_its_pocket(tmp_path):
    from hangar.checks import _overlap_volume
    for sub, pos in (("a", (0, 0, 0)), ("moved", (35, 0, 0))):
        design = load_design(_design(tmp_path / sub, flap_pos=pos))
        wp = component_parts(design.component("wing"), design.base_dir)
        fp = component_parts(design.component("flap"), design.base_dir)
        assert abs(sum(m.volume for m in wp)) == pytest.approx(694000, rel=1e-6)
        assert _overlap_volume(wp, fp) < 1.0
    assert "cut_poses" not in design.raw["components"][0]["geometry"]["params"]
    (e,) = design.data["components"][0]["geometry"]["params"]["cut_poses"]
    assert e["matrix"] == pytest.approx([1, 0, 0, 35, 0, 1, 0, 0, 0, 0, 1, 0])


def test_design_set_move_reports_the_wing_as_regenerated(tmp_path):
    d = _design(tmp_path / "src")
    s = tmp_path / "s"
    shutil.copytree(d, s)
    r = call("design.set", path=str(s), key="components[flap].position[0]", value="35", why="move flap")
    assert r.ok, r.messages
    assert "wing" in r.data["regenerated"]["components"]


def test_t1_pocket_flags_a_part_in_uncut_core(tmp_path):
    design = load_design(_design(tmp_path, flap_pos=(35, 0, 0)))
    design.data["components"][0]["geometry"]["params"].pop("cut_poses")
    (row,) = _rows(design)
    assert row.status == "FAIL"
    assert row.message.startswith(MSG_STALE.format(c="flap", v=6000))
    assert row.data["volume_mm3"] == pytest.approx(6000, rel=1e-3)
    assert row.data["listed"] is True


def test_t1_pocket_flags_an_unlisted_attached_part(tmp_path):
    (row,) = _rows(load_design(_design(tmp_path, horn=True)))
    assert row.status == "FAIL"
    assert row.message == ("horn: 400 mm^3 of it sits in uncut core of wing; it is attached to wing but its mesh "
                           "file is not in wing's cut_files")
    assert row.data["listed"] is False and row.data["part"] == "horn"


def test_t1_pocket_passes_when_every_pocket_is_cut(tmp_path):
    for sub, pos in (("a", (0, 0, 0)), ("m", (35, 0, 0))):
        (row,) = _rows(load_design(_design(tmp_path / sub, flap_pos=pos)))
        assert row.status == "PASS"
        assert row.message == "wing: no part it is cut for or attached to sits in uncut core"


def test_designs_without_a_wing_panel_get_no_pocket_row():
    assert _rows(load_design(REPO / "designs" / "example-tailsitter-wing")) == []


def test_concept_a_param_pockets_unchanged():
    design = load_design(REPO / "designs" / "concept-a-param")
    assert "cut_poses" not in design.component("wng-001")["geometry"]["params"]
    (row,) = _rows(design)
    assert row.status == "PASS"
