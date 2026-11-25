"""U13.6-2: set/apply replace a list value; remove a mid-list element of a one-line list."""
from __future__ import annotations

import difflib
import shutil

import pytest
import yaml

from hangar import design as design_mod
from hangar import pdledit
from hangar.ops import call

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"


@pytest.fixture
def tmp_example(tmp_path):
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE_DIR, dst)
    return dst


def test_replace_vector_in_flow_element():
    out = pdledit.replace_list("components:\n  - {id: a, position: [1, 2, 3], mass_g: 5}\n", "components[a].position", [4.5, 0, -2])[0]
    assert out == "components:\n  - {id: a, position: [4.5, 0, -2], mass_g: 5}\n"


def test_replace_vector_in_block_element():
    out = pdledit.replace_list("x:\n  - id: a\n    position: [1, 2, 3]\n", "x[a].position", [4, 5, 6])[0]
    assert out == "x:\n  - id: a\n    position: [4, 5, 6]\n"
    crlf = pdledit.replace_list("x:\r\n  - id: a\r\n    position: [1, 2, 3]\r\n", "x[a].position", [4, 5, 6])[0]
    assert crlf == "x:\r\n  - id: a\r\n    position: [4, 5, 6]\r\n"
    assert "\n" not in crlf.replace("\r\n", "")


def test_replace_refusals():
    with pytest.raises(Exception, match="is not a list"):
        pdledit.replace_list("a: 1\n", "a", [1])
    with pytest.raises(Exception, match="must not be empty"):
        pdledit.replace_list("a: [1]\n", "a", [])
    with pytest.raises(Exception, match="one-line"):
        pdledit.replace_list("a:\n  - 1\n  - 2\n", "a", [1])


def _lines_changed(a: str, b: str) -> int:
    return sum(1 for x in difflib.ndiff(a.splitlines(), b.splitlines()) if x.startswith("- "))


def test_set_op_replaces_position(tmp_example):
    d = tmp_example
    before = (d / "plane.yaml").read_text(encoding="utf-8")
    r = call("design.set", path=str(d), key="components[center_body].position", value="[155, 0, 1]", why="t")
    assert r.ok, r.messages
    after = (d / "plane.yaml").read_text(encoding="utf-8")
    assert yaml.safe_load(after)["components"][0]["position"] == [155, 0, 1]
    last = yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))[-1]
    assert last["old"] == [150, 0, 0] and last["new"] == [155, 0, 1] and last["kind"] == "modify"
    assert _lines_changed(before, after) == 1


def test_set_list_type_mismatches(tmp_example):
    d = tmp_example
    before = (d / "plane.yaml").read_bytes()
    r = call("design.set", path=str(d), key="components[center_body].mass_g", value="[1, 2]", why="t")
    assert not r.ok and "is not a list" in r.messages[0]
    assert (d / "plane.yaml").read_bytes() == before
    r = call("design.set", path=str(d), key="components[center_body].position", value="5", why="t")
    assert not r.ok
    assert (d / "plane.yaml").read_bytes() == before


def test_apply_set_list(tmp_example, tmp_path):
    d = tmp_example
    f = tmp_path / "edits.yaml"
    f.write_text(yaml.safe_dump([{"set": "components[center_body].position", "value": [155, 0, 1]},
                                 {"set": "components[center_body].mass_g", "value": 121}]), encoding="utf-8")
    n0 = len(yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8")) or []) if (d / "CHANGELOG.yaml").exists() else 0
    r = call("design.apply", path=str(d), edits=f, why="t")
    assert r.ok, r.messages
    c = yaml.safe_load((d / "plane.yaml").read_text(encoding="utf-8"))["components"][0]
    assert c["position"] == [155, 0, 1] and c["mass_g"] == 121
    log = yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert len(log) == n0 + 1 and log[-1]["kind"] == "batch"


def test_remove_mid_flow_element():
    rm = pdledit.remove_element
    assert rm("items: [{id: a}, {id: b}, {id: c}]\n", "items[b]") == ("items: [{id: a}, {id: c}]\n", {"id": "b"})
    assert rm("items: [{id: a}, {id: b}, {id: c}]\n", "items[a]")[0] == "items: [{id: b}, {id: c}]\n"
    assert rm("items: [{id: a}, {id: b}, {id: c}]\n", "items[c]")[0] == "items: [{id: a}, {id: b}]\n"
    assert rm("items: [{id: a}]\n", "items[a]")[0] == "items: []\n"
    assert rm("items: [{id: a, p: [1, 2]}, {id: b, p: [3]}]\n", "items[a]")[0] == "items: [{id: b, p: [3]}]\n"


def test_remove_after_design_add(tmp_path):
    from hangar.cli import BLANK_DESIGN_TEXT
    d = tmp_path / "x"
    d.mkdir()
    (d / "plane.yaml").write_text(BLANK_DESIGN_TEXT.replace("<id>", "x"), encoding="utf-8")
    for i in ("a1", "a2", "a3"):
        el = {"id": i, "parent": "datum", "child": "datum", "method": "glued", "location": [0, 0, 0], "embed_ok": True, "rated_load_n": 1}
        r = call("design.add", path=str(d), key="attachments", value=yaml.safe_dump(el, default_flow_style=True).strip(), why="t")
        assert r.ok, r.messages
    r = call("design.set", path=str(d), key="attachments[a2]", kind="remove", why="t")
    assert r.ok, r.messages
    ids = [a["id"] for a in yaml.safe_load((d / "plane.yaml").read_text(encoding="utf-8"))["attachments"]]
    assert ids == ["a1", "a3"]
