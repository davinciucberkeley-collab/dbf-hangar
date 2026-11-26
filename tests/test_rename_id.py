"""T168: plane design rename-id renames an id everywhere it is a value or list item, byte-preserving."""
from __future__ import annotations

import copy
import difflib
import re
import shutil

import pytest
import yaml

from hangar import design as design_mod
from hangar.ops import call

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
SKIP_TOP = {"id", "name", "description", "notes", "lineage", "authors", "status"}

COMP = """  - id: {i}
    type: other
    geometry: {{point_mass: {{}}}}
    position: [10, 0, 0]
    mass_g: 2

"""
TAIL = """  - {id: rn-a1, parent: rn-old, child: wing, method: glued, location: [10, 0, 0], rated_load_n: 5}
  - {id: rn-a2, parent: center_body, child: rn-old, method: glued, location: [10, 0, 0], rated_load_n: 5}
mechanisms:
  - id: rn-mech
    driver: rn-old
    driven: [rn-old]
    expect: [{attachment: rn-old, ratio: 1}]
    link: {driver_end: rn-old, follower_end: rn-a1}
wiring:
  harnesses:
    - id: rn-h1
      from: rn-old
      to: battery
      route: ["rn-old", wing]
    - id: rn-h2
      from: battery
      to: flight_controller
      route:
        - center_body
        - rn-old
transport:
  disassembly:
    - group: g1
      component_ids:
        - wing
        - rn-old
assembly:
  sequence:
    - step: 1
      add:
        - rn-old
      note: put rn-old on
    - step: 2
      add:
        - wing
bom:
  items:
    - id: rn-b1
      qty: 1
      component_ids:
        - rn-old
        - wing
files:
  cad:
    - {path: meshes/rn-old.stl, format: stl, role: derived}
notes: rn-old
"""


def make(tmp_path, old_comp=True, new_comp=False, name="ref"):
    d = tmp_path / name
    shutil.copytree(EXAMPLE_DIR, d)
    t = (d / "plane.yaml").read_bytes().decode()
    comps = (COMP.format(i="rn-old") if old_comp else "") + (COMP.format(i="rn-new") if new_comp else "")
    assert "\nattachments:\n" in t
    t = t.replace("\nattachments:\n", "\n" + comps.rstrip("\n") + "\n\nattachments:\n", 1)
    if not t.endswith("\n"):
        t += "\n"
    (d / "plane.yaml").write_bytes((t + TAIL).encode())
    return d


def _bytes(d):
    log = d / "CHANGELOG.yaml"
    return (d / "plane.yaml").read_bytes(), log.read_bytes() if log.exists() else None


def _swap(node, old, new, top=True):
    if isinstance(node, dict):
        return {k: (v if top and k in SKIP_TOP else _swap(v, old, new, False)) for k, v in node.items()}
    if isinstance(node, list):
        return [_swap(x, old, new, False) for x in node]
    return new if node == old else node


def _count(node, old, top=True):
    if isinstance(node, dict):
        return sum(0 if top and k in SKIP_TOP else _count(v, old, False) for k, v in node.items())
    if isinstance(node, list):
        return sum(_count(x, old, False) for x in node)
    return 1 if node == old else 0


def _rename(d, old="rn-old", new="rn-new", why="t"):
    return call("design.rename-id", path=str(d), old=old, new=new, why=why)


def _fails(d, text, **kw):
    r = _rename(d, **kw)
    assert r.ok is False and text in " ".join(r.messages), r.messages


def test_rename_every_reference(tmp_path):
    d = make(tmp_path)
    before = yaml.safe_load((d / "plane.yaml").read_bytes().decode())
    r = _rename(d)
    assert r.ok
    after = yaml.safe_load((d / "plane.yaml").read_bytes().decode())
    assert after == _swap(before, "rn-old", "rn-new")
    assert _count(after, "rn-old") == 0 and _count(after, "rn-new") == r.data["count"] > 10
    assert after["notes"] == "rn-old"
    assert after["files"]["cad"][0]["path"] == "meshes/rn-old.stl"
    assert any(m.startswith("not renamed:") and "files.cad[0].path" in m for m in r.messages)


def test_only_reference_lines_change(tmp_path):
    d = make(tmp_path)
    a = (d / "plane.yaml").read_bytes().decode()
    r = _rename(d)
    b = (d / "plane.yaml").read_bytes().decode()
    ops = difflib.SequenceMatcher(None, a.splitlines(), b.splitlines(), autojunk=False).get_opcodes()
    # adjacent changed lines come back as one multi-line replace of equal length: still a line-for-line change
    assert all(t == "equal" or (t == "replace" and i2 - i1 == j2 - j1) for t, i1, i2, j1, j2 in ops)
    replaced = sum(i2 - i1 for t, i1, i2, j1, j2 in ops if t == "replace")
    hit = [ln for ln in a.splitlines() if "rn-old" in ln and "meshes/" not in ln and not ln.startswith("notes:") and "put rn-old" not in ln]
    assert replaced == len(hit)
    assert r.data["count"] == sum(ln.count("rn-old") for ln in hit)


def test_quotes_and_crlf_preserved(tmp_path):
    d = make(tmp_path)
    p = d / "plane.yaml"
    p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
    _rename(d)
    out = p.read_bytes()
    assert b'["rn-new", wing]' in out
    assert b"\r\n" in out and not re.search(rb"(?<!\r)\n", out)


def test_idempotent(tmp_path):
    d = make(tmp_path)
    assert _rename(d).data["changed"] is True
    first = _bytes(d)
    r = _rename(d)
    assert r.ok and r.data["changed"] is False
    assert "already renamed" in "\n".join(r.messages)
    assert _bytes(d) == first


def test_unknown_id_error(tmp_path):
    d = make(tmp_path)
    before = _bytes(d)
    _fails(d, "unknown id", old="nope-zz", new="nope-yy")
    assert _bytes(d) == before


def test_collision_error(tmp_path):
    d = make(tmp_path, new_comp=True)
    before = _bytes(d)
    _fails(d, "both")
    assert _bytes(d) == before


def test_duplicate_in_list_error(tmp_path):
    d = make(tmp_path, old_comp=False, new_comp=True)
    p = d / "plane.yaml"
    t = p.read_bytes().decode().replace("        - rn-old\n        - wing\nfiles:", "        - rn-old\n        - rn-new\nfiles:")
    assert "rn-new\nfiles:" in t
    p.write_bytes(t.encode())
    before = _bytes(d)
    _fails(d, "would duplicate")
    assert _bytes(d) == before


def test_stale_id_repoint(tmp_path):
    d = make(tmp_path, old_comp=False, new_comp=True)
    before = yaml.safe_load((d / "plane.yaml").read_bytes().decode())
    r = _rename(d)
    assert r.ok and r.data["changed"] is True
    after = yaml.safe_load((d / "plane.yaml").read_bytes().decode())
    assert after == _swap(before, "rn-old", "rn-new")
    assert _count(before, "rn-old") == r.data["count"] and _count(after, "rn-old") == 0
    assert [c["id"] for c in after["components"]].count("rn-new") == 1


def test_bad_new_id_and_empty_why(tmp_path):
    d = make(tmp_path)
    before = _bytes(d)
    _fails(d, "", new="Bad Id!")
    _fails(d, "why must not be empty", why=" ")
    _fails(d, "", new="rn-old")
    assert _bytes(d) == before


def test_changelog_entry(tmp_path):
    d = make(tmp_path)
    r = _rename(d, why="fix stale id")
    log = yaml.safe_load((d / "CHANGELOG.yaml").read_bytes().decode())
    assert len(log) == 1
    e = log[0]
    assert e["key"] == "rename-id" and e["old"] == "rn-old" and e["new"] == "rn-new" and e["why"] == "fix stale id"
    assert e["paths"] == r.data["paths"] and len(e["paths"]) == r.data["count"]


def test_validate_unchanged_except_ids(tmp_path):
    d = make(tmp_path)
    r = _rename(d)
    assert r.ok
    v = call("design.validate", path=str(d), tier="0")
    assert v.ok
