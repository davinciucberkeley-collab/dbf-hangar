"""U1.4: design.set/get/diff/copy/sweep/propose."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from hangar import design as design_mod
from hangar.ops import call
from hangar.ops import edit

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
CONCEPT_A_DIR = design_mod.DESIGNS_DIR / "concept-a"


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
    assert (tmp_path / "sweeps" / "example-tailsitter-wing" / "1" / "plane.yaml").is_file()


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
    assert "--title" in gh[0] and "design(example-tailsitter-wing): Lighter battery" in gh[0]
    commit = [c for c in calls if "commit" in c][0]
    assert "Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>" in commit[-1]
    assert calls[-1] == ["git", "-C", str(tmp_path), "switch", "main"]      # back where we started


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
