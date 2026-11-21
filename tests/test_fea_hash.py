"""D13/D18: what FEA's stored-result hash does and does not depend on."""
import json
import shutil

import pytest
import yaml

import hangar.design as design_mod
import hangar.fea as fea
from hangar.design import DESIGNS_DIR, load_design

PART = "wng-004-l"


@pytest.fixture(scope="module")
def concept_a():
    return load_design(DESIGNS_DIR / "concept-a" / "plane.yaml")


@pytest.fixture
def edit_standards(tmp_path, monkeypatch):
    def edit(fn):
        std = yaml.safe_load(design_mod.STANDARDS_PATH.read_text(encoding="utf-8"))
        fn(std)
        p = tmp_path / "std.yaml"
        p.write_text(yaml.safe_dump(std, sort_keys=False), encoding="utf-8")
        monkeypatch.setattr(design_mod, "STANDARDS_PATH", p)
    return edit


def edit_plane(tmp_path, fn, name="concept-a"):
    dst = tmp_path / name
    shutil.copytree(DESIGNS_DIR / "concept-a", dst)
    data = yaml.safe_load((dst / "plane.yaml").read_text(encoding="utf-8"))
    fn(data)
    (dst / "plane.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return load_design(dst / "plane.yaml")


def _comp(data, cid):
    return next(c for c in data["components"] if c["id"] == cid)


def _other(data):
    return next(c for c in data["components"] if c["id"] != PART and "description" in c)


def test_unrelated_standards_key_leaves_hash_unchanged(concept_a, edit_standards):
    before = fea.part_hash(concept_a, PART)
    edit_standards(lambda s: s["aero"]["static_margin"].update(value=0.99))
    assert fea.part_hash(concept_a, PART) == before


def test_non_value_edits_leave_hash_unchanged(concept_a, edit_standards):
    before = fea.part_hash(concept_a, PART)

    def fn(s):
        s["structure"]["landing_load_factor"]["source"] = "decided"
        s["structure"]["fea_allowable_printed_petg_mpa"]["source"] = "other"
    edit_standards(fn)
    assert fea.part_hash(concept_a, PART) == before


@pytest.mark.parametrize("section,key", [("structure", "ultimate_factor"),
                                         ("structure", "fea_allowable_printed_petg_mpa"),
                                         ("structure", "fea_singularity_band_mm"),
                                         ("sim", "drop_height_m"), ("sim", "duration_s"),
                                         ("structure", "fea_material_printed_petg")])
def test_fea_key_value_change_changes_hash(concept_a, edit_standards, section, key):
    before = fea.part_hash(concept_a, PART)

    def fn(s):
        if key == "fea_material_printed_petg":
            s[section][key]["value"]["youngs_modulus_mpa"] = 1
        else:
            s[section][key]["value"] = s[section][key]["value"] + 1.0
    edit_standards(fn)
    assert fea.part_hash(concept_a, PART) != before


def test_every_standards_key_fea_reads_is_in_the_hash_list():
    listed = fea.FEA_STANDARDS_KEYS["structure"]
    for _mid, allow, mat in fea.MATERIALS.values():
        assert allow in listed and mat in listed
    assert "ultimate_factor" in listed and "fea_singularity_band_mm" in listed
    std = yaml.safe_load(design_mod.STANDARDS_PATH.read_text(encoding="utf-8"))
    for sec, keys in fea.FEA_STANDARDS_KEYS.items():
        for k in keys:
            assert k in std[sec]


def test_committed_concept_a_results_are_fresh(concept_a):
    files = sorted((DESIGNS_DIR / "concept-a" / "fea").glob("*.json"))
    assert files
    for f in files:
        assert json.loads(f.read_text(encoding="utf-8"))["hash"] == fea.part_hash(concept_a, f.stem), f.name


def test_unrelated_standards_edit_keeps_scorecard_fresh(tmp_path, edit_standards):
    dst = tmp_path / "concept-a"
    shutil.copytree(DESIGNS_DIR / "concept-a", dst)
    edit_standards(lambda s: s["aero"]["static_margin"].update(value=0.99))
    rows = fea.tier2_fea(load_design(dst / "plane.yaml"))
    assert not any("out of date" in r.message for r in rows)
    assert any(r.status in ("PASS", "FAIL", "WARN") for r in rows)


def test_other_components_non_load_fields_leave_part_fresh(tmp_path):
    def fn(d):
        o = _other(d)
        o["description"] = "changed text"
        o["manufacturing"] = {"method": "other"}
        d["name"] = "renamed"
    assert fea.part_hash(edit_plane(tmp_path, fn, "a"), PART) == \
        fea.part_hash(edit_plane(tmp_path, lambda d: None, "b"), PART)


def test_comment_and_formatting_edits_leave_part_fresh(tmp_path):
    base = edit_plane(tmp_path, lambda d: None, "a")
    b = edit_plane(tmp_path, lambda d: None, "b")
    p = b.base_dir / "plane.yaml"
    p.write_text(p.read_text(encoding="utf-8") + "\n# note\n", encoding="utf-8")
    assert fea.part_hash(load_design(p), PART) == fea.part_hash(base, PART)


def test_other_components_mass_makes_part_stale(tmp_path):
    def fn(d):
        _other(d)["mass_g"] += 1.0
    assert fea.part_hash(edit_plane(tmp_path, fn, "a"), PART) != \
        fea.part_hash(edit_plane(tmp_path, lambda d: None, "b"), PART)


def test_own_geometry_edit_makes_part_stale(tmp_path):
    def fn(d):
        _comp(d, PART)["position"][0] += 1.0
    assert fea.part_hash(edit_plane(tmp_path, fn, "a"), PART) != \
        fea.part_hash(edit_plane(tmp_path, lambda d: None, "b"), PART)


def test_attachment_edit_makes_part_stale(tmp_path):
    def fn(d):
        a = next(a for a in d["attachments"] if PART in (a.get("parent"), a.get("child")))
        a["location"][0] += 1.0
    assert fea.part_hash(edit_plane(tmp_path, fn, "a"), PART) != \
        fea.part_hash(edit_plane(tmp_path, lambda d: None, "b"), PART)


def test_other_components_mesh_bytes_make_part_stale(tmp_path):
    b = edit_plane(tmp_path, lambda d: None, "b")
    before = fea.part_hash(b, PART)
    c = next(c for c in b.components if c["id"] != PART
             and ((c.get("geometry") or {}).get("mesh") or {}).get("file")
             and (b.base_dir / c["geometry"]["mesh"]["file"]).is_file())
    with open(b.base_dir / c["geometry"]["mesh"]["file"], "ab") as fh:
        fh.write(b"\0")
    assert fea.part_hash(b, PART) != before
