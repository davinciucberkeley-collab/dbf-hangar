from __future__ import annotations
import copy, json, os, re, shutil
import pytest
import yaml
from click.testing import CliRunner
from hangar.checks import tier0_schema, validate
from hangar.cli import cli
from hangar.design import Design, REPO_ROOT, SCHEMA_PATH, list_designs, load_design
from hangar.migrate import LATEST, KNOWN_VERSIONS, bump_version_text, migrate
from hangar.ops import call
from hangar.pdlref import build_reference

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "pdl-v1-full.yaml"
EXAMPLE = REPO_ROOT / "designs" / "example-tailsitter-wing" / "plane.yaml"
DESIGNS = list_designs()
IDS = [p.parent.name for p in DESIGNS]
# Per-design migrate+validate cases that take more than about 5 s (from --durations) are slow.
SLOW_DESIGN_IDS = {"concept-a", "c0-a1", "c0-a2", "c0-a3", "c0-lift-cruise", "tiltwing-cakir"}
VERDICT_PARAMS = [pytest.param(p, id=i, marks=pytest.mark.slow) if i in SLOW_DESIGN_IDS
                  else pytest.param(p, id=i) for p, i in zip(DESIGNS, IDS)]
# Frozen pre-1.0 copies of the committed designs (from the base commit), so migration tests
# do not depend on what designs/ holds at any given commit.
LEGACY_DIR = REPO_ROOT / "tests" / "fixtures" / "pdl-legacy"
LEGACY_EXAMPLE = LEGACY_DIR / "example-tailsitter-wing.yaml"
LEGACY_DESIGNS = [LEGACY_DIR / f"{i}.yaml" for i in
                  ["c0-a1", "c0-a2", "c0-a3", "c0-lift-cruise", "example-tailsitter-wing", "tiltwing-cakir"]]
LEGACY_DESIGNS.append(REPO_ROOT / "tests" / "fixtures" / "concept-a-frozen" / "plane.yaml")
LEGACY_IDS = [p.stem if p.parent == LEGACY_DIR else p.parent.name for p in LEGACY_DESIGNS]


def _example_data():
    return copy.deepcopy(load_design(EXAMPLE).data)


@pytest.mark.parametrize("d", VERDICT_PARAMS)
def test_every_committed_design_migrates_to_1_0_with_same_verdict(d):
    before = validate(load_design(d)).accepted
    data, _ = migrate(load_design(d).data)
    assert data["schema_version"] == "1.0"
    assert validate(Design(data, d)).accepted == before


@pytest.mark.parametrize("d", DESIGNS, ids=IDS)
def test_migrated_tier0_results_match_for_every_design(d):
    a = [(r.check_id, r.status) for r in tier0_schema(load_design(d)).results]
    b = [(r.check_id, r.status)
         for r in tier0_schema(Design(migrate(load_design(d).data)[0], d)).results]
    assert a == b


def test_migrate_does_not_mutate_input_and_is_idempotent():
    data = copy.deepcopy(load_design(LEGACY_EXAMPLE).data)
    orig = copy.deepcopy(data)
    out, _ = migrate(data)
    assert data == orig and data["schema_version"] == "0.1"
    again, notes = migrate(out)
    assert again == out and notes == ["already 1.0"]


def test_migrate_rejects_unknown_or_missing_version():
    data = _example_data()
    data["schema_version"] = "9"
    with pytest.raises(ValueError):
        migrate(data)
    del data["schema_version"]
    with pytest.raises(ValueError):
        migrate(data)


@pytest.mark.parametrize("v", ["0.1", "0.2", "0.3", "0.4"])
def test_migrate_notes_for_each_old_version(v):
    data = _example_data()
    data["schema_version"] = v
    _, notes = migrate(data)
    assert notes == [f"schema_version {v} -> 1.0",
                     "no fields added, removed or renamed (all 1.0 blocks are optional)"]


def test_bump_version_text_keeps_crlf_comments_and_other_bytes():
    text = '# head\r\nschema_version: "0.2"  # keep me\r\nid: x\r\n'
    assert bump_version_text(text) == '# head\r\nschema_version: "1.0"  # keep me\r\nid: x\r\n'
    assert bump_version_text("schema_version: '0.3'\nid: x\n") == 'schema_version: "1.0"\nid: x\n'
    assert bump_version_text("schema_version: 0.1\nid: x\n") == 'schema_version: "1.0"\nid: x\n'


def test_bump_version_text_rejects_missing_or_duplicate_or_already_1_0():
    for bad in ("id: x\n", 'schema_version: "0.1"\nschema_version: "0.2"\n', 'schema_version: "1.0"\n'):
        with pytest.raises(ValueError):
            bump_version_text(bad)


@pytest.mark.parametrize("d", LEGACY_DESIGNS, ids=LEGACY_IDS)
def test_bump_changes_only_the_version_line_of_every_committed_design(d):
    old = d.read_bytes().decode("utf-8")
    new = bump_version_text(old)
    a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
    assert len(a) == len(b)
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(diff) == 1
    assert b[diff[0]].startswith('schema_version: "1.0"')


def test_v1_blocks_validate():
    assert tier0_schema(load_design(FIXTURE)).status == "PASS"


def test_v1_blocks_need_schema_version_1_0():
    data = copy.deepcopy(load_design(FIXTURE).data)
    data["schema_version"] = "0.4"
    res = tier0_schema(Design(data, FIXTURE))
    assert any(r.check_id == "T0.version" and r.status == "FAIL" and "files" in r.message
               for r in res.results)


def test_features_of_old_versions_are_valid_at_1_0():
    data = _example_data()
    data["components"].append({"id": "hw", "type": "other", "geometry": {"point_mass": {}},
                               "position": [100, 0, 0], "mass_g": 5})
    data["attachments"].append({"parent": "center_body", "child": "hw", "method": "glued",
                                "location": [100, 0, 0], "rated_load_n": 5,
                                "kinematic_link": True, "rating_basis": "placeholder"})
    data["schema_version"] = "1.0"
    assert tier0_schema(Design(data, EXAMPLE)).status == "PASS"
    data["schema_version"] = "0.3"
    res = tier0_schema(Design(data, EXAMPLE))
    assert any(r.check_id == "T0.version" and r.status == "FAIL" for r in res.results)


@pytest.mark.parametrize("bad", ["cad\\x.step", "C:/x/y.step", "/abs/y.step", "../y.step", "a/../y.step"])
def test_file_paths_must_be_relative_with_forward_slashes(bad):
    data = copy.deepcopy(load_design(FIXTURE).data)
    data["files"]["cad"][0]["path"] = bad
    assert tier0_schema(Design(data, FIXTURE)).status == "FAIL"
    for good in ("cad/sub dir/x.step", "a..b/x.step"):
        data["files"]["cad"][0]["path"] = good
        assert tier0_schema(Design(data, FIXTURE)).status == "PASS"


def test_schema_is_v1_and_lists_all_versions():
    s = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert s["title"] == "Plane Design Language v1.0"
    assert s["properties"]["schema_version"]["enum"] == ["0.1", "0.2", "0.3", "0.4", "1.0"]
    assert KNOWN_VERSIONS == ("0.1", "0.2", "0.3", "0.4", "1.0")
    assert LATEST == "1.0"


def test_schema_file_is_canonical_json():
    raw = SCHEMA_PATH.read_bytes()
    assert raw == (json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def test_reference_doc_is_current():
    assert (REPO_ROOT / "docs/pdl/reference.md").read_bytes() == build_reference().encode("utf-8")


def test_reference_covers_every_property_and_def():
    text = build_reference()
    s = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for name in s["$defs"]:
        assert f"### `{name}`" in text
    for name in s["properties"]:
        assert f"| `{name}` |" in text


def test_readme_excerpts_are_verbatim():
    readme = (REPO_ROOT / "docs/pdl/README.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    blocks = re.findall(r"<!-- excerpt: (\S+) -->\n```yaml\n(.*?)```", readme, re.DOTALL)
    assert len(blocks) >= 3
    for name, body in blocks:
        src = (REPO_ROOT / name).read_text(encoding="utf-8").replace("\r\n", "\n")
        assert body in src


def _copy_example(tmp_path, crlf=True):
    dst = tmp_path / "d"
    shutil.copytree(EXAMPLE.parent, dst)
    f = dst / "plane.yaml"
    if crlf:
        f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))
    return dst


def _copy_legacy_example(tmp_path, crlf=True):
    dst = tmp_path / "d"
    dst.mkdir()
    f = dst / "plane.yaml"
    f.write_bytes(LEGACY_EXAMPLE.read_bytes())
    if crlf:
        f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))
    return dst


def test_schema_docs_op_writes_same_bytes(tmp_path):
    r = call("schema.docs", out=tmp_path / "ref.md")
    assert r.ok
    assert (tmp_path / "ref.md").read_bytes() == (REPO_ROOT / "docs/pdl/reference.md").read_bytes()


def test_migrate_op_dry_run_writes_nothing(tmp_path):
    d = _copy_example(tmp_path)
    before = (d / "plane.yaml").read_bytes()
    r = call("design.migrate", path=str(d))
    assert r.ok and r.data["to_version"] == "1.0" and r.data["written"] is False
    assert (d / "plane.yaml").read_bytes() == before


def test_migrate_op_write_changes_only_version_line_and_keeps_crlf(tmp_path):
    d = _copy_legacy_example(tmp_path)
    old = (d / "plane.yaml").read_bytes()
    r = call("design.migrate", path=str(d), write=True)
    assert r.ok and r.data["written"] is True
    new = (d / "plane.yaml").read_bytes()
    a, b = old.decode().splitlines(keepends=True), new.decode().splitlines(keepends=True)
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(a) == len(b) and len(diff) == 1 and b[diff[0]].startswith('schema_version: "1.0"')
    assert new.count(b"\r\n") == old.count(b"\r\n")
    assert tier0_schema(load_design(d)).status == "PASS"
    r2 = call("design.migrate", path=str(d), write=True)
    assert r2.ok and r2.data["written"] is False and r2.data["notes"] == ["already 1.0"]


@pytest.mark.parametrize("src", DESIGNS, ids=IDS)
def test_migrate_op_write_on_copy_of_every_committed_design(tmp_path, src):
    dst = tmp_path / src.parent.name
    dst.mkdir()
    shutil.copy2(src, dst / "plane.yaml")
    r = call("design.migrate", path=str(dst), write=True)
    assert r.ok
    assert tier0_schema(load_design(dst / "plane.yaml")).status == tier0_schema(load_design(src)).status
    assert load_design(dst / "plane.yaml").data["schema_version"] == "1.0"


def test_migrate_op_bad_input(tmp_path):
    r = call("design.migrate", path=str(tmp_path))
    assert r.ok is False and r.data["error"] == "input" and r.exit_code == 2
    assert list(tmp_path.iterdir()) == []
    d = _copy_legacy_example(tmp_path, crlf=False)
    f = d / "plane.yaml"
    f.write_text(f.read_text(encoding="utf-8").replace('schema_version: "0.1"', 'schema_version: "9"'), encoding="utf-8", newline="")
    r = call("design.migrate", path=str(d), write=True)
    assert r.ok is False and r.data["error"] == "input" and r.exit_code == 2
    d2 = tmp_path / "e"
    d2.mkdir()
    f2 = d2 / "plane.yaml"
    f2.write_bytes(LEGACY_EXAMPLE.read_bytes())
    f2.write_bytes(f2.read_bytes().replace(b"status: designed", b"status: nope").replace(b"status: concept", b"status: nope"))
    before = f2.read_bytes()
    assert b"status: nope" in before
    r = call("design.migrate", path=str(d2), write=True)
    assert r.ok is False and "error" not in r.data and r.exit_code == 1
    assert f2.read_bytes() == before


def test_plane_schema_default_still_prints_path():
    res = CliRunner().invoke(cli, ["schema"])
    assert res.exit_code == 0 and res.output.strip() == str(SCHEMA_PATH)


def test_cli_schema_docs_json(tmp_path):
    res = CliRunner().invoke(cli, ["schema", "docs", "--out", str(tmp_path / "r.md"), "--json"])
    assert res.exit_code == 0
    assert (tmp_path / "r.md").read_bytes() == (REPO_ROOT / "docs/pdl/reference.md").read_bytes()


def test_cli_design_migrate_json(tmp_path):
    d = _copy_example(tmp_path)
    res = CliRunner().invoke(cli, ["design", "migrate", str(d), "--json"])
    assert res.exit_code == 0
    assert json.loads(res.output)["data"]["to_version"] == "1.0"


@pytest.mark.skipif(os.name != "nt", reason="backslash paths are a Windows form")
def test_migrate_op_accepts_backslash_path(tmp_path):
    d = _copy_example(tmp_path)
    r = call("design.migrate", path=str(d).replace("/", "\\"))
    assert r.ok and r.data["to_version"] == "1.0"
