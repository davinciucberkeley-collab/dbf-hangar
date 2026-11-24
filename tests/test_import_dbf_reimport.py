import numpy as np
import pytest

from hangar.importers import dbf, dbf_geometry as geo


def _cube(side_m):
    s = side_m / 2
    v = [(-s,-s,-s),(s,-s,-s),(s,s,-s),(-s,s,-s),(-s,-s,s),(s,-s,s),(s,s,s),(-s,s,s)]
    t = [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return {"kind": "mesh", "name": "cube", "verts": [list(p) for p in v], "tris": [list(x) for x in t]}

def test_mesh_kind_volume_in_mm3():
    m = geo.body_mesh(_cube(0.01))                      # a 10 mm cube given in metres
    assert m.is_watertight and m.volume == pytest.approx(1000.0, rel=1e-6)
    assert np.allclose(m.bounds, [[-5, -5, -5], [5, 5, 5]], atol=1e-6)

def test_mesh_kind_without_triangles_is_a_geometry_error():
    with pytest.raises(geo.GeometryError):
        geo.body_mesh({"kind": "mesh", "verts": [[0, 0, 0]], "tris": []})

def test_retention_n_ignores_non_numeric():
    assert dbf._retention_n({"retention": {"load_n": 38.8}}) == 38.8
    assert dbf._retention_n({"retention": {"load_n": "none (pneumatic)"}}) is None
    assert dbf._retention_n({"retention": {"load_n": 0}}) is None
    assert dbf._retention_n({}) is None

def test_conn_method_knows_pitot_tubing():
    assert dbf.CONN_METHOD["CT-PITOT-TUBING"][0] == "press-fit"


# ---------------------------------------------------------------- part 1b: the blocks
import csv
from pathlib import Path

import yaml

from hangar.importers import dbf_blocks as blk

DBF = Path("C:/Users/trist/DBF-Combined")
HAVE_DBF = (DBF / "redesign/qp/A/BOM-A.csv").exists()
HDR = "id,subsystem,item,ship_group,qty,spares,unit_usd,flag,status,source_url,date_checked,note"
PARTS = {"WNG-001": {"part_id": "WNG-001", "vendor_or_file": "Made from BOM P01 ..."}}


def _bom(tmp_path, *rows):
    d = tmp_path / "redesign/qp/A"
    d.mkdir(parents=True)
    (d / "BOM-A.csv").write_text("\n".join([HDR, *rows]) + "\n", encoding="utf-8")
    return tmp_path


def _items(text):
    return yaml.safe_load(text)["bom"]["items"]


def test_bom_block_maps_a_verified_line(tmp_path):
    root = _bom(tmp_path, "P01,propulsion,T-Motor MN2212,TMotor,5,1,46.90,V,verified,https://store.tmotor.com/x,2026-11-14,note")
    (item,) = _items(blk.bom_block(root, "A", PARTS, "a93f14d"))
    assert item == {"id": "p01", "qty": 5, "supplier": "TMotor", "part_number": "T-Motor MN2212", "unit_cost_usd": 46.9,
                    "url": "https://store.tmotor.com/x", "component_ids": ["wng-001"],
                    "verified": {"by": "DBF-Combined BOM-A.csv @ a93f14d", "date": "2026-11-14", "method": "browser"}}


def test_bom_block_qty_already_includes_spares_and_is_not_added_to(tmp_path):  # T94
    root = _bom(tmp_path,
                "P01,propulsion,T-Motor MN2212 (4 + 1 spare),TMotor,5,1,46.90,V,unverified,-,-,n",
                "M01,mechanisms,Servo (2 elevons + 1 spare),RMRC,3,1,13.99,V,unverified,-,-,n",
                "P02,propulsion,Props,RMRC,1,0,9.40,V,unverified,-,-,n")
    items = {i["id"]: i for i in _items(blk.bom_block(root, "A", {}, "a93f14d"))}
    assert [items[k]["qty"] for k in ("p01", "m01", "p02")] == [5, 3, 1]
    assert items["p01"]["part_number"] == "T-Motor MN2212 (4 + 1 spare)"
    assert "spares" not in items["p01"]


def test_bom_block_unverified_line_has_no_verified_and_no_url(tmp_path):
    root = _bom(tmp_path, "P02,x,Thing,Grp,2,,10.00,V,unverified,-,-,n")
    (item,) = _items(blk.bom_block(root, "A", PARTS, "a93f14d"))
    assert "verified" not in item and "url" not in item and "component_ids" not in item and item["qty"] == 2


def test_bom_block_unverified_with_url_keeps_url(tmp_path):
    root = _bom(tmp_path, "B03,x,Thing,Grp,1,0,3.00,V,unverified,https://e.com/a,-,n")
    (item,) = _items(blk.bom_block(root, "A", PARTS, "a93f14d"))
    assert item["url"] == "https://e.com/a" and "verified" not in item


def test_bom_block_loads_through_the_schema(tmp_path):
    root = _bom(tmp_path, "P01,propulsion,T-Motor MN2212,TMotor,5,1,46.90,V,verified,https://store.tmotor.com/x,2026-11-14,note",
                "P02,x,Thing,Grp,2,,10.00,V,unverified,-,-,n")
    fx = yaml.safe_load((Path(__file__).parent / "fixtures/pdl-v1-full.yaml").read_text())
    fx["bom"] = yaml.safe_load(blk.bom_block(root, "A", {}, "a93f14d"))["bom"]
    from hangar.checks import tier0_schema
    from hangar.design import Design
    res = tier0_schema(Design(fx, tmp_path / "plane.yaml")).results
    assert all(r.status == "PASS" for r in res if r.check_id == "T0.schema"), [r.message for r in res]


@pytest.mark.skipif(not HAVE_DBF, reason="DBF-Combined clone not present")
def test_concept_a_bom_total_matches_source():
    parts = {r["part_id"]: r for r in csv.DictReader((DBF / "redesign/qp/A/cad/out/parts-a.csv").open(encoding="utf-8"))}
    items = _items(blk.bom_block(DBF, "A", parts, "a93f14d"))
    rows = list(csv.DictReader((DBF / "redesign/qp/A/BOM-A.csv").open(encoding="utf-8")))
    want = sum(int(r["qty"]) * float(r["unit_usd"]) for r in rows)
    got = sum(i["qty"] * i["unit_cost_usd"] for i in items)
    assert got == pytest.approx(want, abs=0.01) and got == pytest.approx(1262.50, abs=0.01)
    assert len(items) == 42 and sum(1 for i in items if "verified" in i) == 26
    assert all(i["url"] and i["verified"]["date"] for i in items if "verified" in i)


def test_files_block_lists_every_mesh():
    f = yaml.safe_load(blk.files_block(["a", "b"], "a93f14d"))["files"]["cad"]
    assert [e["path"] for e in f] == ["meshes/a.stl", "meshes/b.stl"]
    assert all(e["role"] == "derived" and e["format"] == "stl" for e in f)


def test_wiring_block_renames_e_hrn_13():
    edges = [{"id": "E-HRN-12", "part_a": "HRN-002", "part_b": "PRP-003"}, {"id": "E-HRN-13", "part_a": "PWR-001", "part_b": "HRN-002"}]
    h = yaml.safe_load(blk.wiring_block(edges, {"E-HRN-12", "E-HRN-13"}, "a93f14d"))["wiring"]["harnesses"]
    assert h == [{"id": "e-hrn-12", "from": "hrn-002", "to": "prp-003"}, {"id": "hrn-bat", "from": "pwr-001", "to": "hrn-002"}]


def test_wiring_block_ignores_non_wire_edges():
    edges = [{"id": "E-WNG-01", "part_a": "A", "part_b": "B"}, {"id": "E-HRN-01", "part_a": "C", "part_b": "D"}]
    h = yaml.safe_load(blk.wiring_block(edges, {"E-HRN-01"}, "a93f14d"))["wiring"]["harnesses"]
    assert [x["id"] for x in h] == ["e-hrn-01"]


def test_transport_block_one_group():
    t = yaml.safe_load(blk.transport_block(["b", "a", "hrd-001", "hrn-001"]))["transport"]["disassembly"]
    assert t == [{"group": "packed-airframe", "component_ids": ["a", "b"]}]


def test_assembly_block_folds_markers_and_adds_proxies():
    steps = [{"id": "A1", "caption": "c1", "parts": ["WNG-001"]}, {"id": "M1", "caption": "lay", "parts": []},
             {"id": "A2", "caption": "c2", "parts": ["AVN-001"]}]
    s = yaml.safe_load(blk.assembly_block(steps, ["wng-001", "avn-001", "hrd-001", "hrn-001"]))["assembly"]["sequence"]
    assert [x["step"] for x in s] == [1, 2, 3]
    assert s[1]["add"] == ["avn-001"] and "before this step, M1: lay" in s[1]["note"] and s[0]["note"] == "A1: c1"
    assert s[2]["add"] == ["hrd-001", "hrn-001"]


def test_assembly_block_rejects_an_unplaced_real_component():
    steps = [{"id": "A1", "caption": "c1", "parts": ["WNG-001"]}]
    with pytest.raises(ValueError, match="zzz-001"):
        blk.assembly_block(steps, ["wng-001", "zzz-001", "hrd-001", "hrn-001"])


@pytest.mark.skipif(not HAVE_DBF, reason="DBF-Combined clone not present")
def test_dump_exposes_assembly_steps():
    d = dbf._run_dump(DBF, "A")
    real = [s for s in d["assembly_steps"] if s["parts"]]
    assert len(d["assembly_steps"]) == 50 and len(real) == 43
    import json
    want = [s["id"] for s in json.loads((DBF / "redesign/qp/A/cad/out/assembly.json").read_text(encoding="utf-8"))["steps"]]
    assert [s["id"] for s in real] == want
