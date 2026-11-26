"""U1.4: design.set/get/diff/copy/sweep/propose."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from hangar import design as design_mod
from hangar.ops import call
from hangar.ops import edit

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
CONCEPT_A_DIR = design_mod.REPO_ROOT / "tests" / "fixtures" / "concept-a-frozen"


@pytest.fixture
def tmp_example(tmp_path) -> Path:
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE_DIR, dst)
    return dst


@pytest.fixture
def tmp_concept_a(tmp_path) -> Path:
    dst = tmp_path / "concept-a"
    shutil.copytree(CONCEPT_A_DIR, dst, ignore=shutil.ignore_patterns("fea"))
    return dst


def _swap(raw: bytes, anchor: bytes, old: bytes, new: bytes) -> bytes:
    """Replace the first `old` that comes after `anchor`; exactly one occurrence changes."""
    i = raw.index(anchor)
    j = raw.index(old, i)
    return raw[:j] + new + raw[j + len(old):]


def test_set_changes_one_value_keeps_comments_and_logs(tmp_concept_a):
    r = call("design.set", path=str(tmp_concept_a), key="components[wng-004-l].mass_g", value="41.5",
             why="measured", kind="modify")
    assert r.ok, r.messages
    text = (tmp_concept_a / "plane.yaml").read_text(encoding="utf-8")
    assert "# " in text
    assert yaml.safe_load(text)["components"][[c["id"] for c in yaml.safe_load(text)["components"]].index("wng-004-l")]["mass_g"] == 41.5
    log = yaml.safe_load((tmp_concept_a / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert log[-1]["kind"] == "modify" and log[-1]["key"] == "components[wng-004-l].mass_g"
    assert log[-1]["old"] == 1.2 and log[-1]["new"] == 41.5 and log[-1]["why"] == "measured"


def test_set_changes_only_target_bytes_on_crlf_with_comment(tmp_example):
    p = tmp_example / "plane.yaml"
    raw = p.read_bytes().replace(b"\r\n", b"\n")
    raw = _swap(raw, b"id: battery\n", b"mass_g: 250\n", b"mass_g: 250   # measured\n")
    raw = raw.replace(b"\n", b"\r\n")
    p.write_bytes(raw)
    r = call("design.set", path=str(tmp_example), key="components[battery].mass_g", value="300", why="weighed")
    assert r.ok, r.messages
    after1 = p.read_bytes()
    assert after1 == _swap(raw, b"id: battery\r\n", b"mass_g: 250   # measured", b"mass_g: 300   # measured")
    r = call("design.set", path=str(tmp_example), key="components[battery].position[0]", value="100", why="move")
    assert r.ok, r.messages
    assert p.read_bytes() == _swap(after1, b"id: battery\r\n", b"position: [140, 0, -27.5]", b"position: [100, 0, -27.5]")
    log = (tmp_example / "CHANGELOG.yaml").read_bytes()
    assert log.count(b"\n") == log.count(b"\r\n") > 0     # the log follows the file's line endings


def test_set_rejects_bad_path_and_type_without_writing(tmp_concept_a):
    plane = tmp_concept_a / "plane.yaml"
    before = plane.read_bytes()
    a = call("design.set", path=str(tmp_concept_a), key="components[nope].mass_g", value="1", why="x")
    assert a.ok is False and a.exit_code == 2 and "nope" in " ".join(a.messages)
    b = call("design.set", path=str(tmp_concept_a), key="components[wng-004-l].mass_g", value="heavy", why="x")
    assert b.ok is False and b.exit_code == 2
    assert "mass_g" in " ".join(b.messages) and "number" in " ".join(b.messages)   # schema path and allowed type
    c = call("design.set", path=str(tmp_concept_a), key="components[wng-004-l].no_such_field", value="1", why="x")
    assert c.ok is False and c.exit_code == 2
    d = call("design.set", path=str(tmp_concept_a), key="components[wng-004-l].mass_g", value="[1, 2]", why="x")
    assert d.ok is False and d.exit_code == 2
    assert plane.read_bytes() == before
    assert not (tmp_concept_a / "CHANGELOG.yaml").exists()


def test_get_with_key_returns_value_and_without_key_returns_text(tmp_example):
    r = call("design.get", path=str(tmp_example), key="components[battery].mass_g")
    assert r.ok and r.data["value"] == 250
    r = call("design.get", path=str(tmp_example), key="components[battery].position[0]")
    assert r.data["value"] == 140
    assert call("design.get", path=str(tmp_example), key="components[nope].mass_g").exit_code == 2
    assert "id: battery" in call("design.get", path=str(tmp_example)).data["text"]


def test_diff_lists_changed_keys(tmp_example):
    call("design.set", path=str(tmp_example), key="components[battery].mass_g", value="300", why="t")
    r = call("design.diff", a=str(EXAMPLE_DIR), b=str(tmp_example))
    assert r.ok and r.data["changes"] == [{"key": "components[battery].mass_g", "a": 250, "b": 300}]
    assert call("design.diff", a=str(EXAMPLE_DIR), b=str(EXAMPLE_DIR)).data["changes"] == []


def test_copy_makes_new_design_with_new_id(tmp_path, monkeypatch):
    designs = tmp_path / "designs"
    shutil.copytree(EXAMPLE_DIR, designs / "example-tailsitter-wing")
    (designs / "example-tailsitter-wing" / "fea").mkdir()
    (designs / "example-tailsitter-wing" / "fea" / "x.json").write_text("{}")
    monkeypatch.setattr(design_mod, "DESIGNS_DIR", designs)
    r = call("design.copy", src=str(designs / "example-tailsitter-wing"), new_id="my-copy")
    assert r.ok, r.messages
    assert yaml.safe_load((designs / "my-copy" / "plane.yaml").read_text(encoding="utf-8"))["id"] == "my-copy"
    assert not (designs / "my-copy" / "fea").exists()
    assert call("design.copy", src=str(EXAMPLE_DIR), new_id="my-copy").exit_code == 2     # already exists
    assert call("design.copy", src=str(EXAMPLE_DIR), new_id="Bad Id").exit_code == 2


def test_sweep_never_touches_source(tmp_example, tmp_path, monkeypatch):
    monkeypatch.setattr(edit, "SWEEP_ROOT", tmp_path / "sweeps")
    before = (tmp_example / "plane.yaml").read_bytes()
    r = call("design.sweep", path=str(tmp_example), key="components[battery].position[0]", values=["100", "140"])
    assert r.ok, r.messages
    rows = r.data["rows"]
    assert len(rows) == 2 and [x["value"] for x in rows] == ["100", "140"]
    assert set(rows[0]) == {"value", "accepted", "mass_g", "static_margin", "stall_speed_mps", "hover_tw", "failures"}
    assert isinstance(rows[0]["failures"], list) and rows[0]["mass_g"] > 0
    assert (tmp_example / "plane.yaml").read_bytes() == before
    assert not (tmp_example / "CHANGELOG.yaml").exists()
    assert (Path(r.data["sweep_dir"]) / "1" / "plane.yaml").is_file()
    assert Path(r.data["sweep_dir"]).parent == tmp_path / "sweeps" / "example-tailsitter-wing"


def test_sweep_writes_next_to_the_designs_dir_when_plane_designs_dir_is_set(tmp_example, tmp_path, monkeypatch):  # T101
    monkeypatch.setattr(edit, "SWEEP_ROOT", tmp_path / "real-repo-sweeps")
    monkeypatch.setenv("PLANE_DESIGNS_DIR", str(tmp_path / "ws" / "designs"))
    r = call("design.sweep", path=str(tmp_example), key="components[battery].position[0]", values=["100"])
    assert r.ok, r.messages
    assert (Path(r.data["sweep_dir"]) / "1" / "plane.yaml").is_file()
    assert not (tmp_path / "real-repo-sweeps").exists()
    assert Path(r.data["sweep_dir"]).parent == tmp_path / "ws" / ".sweeps" / "example-tailsitter-wing"


def test_sweep_bad_value_exits_2_and_creates_nothing(tmp_example, tmp_path, monkeypatch):
    monkeypatch.setattr(edit, "SWEEP_ROOT", tmp_path / "sweeps")
    r = call("design.sweep", path=str(tmp_example), key="components[battery].mass_g", values=["100", "heavy"])
    assert r.ok is False and r.exit_code == 2
    assert not (tmp_path / "sweeps").exists()


def test_propose_runs_exact_git_and_gh_commands_without_network(tmp_example, tmp_path, monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, cwd):
        calls.append(list(argv))
        if "--show-toplevel" in argv:
            return str(tmp_path) + "\n"
        if "status" in argv:
            return " M designs/example-tailsitter-wing/plane.yaml\n"
        if "--abbrev-ref" in argv:
            return "main\n"
        if "create" in argv:
            return "https://github.com/o/r/pull/7\n"
        return ""

    monkeypatch.setattr(edit, "_run", fake_run)
    monkeypatch.setenv("HANGAR_GH", "gh-test")
    r = call("design.propose", path=str(tmp_example), title="Lighter battery")
    assert r.ok, r.messages
    assert r.data["pr_url"] == "https://github.com/o/r/pull/7"
    branch = "design/example-tailsitter-wing/lighter-battery"
    assert r.data["branch"] == branch
    assert ["git", "-C", str(tmp_path), "switch", "-c", branch] in calls
    assert ["git", "-C", str(tmp_path), "push", "-u", "origin", branch] in calls
    gh = [c for c in calls if c[0] == "gh-test"]
    assert len(gh) == 1
    assert gh[0][:9] == ["gh-test", "-R", "davinciucberkeley-collab/dbf-hangar", "pr", "create",
                         "--head", branch, "--base", "main"]
    assert gh[0][gh[0].index("--title") + 1] == "Lighter battery" and "--draft" not in gh[0]
    commit = [c for c in calls if "commit" in c][0]
    assert commit[-1].startswith("design(example-tailsitter-wing): Lighter battery")
    assert "Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>" in commit[-1]
    assert calls[-3:] == [["git", "-C", str(tmp_path), "switch", "main"], ["git", "-C", str(tmp_path), "checkout", branch, "--", str(tmp_example.resolve())], ["git", "-C", str(tmp_path), "reset", "-q", "--", str(tmp_example.resolve())]]


def test_propose_resolves_a_relative_design_path(tmp_example, tmp_path, monkeypatch):
    seen: list[tuple[list[str], str]] = []

    def fake_run(argv, cwd):
        seen.append((list(argv), cwd))
        if "--show-toplevel" in argv:
            return str(tmp_path) + "\n"
        if "status" in argv:
            return " M plane.yaml\n"
        if "--abbrev-ref" in argv:
            return "main\n"
        if "create" in argv:
            return "https://github.com/o/r/pull/8\n"
        return ""

    monkeypatch.setattr(edit, "_run", fake_run)
    monkeypatch.setenv("HANGAR_GH", "gh-test")
    monkeypatch.chdir(tmp_path)
    r = call("design.propose", path="example-tailsitter-wing", title="Relative path")
    assert r.ok, r.messages
    assert seen[0][0] == ["git", "-C", str(tmp_example.resolve()), "rev-parse", "--show-toplevel"]
    assert all(Path(cwd).is_absolute() for _, cwd in seen)


def test_propose_refuses_when_nothing_changed(tmp_example, tmp_path, monkeypatch):
    def fake_run(argv, cwd):
        return str(tmp_path) + "\n" if "--show-toplevel" in argv else ""

    monkeypatch.setattr(edit, "_run", fake_run)
    r = call("design.propose", path=str(tmp_example), title="x")
    assert r.ok is False and r.exit_code == 2


# ---- design.set --kind add (U3.6-2) ----
import difflib

from hangar import pdledit
from hangar.ops import OpInputError


def _bytes(d):
    return (d / "plane.yaml").read_bytes(), (d / "CHANGELOG.yaml").read_bytes() if (d / "CHANGELOG.yaml").exists() else None


def test_add_creates_missing_scalar_and_keeps_comments(tmp_concept_a):
    plane = tmp_concept_a / "plane.yaml"
    old_text = plane.read_text(encoding="utf-8")
    r = call("design.set", path=str(tmp_concept_a), key="flight.hover_pose", value="up", why="d21", kind="add")
    assert r.ok, r.messages
    new_text = plane.read_text(encoding="utf-8")
    assert yaml.safe_load(new_text)["flight"]["hover_pose"] == "up"
    for line in old_text.splitlines():
        if line.strip().startswith("#"):
            assert line in new_text.splitlines()
    log = yaml.safe_load((tmp_concept_a / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert log[-1]["kind"] == "add" and log[-1]["old"] is None and log[-1]["new"] == "up"


def test_add_creates_list_element_and_mapping(tmp_concept_a):
    text = (tmp_concept_a / "plane.yaml").read_text(encoding="utf-8")
    t1 = pdledit.add_value(text, "wiring.harnesses[hrn-bat].from", "pwr-001")
    assert yaml.safe_load(t1)["wiring"]["harnesses"] == [{"id": "hrn-bat", "from": "pwr-001"}]
    t2 = pdledit.add_value(t1, "wiring.harnesses[hrn-bat].to", "prp-003")
    assert yaml.safe_load(t2)["wiring"]["harnesses"] == [{"id": "hrn-bat", "from": "pwr-001", "to": "prp-003"}]


_HARNESS = "wiring.harnesses[hrn-bat]"


def test_add_op_builds_harness_in_one_call(tmp_concept_a):
    before = _bytes(tmp_concept_a)
    r = call("design.set", path=str(tmp_concept_a), key=f"{_HARNESS}.from", value="pwr-001", why="d21", kind="add")
    assert r.ok is False and "required" in " ".join(r.messages)
    assert _bytes(tmp_concept_a) == before
    r = call("design.set", path=str(tmp_concept_a), key=f"{_HARNESS}.from", value="pwr-001", why="d21", kind="add",
             also=[f"{_HARNESS}.to=prp-003", f"{_HARNESS}.gauge_awg=14"])
    assert r.ok, r.messages
    v = call("design.validate", path=str(tmp_concept_a), tier="0")
    assert not [m for m in v.messages if m.startswith("T0.schema")], v.messages
    log = yaml.safe_load((tmp_concept_a / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert len(log) == 3


def test_add_two_pairs_bad_type_writes_nothing(tmp_concept_a):
    before = _bytes(tmp_concept_a)
    r = call("design.set", path=str(tmp_concept_a), key=f"{_HARNESS}.from", value="pwr-001", why="d21", kind="add",
             also=[f"{_HARNESS}.to=prp-003", f"{_HARNESS}.gauge_awg=x"])
    assert r.ok is False
    assert _bytes(tmp_concept_a) == before


def test_modify_on_missing_key_still_fails(tmp_concept_a):
    before = _bytes(tmp_concept_a)
    r = call("design.set", path=str(tmp_concept_a), key="flight.hover_pose", value="up", why="x", kind="modify")
    assert r.ok is False and r.exit_code == 2
    assert _bytes(tmp_concept_a) == before


def test_add_preserves_crlf(tmp_example):
    p = tmp_example / "plane.yaml"
    p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    r = call("design.set", path=str(tmp_example), key="flight.hover_pose", value="up", why="x", kind="add")
    assert r.ok, r.messages
    raw = p.read_bytes()
    assert raw.count(b"\n") == raw.count(b"\r\n") > 0


def test_add_value_refuses_existing_key(tmp_example):
    text = (tmp_example / "plane.yaml").read_text(encoding="utf-8")
    with pytest.raises(OpInputError, match="already set"):
        pdledit.add_value(text, "flight.cl_max", 1.0)


def test_add_provenance_pair_is_inserts_only(tmp_concept_a):
    plane = tmp_concept_a / "plane.yaml"
    old = plane.read_text(encoding="utf-8").splitlines()
    r = call("design.set", path=str(tmp_concept_a), key="components[pwr-001].provenance.mass_source", value="datasheet",
             why="d21", kind="add", also=["components[pwr-001].provenance.geometry_source=vendor drawing"])
    assert r.ok, r.messages
    new = plane.read_text(encoding="utf-8").splitlines()
    tags = {t for t, *_ in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes()}
    assert tags <= {"equal", "insert"} and "insert" in tags


def test_add_connection_changes_one_line(tmp_concept_a):
    plane = tmp_concept_a / "plane.yaml"
    old = plane.read_text(encoding="utf-8").splitlines()
    r = call("design.set", path=str(tmp_concept_a), key="attachments[E-WNG-01].connection", value="CT-M3-SHCS-INSERT",
             why="d21", kind="add")
    assert r.ok, r.messages
    new = plane.read_text(encoding="utf-8").splitlines()
    ops = [o for o in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes() if o[0] != "equal"]
    assert len(ops) == 1 and ops[0][0] == "replace" and ops[0][2] - ops[0][1] == 1 and ops[0][4] - ops[0][3] == 1
    assert "E-WNG-01" in old[ops[0][1]] and "{" in old[ops[0][1]]


def test_add_out_of_range_index_names_the_range_and_writes_nothing(tmp_concept_a):
    before = _bytes(tmp_concept_a)
    r = call("design.set", path=str(tmp_concept_a), key="components[pwr-001].position[5]", value="1", why="x", kind="add")
    assert r.ok is False and r.exit_code == 2
    msg = " ".join(r.messages)
    assert "out of range" in msg and "5" in msg and "already set" not in msg
    assert _bytes(tmp_concept_a) == before


# ---- design.set --kind add with list and mapping values (U3.6c) ----
def _opcodes(old, new):
    return [o for o in difflib.SequenceMatcher(None, old.splitlines(), new.splitlines(), autojunk=False).get_opcodes()
            if o[0] != "equal"]


def _plane_text(d):
    return (d / "plane.yaml").read_bytes().decode("utf-8")


ARTIC = {"type": "revolute", "pivot": [140.563, 195.69, 6.7], "axis": [0, 0, -1], "range_deg": [-36, 36]}
ARTIC_TEXT = "{type: revolute, pivot: [140.563, 195.69, 6.7], axis: [0, 0, -1], range_deg: [-36, 36]}"


def _one_inserted_line(old, new):
    ops = _opcodes(old, new)
    assert len(ops) == 1 and ops[0][0] == "insert" and ops[0][4] - ops[0][3] == 1
    return new.splitlines()[ops[0][3]]


def test_add_list_value_is_one_inserted_line(tmp_example):
    text = _plane_text(tmp_example)
    out = pdledit.add_value(text, "flight.test_list", ["E-MEC-03", "E-MEC-05", 2])
    assert _one_inserted_line(text, out).strip() == "test_list: [E-MEC-03, E-MEC-05, 2]"
    assert yaml.safe_load(out)["flight"]["test_list"] == ["E-MEC-03", "E-MEC-05", 2]


def test_add_mapping_value_is_one_inserted_line(tmp_example):
    text = _plane_text(tmp_example)
    val = {"a": 1, "b": [1, 2], "c": {"d": "x y"}}
    out = pdledit.add_value(text, "flight.test_map", val)
    assert _one_inserted_line(text, out).strip() == 'test_map: {a: 1, b: [1, 2], c: {d: "x y"}}'
    assert yaml.safe_load(out)["flight"]["test_map"] == val


@pytest.mark.parametrize("a", ["E-MEC-02", "E-MEC-03", "E-MEC-05"])
def test_add_into_one_line_flow_attachment(tmp_concept_a, a):
    text = _plane_text(tmp_concept_a)
    out = pdledit.add_value(text, f"attachments[{a}].articulation", ARTIC)
    ops = _opcodes(text, out)
    assert len(ops) == 1 and ops[0][0] == "replace" and ops[0][2] - ops[0][1] == 1 and ops[0][4] - ops[0][3] == 1
    old_line, new_line = text.splitlines()[ops[0][1]], out.splitlines()[ops[0][3]]
    assert f"id: {a}" in old_line
    assert new_line == old_line[:-1] + f", articulation: {ARTIC_TEXT}" + "}"


def test_add_nested_chain_in_flow_attachment_is_one_flow_value(tmp_concept_a):
    text = _plane_text(tmp_concept_a)
    out = pdledit.add_value(text, "attachments[E-MEC-02].extra.k", 1)
    ops = _opcodes(text, out)
    assert len(ops) == 1 and ops[0][0] == "replace" and ops[0][2] - ops[0][1] == 1 and ops[0][4] - ops[0][3] == 1
    assert out.splitlines()[ops[0][3]].endswith(", extra: {k: 1}}")
    att = next(x for x in yaml.safe_load(out)["attachments"] if x["id"] == "E-MEC-02")
    assert att["extra"] == {"k": 1}


def test_add_collection_op_logs_and_checks_schema_once(tmp_concept_a, tmp_path):
    fresh = tmp_path / "fresh"
    shutil.copytree(tmp_concept_a, fresh)
    r = call("design.set", path=str(tmp_concept_a), kind="add", why="t", key="attachments[E-MEC-02].articulation",
             value="{type: revolute, pivot: [1, 2, 3], axis: [0, 0, 1], range_deg: [0, 1]}")
    assert r.ok, r.messages
    log = yaml.safe_load((tmp_concept_a / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert log[-1]["old"] is None and log[-1]["kind"] == "add"
    assert log[-1]["new"] == {"type": "revolute", "pivot": [1, 2, 3], "axis": [0, 0, 1], "range_deg": [0, 1]}
    before = _bytes(fresh)
    r = call("design.set", path=str(fresh), kind="add", why="t", key="attachments[E-MEC-02].articulation",
             value="{type: revolute, pivot: [1, 2], axis: [0, 0, 1], range_deg: [0, 1]}")
    assert r.ok is False and "pivot" in " ".join(r.messages)
    assert _bytes(fresh) == before


def test_add_collection_preserves_crlf(tmp_concept_a, tmp_example):
    lf = _plane_text(tmp_concept_a)
    crlf = lf.replace("\n", "\r\n")
    key = "attachments[E-MEC-02].articulation"
    out = pdledit.add_value(crlf, key, ARTIC)
    assert "\n" not in out.replace("\r\n", "")
    assert out.replace("\r\n", "\n") == pdledit.add_value(lf, key, ARTIC)
    lf2 = _plane_text(tmp_example)
    out2 = pdledit.add_value(lf2.replace("\n", "\r\n"), "flight.test_list", ["E-MEC-03", "E-MEC-05", 2])
    assert "\n" not in out2.replace("\r\n", "")
    assert out2.replace("\r\n", "\n") == pdledit.add_value(lf2, "flight.test_list", ["E-MEC-03", "E-MEC-05", 2])


def test_collection_refusals_stay_refusals(tmp_concept_a):
    text = _plane_text(tmp_concept_a)

    def refuses(match, fn, *a):
        with pytest.raises(OpInputError, match=match):
            fn(*a)

    refuses("cannot add a list element by index", pdledit.add_value, text, "mechanisms[elevon-r].driven[0]", "x")
    refuses("without rewriting other text", pdledit.add_value, text, "attachments[E-WNG-10].extra", {"a": 1})
    refuses("without rewriting other text", pdledit.add_value, text, "attachments[E-MEC-02].x[foo].y", 1)
    refuses("already set", pdledit.add_value, text, "attachments[E-MEC-02].location", [1, 2, 3])
    refuses("give one scalar", pdledit.parse_value, "a: b")
    refuses("give one scalar", pdledit.parse_value, "- x")
    refuses("empty list or mapping", pdledit.parse_value, "[]")
    refuses("empty list or mapping", pdledit.parse_value, "{a: []}")
    refuses("cannot read value", pdledit.parse_value, "[1, 2")
    refuses("unsupported mapping key", pdledit.render_flow, {"a b": 1})

    before = _bytes(tmp_concept_a)

    def op_fails(match, **kw):
        r = call("design.set", path=str(tmp_concept_a), why="t", **kw)
        assert r.ok is False and match in " ".join(r.messages)
        assert _bytes(tmp_concept_a) == before

    op_fails("is not of type 'array'", kind="add", key="mechanisms[elevon-r].driven", value="E-MEC-03")
    op_fails("already set", kind="add", key="attachments[E-MEC-02].location", value="[1, 2, 3]")
    for kind in ("modify", "subtract"):
        op_fails("give one scalar", kind=kind, key="components[wng-004-l].mass_g", value="[1, 2]")


def test_parse_value_scalars_unchanged():
    assert pdledit.parse_value("41.5") == 41.5
    assert pdledit.parse_value("up") == "up"
    assert pdledit.parse_value("[a, b]") == ["a", "b"]
    assert pdledit.parse_value("{k: v}") == {"k": "v"}
    assert pdledit.parse_value("[-36, 36]") == [-36, 36]


@pytest.mark.slow
def test_concept_a_right_elevon_mechanism_in_one_call(tmp_concept_a):
    import hangar.design
    import hangar.gates
    original = _plane_text(tmp_concept_a)
    r = call("design.migrate", path=str(tmp_concept_a), write=True)
    assert r.ok, r.messages
    base = _plane_text(tmp_concept_a)
    assert 'schema_version: "1.3"' in base
    ops = _opcodes(original, base)
    assert len(ops) == 1 and ops[0][2] - ops[0][1] == 1 and ops[0][4] - ops[0][3] == 1
    log_file = tmp_concept_a / "CHANGELOG.yaml"
    n_log = len(yaml.safe_load(log_file.read_text(encoding="utf-8")) or []) if log_file.exists() else 0
    r = call("design.set", path=str(tmp_concept_a), kind="add", why="declare right elevon mechanism",
             key="attachments[E-MEC-02].articulation", value=ARTIC_TEXT, also=[
                 "attachments[E-MEC-03].articulation={type: revolute, pivot: [141.723, 187.987, 8.701], axis: [0, 0, -1], range_deg: [-36, 36]}",
                 "attachments[E-MEC-05].articulation={type: revolute, pivot: [183.75, 195, 0.295], axis: [0, -1, 0], range_deg: [-21, 21]}",
                 "mechanisms[elevon-r].driver=E-MEC-02",
                 "mechanisms[elevon-r].driven=[E-MEC-03, E-MEC-05, E-WNG-10]",
                 "mechanisms[elevon-r].input_range_deg=[-36, 36]",
                 "mechanisms[elevon-r].expect=[{attachment: E-WNG-10, ratio: 0.57}]"])
    assert r.ok, r.messages
    log = yaml.safe_load((tmp_concept_a / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert len(log) - n_log == 7
    new_text = _plane_text(tmp_concept_a)
    ops = _opcodes(base, new_text)
    replaces = [o for o in ops if o[0] == "replace"]
    assert all(o[0] in ("insert", "replace") for o in ops) and len(replaces) == 3
    assert all(o[2] - o[1] == 1 and o[4] - o[3] == 1 for o in replaces)
    design = hangar.design.load_design(tmp_concept_a)
    card = hangar.gates.run_gates(design, only_tiers={6})
    t0 = next(t for t in card.tiers if t.tier == 0)
    assert all(x.status == "PASS" for x in t0.results), [(x.check_id, x.status) for x in t0.results]
    t6 = next(t for t in card.tiers if t.tier == 6)
    rows = {x.check_id: x for x in t6.results}
    row = rows["T6.mechanism.elevon-r"]
    assert "E-WNG-10" in row.data["joint"]
    assert row.data.get("raw_status", row.status) != "SKIP" and row.status != "SKIP"
    assert "T6.undriven.E-WNG-10" not in rows


def test_collection_pairs_are_atomic(tmp_concept_a):
    before = _bytes(tmp_concept_a)
    r = call("design.set", path=str(tmp_concept_a), kind="add", why="t", key="mechanisms[elevon-r].driver",
             value="E-MEC-02", also=["mechanisms[elevon-r].driven=[E-MEC-03]",
                                     "attachments[E-MEC-02].articulation={type: bogus}"])
    assert r.ok is False
    assert _bytes(tmp_concept_a) == before


# ---- design.set --kind remove (U3.6d) ----
def _lines(text):
    return text.replace("\r\n", "\n").splitlines()


def _line_no(lines, needle):
    return next(n for n, line in enumerate(lines) if needle in line)


def _log(d):
    return yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))


def test_remove_flow_attachment_deletes_its_line_and_id_comments(tmp_concept_a):
    text = _plane_text(tmp_concept_a)
    out, gone = pdledit.remove_element(text, "attachments[E-MEC-HW-R1]")
    old = _lines(text)
    i = _line_no(old, "- {id: E-MEC-HW-R1,")
    assert old[i - 2].strip().startswith("# E-MEC-HW-R1 CT-HW-SEATED")
    assert old[i - 1].strip().startswith("# rating [derived]")
    assert _lines(out) == old[:i - 2] + old[i + 1:]
    assert {o[0] for o in _opcodes(text, out)} == {"delete"}
    assert "E-MEC-HW-R1" not in out
    assert "# E-MEC-HW-R2 CT-HW-SEATED" in out
    assert gone["id"] == "E-MEC-HW-R1" and gone["parent"] == "mec-001-r"
    ids = [a["id"] for a in yaml.safe_load(text)["attachments"]]
    assert [a["id"] for a in yaml.safe_load(out)["attachments"]] == [x for x in ids if x != "E-MEC-HW-R1"]


def test_remove_block_element_deletes_exactly_its_lines(tmp_example):
    text = _plane_text(tmp_example)
    old = _lines(text)
    out, gone = pdledit.remove_element(text, "components[fin_l]")
    i = _line_no(old, "  - id: fin_l")
    assert old[i + 9] == "  - id: fin_r"
    assert _lines(out) == old[:i] + old[i + 9:]
    assert gone["id"] == "fin_l" and gone["mass_g"] == 15
    last, _ = pdledit.remove_element(text, "components[battery]")     # last element: the blank line after it stays
    j = _line_no(old, "  - id: battery")
    assert old[j + 6] == "" and _lines(last) == old[:j] + old[j + 6:]


def test_remove_keeps_a_comment_that_only_mentions_the_id(tmp_example):
    text = _plane_text(tmp_example)
    old = _lines(text)
    i = _line_no(old, "- {id: wing-body,")
    assert "wing-body" in old[i - 2] and not old[i - 2].lstrip().startswith("# wing-body")
    out, _ = pdledit.remove_element(text, "attachments[wing-body]")
    assert _lines(out) == old[:i] + old[i + 1:]
    assert "# Ratings revised 2026-11-11" in out


def test_remove_preserves_crlf(tmp_example, tmp_concept_a):
    for d, key in ((tmp_example, "components[fin_l]"), (tmp_concept_a, "attachments[E-MEC-HW-R1]")):
        lf = _plane_text(d).replace("\r\n", "\n")
        crlf = lf.replace("\n", "\r\n")
        out, _ = pdledit.remove_element(crlf, key)
        assert "\n" not in out.replace("\r\n", "")
        assert out.replace("\r\n", "\n") == pdledit.remove_element(lf, key)[0]
    p = tmp_example / "plane.yaml"
    raw = _plane_text(tmp_example).replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    p.write_bytes(raw)
    r = call("design.set", path=str(tmp_example), kind="remove", why="t", key="components[fin_l]")
    assert r.ok, r.messages
    assert p.read_bytes() == pdledit.remove_element(raw.decode("utf-8"), "components[fin_l]")[0].encode("utf-8")
    assert b"\n" not in p.read_bytes().replace(b"\r\n", b"")


def test_remove_op_two_ids_logs_flow_strings_and_still_validates(tmp_concept_a):
    import hangar.gates
    before = _plane_text(tmp_concept_a)
    log_file = tmp_concept_a / "CHANGELOG.yaml"
    n_log = len(_log(tmp_concept_a) or []) if log_file.exists() else 0
    r = call("design.set", path=str(tmp_concept_a), kind="remove", why="close the loop (U3.4 run 5)",
             key="attachments[E-MEC-HW-R1]", also=["attachments[E-MEC-HW-L1]="])
    assert r.ok, r.messages
    after = _plane_text(tmp_concept_a)
    ids = [a["id"] for a in yaml.safe_load(after)["attachments"]]
    assert "E-MEC-HW-R1" not in ids and "E-MEC-HW-L1" not in ids and "E-MEC-HW-R2" in ids
    assert {o[0] for o in _opcodes(before, after)} == {"delete"}
    assert len(_lines(before)) - len(_lines(after)) == 6
    log = _log(tmp_concept_a)
    assert len(log) - n_log == 2
    one, two = log[-2], log[-1]
    assert one["key"] == "attachments[E-MEC-HW-R1]" and two["key"] == "attachments[E-MEC-HW-L1]"
    assert one["old"] == ("{id: E-MEC-HW-R1, parent: mec-001-r, child: hwc-002-r, method: bolted, "
                          "location: [140.405, 199.012, 4.423], rated_load_n: 931.5, rating_basis: derived}")
    assert two["old"].startswith("{id: E-MEC-HW-L1, parent: mec-001-l,")
    assert one["new"] is None and two["new"] is None
    assert one["kind"] == "remove" and one["why"] == "close the loop (U3.4 run 5)"
    card = hangar.gates.run_gates(design_mod.load_design(tmp_concept_a), only_tiers={0})
    t0 = next(t for t in card.tiers if t.tier == 0)
    assert {x.check_id: x.status for x in t0.results}["T0.schema"] != "FAIL"


def _refused(text, key, needle):
    with pytest.raises(OpInputError) as e:
        pdledit.remove_element(text, key)
    assert needle in str(e.value), str(e.value)


def test_remove_refusals(tmp_concept_a):
    text = _plane_text(tmp_concept_a)
    _refused(text, "attachments[E-NOPE]", "no element with id")
    _refused(text, "attachments[0]", "remove by index is not supported")
    _refused(text, "attachments[E-MEC-HW-R1].location", "like name[id]")
    _refused(text, "attachments[E-MEC-HW-R1].location[0]", "remove by index is not supported")
    _refused(text, "mechanisms[elevon-r].driven[E-MEC-03]", "no key 'mechanisms'")
    _refused(text, "attachments", "like name[id]")
    _refused(text, "attachments[E-MEC-HW-R1][x]", "named by a key")
    _refused(text, "flight.cl_max", "like name[id]")
    _refused(text, "flight[x]", "needs a list")
    _refused(text, "attachments[E-WNG-10]", "without rewriting other text")      # multi-line flow entry
    # removing a list's only element leaves `attachments: []` now (U13.2-3; tests/test_design_remove_last.py)
    assert pdledit.remove_element("attachments:\n  - {id: a, parent: x, child: y}\n", "attachments[a]")[0] == "attachments: []\n"


def test_remove_op_input_errors_write_nothing(tmp_concept_a):
    before = _bytes(tmp_concept_a)
    for kw, needle in (
            (dict(key="attachments[E-NOPE]"), "no element with id"),
            (dict(key="attachments[E-MEC-HW-R1]", value="1"), "takes no --value"),
            (dict(key="attachments[E-MEC-HW-R1]", also=["attachments[E-MEC-HW-L1]=1"]), "takes no value"),
            (dict(key="attachments[E-MEC-HW-R1]", also=["attachments[E-MEC-HW-L1]"]), "--also needs KEY=VALUE"),
            (dict(key="attachments[E-MEC-HW-R1]", also=["attachments[E-NOPE]="]), "no element with id"),
            (dict(key="attachments[E-MEC-HW-R1]", also=["attachments[E-MEC-HW-L1].location="]), "like name[id]")):
        r = call("design.set", path=str(tmp_concept_a), kind="remove", why="t", **kw)
        assert r.ok is False and needle in " ".join(r.messages), (kw, r.messages)
        assert _bytes(tmp_concept_a) == before
    r = call("design.set", path=str(tmp_concept_a), kind="modify", why="t", key="flight.cl_max")
    assert r.ok is False and "value is required" in " ".join(r.messages)
    assert _bytes(tmp_concept_a) == before


def test_set_value_with_colon_space_is_a_string(tmp_example):  # T58
    r = call("design.set", path=str(tmp_example), key="components[prop_l].description", value="Disc: 10x4.5 prop", why="label")
    assert r.ok, r.messages
    data = yaml.safe_load((tmp_example / "plane.yaml").read_text(encoding="utf-8"))
    assert [c for c in data["components"] if c["id"] == "prop_l"][0]["description"] == "Disc: 10x4.5 prop"


def test_parse_set_value_keeps_other_scalars_and_the_add_path(tmp_example):  # T58
    from hangar.ops.edit import OpInputError
    assert pdledit.parse_set_value("Pack: 3S") == "Pack: 3S"
    assert pdledit.parse_set_value("x:") == "x:"
    assert pdledit.parse_set_value('"a: b"') == "a: b"
    assert pdledit.parse_set_value("41.5") == 41.5
    assert pdledit.parse_set_value("true") is True
    with pytest.raises(OpInputError, match="mapping or list"):
        pdledit.parse_set_value("[1, 2]")
    with pytest.raises(OpInputError, match="give one scalar"):
        pdledit.parse_value("a: b")       # the add path is unchanged
    r = call("design.set", path=str(tmp_example), key="components[battery].mass_g", value="heavy: 250", why="x")
    assert r.exit_code == 2 and "number" in " ".join(r.messages)


def test_sweep_value_with_colon_space_is_a_string(tmp_example, tmp_path, monkeypatch):  # T85
    monkeypatch.setattr(edit, "SWEEP_ROOT", tmp_path / "sweeps")
    r = call("design.sweep", path=str(tmp_example), key="components[prop_l].description", values=["Disc: 10x4.5 prop"])
    assert r.ok, r.messages
    assert r.data["rows"][0]["value"] == "Disc: 10x4.5 prop"
    data = yaml.safe_load((Path(r.data["sweep_dir"]) / "1" / "plane.yaml").read_text(encoding="utf-8"))
    assert [c for c in data["components"] if c["id"] == "prop_l"][0]["description"] == "Disc: 10x4.5 prop"


# ---- design.set --append / --remove on one-line [list] values (T55, D55) ----
AUTHORS_ONE = "authors: [platform bootstrap]"
AUTHORS_CA = '"UC Berkeley DBF capstone team (source repo dbf-combined)"'
AUTHOR_BT = "imported for aircraft-platform by `plane import dbf`"


def _list_op(d, key, **kw):
    return call("design.set", path=str(d), key=key, why="t", **kw)


def _changed_lines(before: str, after: str) -> tuple[str, str]:
    ops = [o for o in difflib.SequenceMatcher(None, before.splitlines(), after.splitlines(), autojunk=False).get_opcodes() if o[0] != "equal"]
    assert len(ops) == 1 and ops[0][0] == "replace" and ops[0][2] - ops[0][1] == 1 and ops[0][4] - ops[0][3] == 1, ops
    return before.splitlines()[ops[0][1]], after.splitlines()[ops[0][3]]


def test_append_adds_one_entry_to_a_one_line_list_and_logs(tmp_example):
    p = tmp_example / "plane.yaml"
    before = p.read_bytes()
    r = _list_op(tmp_example, "authors", append="second author")
    assert r.ok, r.messages
    assert p.read_bytes() == before.replace(AUTHORS_ONE.encode(), b'authors: [platform bootstrap, "second author"]')
    log = yaml.safe_load((tmp_example / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert log[-1]["key"] == "authors" and log[-1]["kind"] == "modify" and log[-1]["why"] == "t"
    assert log[-1]["old"] == ["platform bootstrap"] and log[-1]["new"] == ["platform bootstrap", "second author"]
    assert r.data["changed"] is True and r.data["new"] == ["platform bootstrap", "second author"]


def test_append_to_an_empty_list_and_remove_back_to_empty(tmp_example):
    p = tmp_example / "plane.yaml"
    before = p.read_bytes()
    assert b"  derived_from: []" in before
    assert _list_op(tmp_example, "lineage.derived_from", append="abc-1").ok
    assert p.read_bytes() == before.replace(b"  derived_from: []", b"  derived_from: [abc-1]")
    assert _list_op(tmp_example, "lineage.derived_from", remove="abc-1").ok
    assert p.read_bytes() == before


def test_remove_deletes_the_entry_matched_by_value_and_changes_one_line(tmp_concept_a):
    p = tmp_concept_a / "plane.yaml"
    before = p.read_text(encoding="utf-8")
    r = _list_op(tmp_concept_a, "authors", remove=AUTHOR_BT)
    assert r.ok, r.messages
    old_line, new_line = _changed_lines(before, p.read_text(encoding="utf-8"))
    assert old_line.startswith("authors: [") and new_line == f"authors: [{AUTHORS_CA}]"
    log = yaml.safe_load((tmp_concept_a / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert log[-1]["old"][1] == AUTHOR_BT and log[-1]["new"] == [log[-1]["old"][0]] and log[-1]["kind"] == "modify"


def test_remove_takes_the_first_match_only(tmp_example):
    p = tmp_example / "plane.yaml"
    p.write_bytes(p.read_bytes().replace(AUTHORS_ONE.encode(), b"authors: [x, y, x]"))
    assert _list_op(tmp_example, "authors", remove="x").ok
    assert yaml.safe_load(p.read_text(encoding="utf-8"))["authors"] == ["y", "x"]
    assert "authors: [y, x]" in p.read_text(encoding="utf-8")


def test_remove_matches_value_and_type(tmp_example):
    p = tmp_example / "plane.yaml"
    p.write_bytes(p.read_bytes().replace(AUTHORS_ONE.encode(), b'authors: ["1", y]'))
    before = _bytes(tmp_example)
    r = _list_op(tmp_example, "authors", remove="1")          # 1 is the number; the list holds the text "1"
    assert r.ok is False and r.exit_code == 2 and "is not in the list" in " ".join(r.messages)
    assert _bytes(tmp_example) == before
    assert _list_op(tmp_example, "authors", remove='"1"').ok  # a quoted value is the text
    assert yaml.safe_load(p.read_text(encoding="utf-8"))["authors"] == ["y"]


def test_list_flag_refusals_exit_2_and_write_nothing(tmp_concept_a):
    before = _bytes(tmp_concept_a)
    for key, kw, needle in (
            ("authors", dict(remove="nobody"), "is not in the list"),
            ("status", dict(append="x"), "is not a list"),
            ("components", dict(append="x"), "one-line"),
            ("components[hwc-002-l]", dict(append="x"), "name the list by its key"),
            ("nope", dict(append="x"), "no key"),
            ("authors", dict(append="a", remove="b"), "not both"),
            ("authors", dict(append="a", value="b"), "takes no --value"),
            ("authors", dict(append="a", kind="add"), "takes no --value, --also or --kind"),
            ("authors", dict(remove="a", also=["status=x"]), "takes no --value, --also or --kind"),
            ("authors", dict(append="  "), "non-empty"),
            ("authors", dict(append="{a: 1}"), "mapping or list"),
            ("authors", dict(append="5"), "authors")):          # a number in a list of strings: the schema check names the key
        r = _list_op(tmp_concept_a, key, **kw)
        assert r.ok is False and r.exit_code == 2 and needle in " ".join(r.messages), (key, kw, r.messages)
        assert _bytes(tmp_concept_a) == before


def test_list_flags_preserve_crlf(tmp_example):
    p = tmp_example / "plane.yaml"
    raw = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    p.write_bytes(raw)
    assert _list_op(tmp_example, "authors", append="second author").ok
    assert p.read_bytes() == raw.replace(AUTHORS_ONE.encode(), b'authors: [platform bootstrap, "second author"]')
    assert _list_op(tmp_example, "authors", remove="second author").ok
    assert p.read_bytes() == raw
    log = (tmp_example / "CHANGELOG.yaml").read_bytes()
    assert log.count(b"\n") == log.count(b"\r\n") > 0


def test_append_item_and_remove_item_return_text_old_and_new(tmp_example):
    text = (tmp_example / "plane.yaml").read_bytes().decode("utf-8")
    out, old, new = pdledit.append_item(text, "authors", "b")
    assert old == ["platform bootstrap"] and new == ["platform bootstrap", "b"]
    out2, old2, new2 = pdledit.remove_item(out, "authors", "platform bootstrap")
    assert old2 == new and new2 == ["b"] and "authors: [b]" in out2
    with pytest.raises(OpInputError, match="is not in the list"):
        pdledit.remove_item(text, "authors", "zzz")


def test_list_flags_through_the_cli(tmp_example):
    from click.testing import CliRunner
    from hangar.cli import cli
    base = ["design", "set", str(tmp_example), "authors", "--why", "t", "--json"]
    res = CliRunner().invoke(cli, base + ["--append", "second author"])
    assert res.exit_code == 0, res.output
    assert yaml.safe_load((tmp_example / "plane.yaml").read_text(encoding="utf-8"))["authors"] == ["platform bootstrap", "second author"]
    res = CliRunner().invoke(cli, base + ["--remove", "second author"])
    assert res.exit_code == 0, res.output
    assert yaml.safe_load((tmp_example / "plane.yaml").read_text(encoding="utf-8"))["authors"] == ["platform bootstrap"]
    res = CliRunner().invoke(cli, base + ["--remove", "nobody"])
    assert res.exit_code == 2 and "is not in the list" in json.loads(res.output)["messages"][0]


def test_remove_leaves_the_other_entries_exactly_as_written(tmp_example):
    p = tmp_example / "plane.yaml"
    raw = p.read_bytes()
    for body, rm, want in (("['single q',   \"dbl\", plain one]", "dbl", "['single q',   plain one]"),
                           ("[a,  b, c]", "a", "[b, c]"),
                           ("[a,  b, c]", "c", "[a,  b]"),
                           ("[ only ]", "only", "[]")):
        p.write_bytes(raw.replace(AUTHORS_ONE.encode(), f"authors: {body}".encode()))
        assert _list_op(tmp_example, "authors", remove=rm).ok
        assert p.read_bytes() == raw.replace(AUTHORS_ONE.encode(), f"authors: {want}".encode()), (body, rm)


# ---- U6.1 (T93): --append keeps the spaces before ']'; --remove refuses a mapping or list like --append ----
def test_append_keeps_the_spaces_before_the_closing_bracket(tmp_example):
    p = tmp_example / "plane.yaml"
    raw = p.read_bytes()
    for body, add, want in (("[ only ]", "y", "[ only, y ]"),
                            ("[a,  b ]", "c", "[a,  b, c ]"),
                            ("[a, b,  ]", "c", "[a, b, c  ]"),
                            ("[a, b]", "c", "[a, b, c]")):
        p.write_bytes(raw.replace(AUTHORS_ONE.encode(), f"authors: {body}".encode()))
        assert _list_op(tmp_example, "authors", append=add).ok
        assert p.read_bytes() == raw.replace(AUTHORS_ONE.encode(), f"authors: {want}".encode()), (body, add)


def test_remove_refuses_a_mapping_or_list_like_append(tmp_concept_a):
    before = _bytes(tmp_concept_a)
    for raw in ("{a: 1}", "[a]"):
        r = _list_op(tmp_concept_a, "authors", remove=raw)
        assert r.ok is False and r.exit_code == 2 and "mapping or list" in " ".join(r.messages), (raw, r.messages)
    assert _bytes(tmp_concept_a) == before


def test_two_sweeps_of_one_design_do_not_share_a_folder(tmp_example, tmp_path, monkeypatch):
    monkeypatch.setattr(edit, "SWEEP_ROOT", tmp_path / ".sweeps")
    a = call("design.sweep", path=str(tmp_example), key="components[battery].position[0]", values=["100"])
    b = call("design.sweep", path=str(tmp_example), key="components[battery].position[0]", values=["140"])
    assert a.ok and b.ok
    assert a.data["sweep_dir"] != b.data["sweep_dir"]
    assert (Path(a.data["sweep_dir"]) / "1" / "plane.yaml").is_file()      # the first run is still there
    assert (Path(b.data["sweep_dir"]) / "1" / "plane.yaml").is_file()


def test_sweep_prunes_only_runs_older_than_a_day(tmp_example, tmp_path, monkeypatch):
    import os
    import time
    monkeypatch.setattr(edit, "SWEEP_ROOT", tmp_path / ".sweeps")
    base = tmp_path / ".sweeps" / "example-tailsitter-wing"
    old, young = base / "old-run", base / "young-run"
    for d in (old, young):
        d.mkdir(parents=True)
    t = time.time() - 3 * 86400
    os.utime(old, (t, t))
    r = call("design.sweep", path=str(tmp_example), key="components[battery].position[0]", values=["100"])
    assert r.ok and not old.exists() and young.exists()


def test_two_sweeps_in_the_same_second_and_process_get_distinct_folders(tmp_example, tmp_path, monkeypatch):
    from datetime import datetime, timezone

    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(edit, "SWEEP_ROOT", tmp_path / ".sweeps")
    monkeypatch.setattr(edit, "datetime", Frozen)
    a = call("design.sweep", path=str(tmp_example), key="components[battery].position[0]", values=["100"])
    b = call("design.sweep", path=str(tmp_example), key="components[battery].position[0]", values=["140"])
    assert a.ok and b.ok, (a.messages, b.messages)
    assert a.data["sweep_dir"] != b.data["sweep_dir"]
    assert (Path(a.data["sweep_dir"]) / "1" / "plane.yaml").is_file()
    assert (Path(b.data["sweep_dir"]) / "1" / "plane.yaml").is_file()


def test_branch_slug_cuts_at_a_word_boundary():
    cases = {
        "New test design from concept-a-param span change": "new-test-design-from-concept-a-param",
        "Lighter battery": "lighter-battery",
        "a" * 50: "a" * 40,
        "x" * 39 + " yy": "x" * 39,
        "!!!": "change",
        "w" * 19 + " " + "w" * 20: "w" * 19 + "-" + "w" * 20,
    }
    for t, want in cases.items():
        got = edit._branch_slug(t)
        assert got == want, (t, got)
        assert len(got) <= 40


def test_propose_branch_name_is_cut_at_a_word(tmp_example, tmp_path, monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, cwd):
        calls.append(list(argv))
        if "--show-toplevel" in argv:
            return str(tmp_path) + "\n"
        if "status" in argv:
            return " M designs/example-tailsitter-wing/plane.yaml\n"
        if "--abbrev-ref" in argv:
            return "main\n"
        if "create" in argv:
            return "https://github.com/o/r/pull/8\n"
        return ""

    monkeypatch.setattr(edit, "_run", fake_run)
    monkeypatch.setenv("HANGAR_GH", "gh-test")
    r = call("design.propose", path=str(tmp_example), title="New test design from concept-a-param span change")
    assert r.ok, r.messages
    branch = "design/example-tailsitter-wing/new-test-design-from-concept-a-param"
    assert r.data["branch"] == branch
    assert ["git", "-C", str(tmp_path), "switch", "-c", branch] in calls
