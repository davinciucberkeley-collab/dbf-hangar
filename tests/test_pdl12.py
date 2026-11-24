"""U4.21: PDL 1.2 generator geometry, parameters, references, regeneration on design set (hand numbers from the brief)."""
from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest
import trimesh
import yaml

from hangar.checks import tier0_schema
from hangar.design import DESIGNS_DIR, Design, load_design
from hangar.export import export_glb, export_stl, to_scene
from hangar.fea import part_hash
from hangar.geom.params import find_references, resolve_references
from hangar.geom.resolve import resolve_design_data
from hangar.geometry import component_parts
from hangar.mass import mass_properties
from hangar.ops import call

FIXTURES = Path(__file__).parent / "fixtures"
GEN = FIXTURES / "pdl-gen"


def _copy(tmp_path) -> Path:
    dst = tmp_path / "gen-rod"
    shutil.copytree(GEN, dst)
    return dst


def test_fixture_passes_tier0():
    d = load_design(GEN)
    assert d.raw is not None
    c = d.data["components"][0]
    assert c["mass_g"] == pytest.approx(4.5110, abs=1e-3)
    assert c["geometry"]["params"]["length"] == 100
    assert d.raw["components"][0]["geometry"]["params"]["length"] == "$rod_len_mm"
    res = tier0_schema(d)
    assert res.status == "PASS"
    rows = {r.check_id: r.status for r in res.results}
    assert rows["T0.parameters"] == "PASS" and rows["T0.generator"] == "PASS"


def test_mass_and_cg_hand_numbers():
    mp = mass_properties(load_design(GEN))
    assert mp["mass_g"] == pytest.approx(14.5110, abs=1e-3)
    assert mp["cg_mm"][0] == pytest.approx(68.91, abs=0.01)


def test_find_and_resolve_references():
    data = {"parameters": {"a": 5, "b": 7}, "components": [{
        "id": "c", "description": "$a", "material": "$a",
        "geometry": {"generator": "tube", "params": {"length": "$a", "center": [0, "$b", 0], "nested": {"k": ["$a"]}}},
        "planform": {"span": "$a"}, "position": ["$a", 0, "$nope"], "rotation_deg": [0, "$b", 0]}]}
    orig = copy.deepcopy(data)
    refs = set(find_references(data))
    assert ("c", "geometry.params.length", "a") in refs
    assert ("c", "geometry.params.center[1]", "b") in refs
    assert ("c", "geometry.params.nested.k[0]", "a") in refs
    assert ("c", "planform.span", "a") in refs
    assert ("c", "position[0]", "a") in refs
    assert ("c", "position[2]", "nope") in refs
    assert ("c", "rotation_deg[1]", "b") in refs
    assert not any(p in ("description", "material") for _, p, _ in refs)
    out = resolve_references(data)
    assert data == orig
    c = out["components"][0]
    assert c["description"] == "$a" and c["material"] == "$a"
    assert c["geometry"]["params"]["length"] == 5 and c["geometry"]["params"]["center"] == [0, 7, 0]
    assert c["geometry"]["params"]["nested"] == {"k": [5]}
    assert c["planform"]["span"] == 5 and c["rotation_deg"] == [0, 7, 0]
    assert c["position"] == [5, 0, "$nope"]


def _mut_param(d):
    d["components"][0]["geometry"]["params"]["length"] = "$nope"


def _mut_gen(d):
    d["components"][0]["geometry"]["generator"] = "nope"


def _mut_od(d):
    d["components"][0]["geometry"]["params"]["outer_d"] = 6


def _mut_mat(d):
    d["components"][0]["mass_model"]["material"] = "unobtainium"


def _mut_box(d):
    d["components"][1]["geometry"] = {"box": {"size": [1, 1, 1]}}
    d["components"][1]["mass_model"] = {"density_g_cm3": 1.0}
    del d["components"][1]["mass_g"]


def _mut_both(d):
    d["components"][0]["mass_g"] = 5


def _mut_old(d):
    d["schema_version"] = "1.1"


def _mut_badname(d):
    d["parameters"]["Bad-Name"] = 3


@pytest.mark.parametrize("mut,check,needle", [
    (_mut_param, "T0.parameters", "rod"),
    (_mut_gen, "T0.generator", "tube"),
    (_mut_od, "T0.generator", "rod"),
    (_mut_mat, "T0.generator", "rod"),
    (_mut_box, "T0.generator", "ballast"),
    (_mut_both, "T0.schema", ""),
    (_mut_old, "T0.version", ""),
    (_mut_badname, "T0.schema", ""),
], ids=["unknown-param", "unknown-generator", "outer-below-inner", "unknown-material", "mass-model-on-box",
        "both-masses", "version-1.1", "bad-param-name"])
def test_tier0_reference_and_generator_failures(mut, check, needle):
    raw = yaml.safe_load((GEN / "plane.yaml").read_text(encoding="utf-8"))
    mut(raw)
    data, errs = resolve_design_data(raw, GEN)
    d = Design(data, GEN / "plane.yaml", raw=raw, resolve_errors=errs)
    rows = [(r.check_id, r.status, r.message) for r in tier0_schema(d).results]
    hits = [m for c, s, m in rows if c == check and s == "FAIL"]
    assert hits, rows
    assert any(needle in m for m in hits), hits


def test_old_designs_untouched():
    folders = sorted(p.parent for p in DESIGNS_DIR.glob("*/plane.yaml")) + [FIXTURES / "concept-a-frozen"]
    assert len(folders) >= 8
    for f in folders:
        d = load_design(f)
        assert d.raw is None and d.resolve_errors == {}, f
        assert not any(r.check_id in ("T0.parameters", "T0.generator") for r in tier0_schema(d).results), f


def test_design_set_parameter_regenerates(tmp_path):
    d = _copy(tmp_path)
    orig = (d / "plane.yaml").read_bytes()
    r = call("design.set", path=str(d), key="parameters.rod_len_mm", value="200", why="longer rod")
    assert r.ok, r.messages
    reg = r.data["regenerated"]
    assert reg["components"]["rod"]["mass_g"] == pytest.approx([4.5110, 9.0220], abs=1e-3)
    assert reg["mass_g"] == pytest.approx([14.5110, 19.0220], abs=1e-3)
    assert [reg["cg_mm"][0][0], reg["cg_mm"][1][0]] == pytest.approx([68.91, 52.57], abs=0.01)
    new = (d / "plane.yaml").read_bytes()
    a, b = orig.decode().splitlines(), new.decode().splitlines()
    assert len(a) == len(b)
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    assert len(diff) == 1 and "rod_len_mm" in diff[0][0] and "200" in diff[0][1]
    assert "$rod_len_mm" in new.decode()
    entries = yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert len(entries) == 1
    e = entries[0]
    assert (e["key"], e["old"], e["new"]) == ("parameters.rod_len_mm", 100, 200) and e["regenerated"] == ["rod"]
    assert mass_properties(load_design(d))["mass_g"] == pytest.approx(19.0220, abs=1e-3)


def test_design_set_generator_param_regenerates(tmp_path):
    d = _copy(tmp_path)
    r = call("design.set", path=str(d), key="components[rod].geometry.params.inner_d", value="6", why="thicker wall")
    assert r.ok, r.messages
    assert yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))[0]["regenerated"] == ["rod"]
    rod = r.data["regenerated"]["components"]["rod"]["mass_g"]
    assert rod[1] == pytest.approx(24 * 0.1305262 * (25 - 9) * 100 * 0.0016, abs=1e-3)
    assert rod[1] == pytest.approx(8.0195, abs=1e-3)


def test_design_set_failure_is_atomic(tmp_path):
    d = _copy(tmp_path)
    orig = (d / "plane.yaml").read_bytes()
    r = call("design.set", path=str(d), key="parameters.rod_od_mm", value="6", why="too thin")
    assert r.ok is False
    text = " ".join(r.messages) + str(r.data)
    assert "regeneration failed" in text and "rod" in text and "inner_d must be less than outer_d" in text
    assert (d / "plane.yaml").read_bytes() == orig
    assert not (d / "CHANGELOG.yaml").exists()


def test_design_set_unrelated_key_has_no_regeneration(tmp_path):
    d = _copy(tmp_path)
    r = call("design.set", path=str(d), key="components[ballast].mass_g", value="12", why="heavier ballast")
    assert r.ok, r.messages
    assert not r.data.get("regenerated")
    e = yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))[0]
    assert "regenerated" not in e


def test_sweep_over_a_parameter(tmp_path, monkeypatch):
    d = _copy(tmp_path)
    monkeypatch.setattr("hangar.ops.edit.SWEEP_ROOT", tmp_path / ".sweeps")
    r = call("design.sweep", path=str(d), key="parameters.rod_len_mm", values=["100", "200"])
    assert r.ok, r.messages
    rows = r.data["rows"]
    assert len(rows) == 2
    assert [x["mass_g"] for x in rows] == pytest.approx([14.511, 19.022], abs=1e-3)


def test_export_uses_generated_geometry(tmp_path):
    d = load_design(GEN)
    assert "rod" in to_scene(d).graph.nodes_geometry
    assert export_glb(d, tmp_path / "o.glb").stat().st_size > 0
    paths = export_stl(d, tmp_path / "stl")
    rod = next(p for p in paths if p.name == "rod.stl")
    assert abs(trimesh.load(rod, force="mesh").volume) == pytest.approx(2819.37, abs=0.5)
    parts = component_parts(d.component("rod"), d.base_dir)
    assert len(parts) == 1 and parts[0].is_watertight


def test_fea_part_hash_tracks_generator_params():
    a = load_design(GEN)
    raw = copy.deepcopy(a.raw)
    raw["parameters"]["rod_len_mm"] = 200
    data, errs = resolve_design_data(raw, a.base_dir)
    b = Design(data, a.path, raw=raw, resolve_errors=errs)
    assert part_hash(a, "rod") != part_hash(b, "rod")


def test_migrate_1_1_design_to_1_2(tmp_path):
    text = (FIXTURES / "pdl-v1-full.yaml").read_bytes().decode("utf-8").replace(
        'schema_version: "1.0"', 'schema_version: "1.1"', 1)
    d = tmp_path / "x"
    d.mkdir()
    (d / "plane.yaml").write_bytes(text.encode("utf-8"))
    r = call("design.migrate", path=str(d), write=True)
    assert r.ok, r.messages
    assert r.data["from_version"] == "1.1" and r.data["to_version"] == "1.2"
    new = (d / "plane.yaml").read_bytes().decode("utf-8")
    a, b = text.splitlines(keepends=True), new.splitlines(keepends=True)
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(a) == len(b) and len(diff) == 1 and b[diff[0]].startswith('schema_version: "1.2"')


def _mesh_file_design(tmp_path, with_file=True):
    from hangar.geom.kernel import box
    d = tmp_path / "mf"
    d.mkdir(parents=True)
    if with_file:
        box((10, 10, 10)).export(d / "b.stl")
    raw = yaml.safe_load((GEN / "plane.yaml").read_text(encoding="utf-8"))
    raw["components"][0]["geometry"] = {"generator": "mesh_file", "params": {"file": "b.stl"}}
    del raw["components"][0]["mass_model"]
    raw["components"][0]["mass_g"] = 5
    (d / "plane.yaml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return d


def test_t0_generator_builds_components_with_mass_g(tmp_path):
    d = _mesh_file_design(tmp_path, with_file=False)
    rows = {r.check_id: r for r in tier0_schema(load_design(d)).results}
    assert rows["T0.generator"].status == "FAIL" and "rod" in rows["T0.generator"].message
    d2 = _mesh_file_design(tmp_path / "ok")
    rows = {r.check_id: r.status for r in tier0_schema(load_design(d2)).results}
    assert rows["T0.generator"] == "PASS"


def test_fea_part_hash_tracks_mesh_file_bytes(tmp_path):
    from hangar.geom.kernel import box
    d = _mesh_file_design(tmp_path)
    h1 = part_hash(load_design(d), "rod")
    box((10, 10, 20)).export(d / "b.stl")
    assert part_hash(load_design(d), "rod") != h1
