"""U13.2-1: plane design add appends one list element."""
from __future__ import annotations

import difflib
import shutil

import pytest
import yaml

from hangar import design as design_mod
from hangar import pdledit
from hangar.ops import call, registry

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
COMP = "{id: tail_probe, type: other, geometry: {point_mass: {}}, position: [10, 0, 0], mass_g: 2}"
ATT = "{id: probe-mount, parent: center_body, child: tail_probe, method: glued, location: [10, 0, 0], embed_ok: true, rated_load_n: 5}"


@pytest.fixture
def d(tmp_path):
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE_DIR, dst)
    return dst


def _add(d, key, value, why="t"):
    return call("design.add", path=str(d), key=key, value=value, why=why)


def _only_inserts(a: str, b: str) -> bool:
    ops = difflib.SequenceMatcher(None, a.splitlines(), b.splitlines(), autojunk=False).get_opcodes()
    return all(t in ("equal", "insert") for t, *_ in ops)


def test_append_block_component_after_last(d):
    p = d / "plane.yaml"
    before = p.read_bytes().decode()
    n = len(yaml.safe_load(before)["components"])
    r = _add(d, "components", COMP)
    assert r.ok
    assert r.data["id"] == "tail_probe"
    after = p.read_bytes().decode()
    comps = yaml.safe_load(after)["components"]
    assert comps[-1]["id"] == "tail_probe" and len(comps) == n + 1
    assert "  - id: tail_probe\n" in after
    assert _only_inserts(before, after)


def test_append_flow_attachment_is_one_line(d):
    p = d / "plane.yaml"
    assert _add(d, "components", COMP).ok
    before = p.read_bytes().decode()
    assert _add(d, "attachments", ATT).ok
    after = p.read_bytes().decode()
    assert any(ln.startswith("  - {id: probe-mount") for ln in after.splitlines())
    assert len(after.splitlines()) == len(before.splitlines()) + 1
    assert _only_inserts(before, after)


def test_duplicate_id_refused_nothing_written(d):
    p, log = d / "plane.yaml", d / "CHANGELOG.yaml"
    b1 = p.read_bytes()
    b2 = log.read_bytes() if log.exists() else None
    r = _add(d, "components", "{id: wing, type: other, geometry: {point_mass: {}}, position: [0, 0, 0], mass_g: 1}")
    assert r.ok is False
    assert any("id 'wing' already exists" in m for m in r.messages)
    assert p.read_bytes() == b1
    assert (log.read_bytes() if log.exists() else None) == b2


def test_schema_error_refused_nothing_written(d):
    p, log = d / "plane.yaml", d / "CHANGELOG.yaml"
    b1 = p.read_bytes()
    b2 = log.read_bytes() if log.exists() else None
    r = _add(d, "components", "{id: bad1, type: nonsense}")
    assert r.ok is False
    assert p.read_bytes() == b1
    assert (log.read_bytes() if log.exists() else None) == b2


def test_bad_shapes(d):
    cases = [("components", "[1, 2]", "must be a {mapping}"),
             ("components", "{type: other}", "needs a string id"),
             ("components[wing]", COMP, "name the list by its key"),
             ("nolist", COMP, "create it first")]
    for key, value, msg in cases:
        r = _add(d, key, value)
        assert r.ok is False, key
        assert any(msg in m for m in r.messages), (key, r.messages)


def test_changelog_entry(d):
    assert _add(d, "components", COMP).ok
    last = yaml.safe_load((d / "CHANGELOG.yaml").read_bytes().decode())[-1]
    assert last["kind"] == "add"
    assert last["key"] == "components[tail_probe]"
    assert last["old"] is None
    assert last["new"]["id"] == "tail_probe"
    assert last["why"] == "t"


def test_text_cases():
    assert pdledit.append_element("bom: {items: [{id: a, qty: 1}]}\n", "bom.items", {"id": "b", "qty": 2})[0] \
        == "bom: {items: [{id: a, qty: 1}, {id: b, qty: 2}]}\n"
    src = "x:\n  - id: a\n    n: 1\n  - id: b\n    n: 2\n"
    assert pdledit.append_element(src, "x", {"id": "c", "n": 3})[0] == src + "  - id: c\n    n: 3\n"
    assert pdledit.append_element("attachments: []\n", "attachments", {"id": "a"})[0] == "attachments: [{id: a}]\n"


def test_crlf_preserved():
    src = "x:\n  - id: a\n    n: 1\n  - id: b\n    n: 2\n".replace("\n", "\r\n")
    out = pdledit.append_element(src, "x", {"id": "c", "n": 3})[0]
    assert out == src + "  - id: c\r\n    n: 3\r\n"
    assert "\n" not in out.replace("\r\n", "")


def test_op_registered():
    from hangar import mcp_server
    assert "design.add" in registry()
    assert "design_add" in mcp_server.GENERATED
