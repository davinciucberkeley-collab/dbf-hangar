import shutil
from pathlib import Path

import pytest
import yaml

from hangar import pdledit
from hangar.ops import call
from hangar.pdledit import OpInputError

FIX = Path(__file__).parent / "fixtures" / "gates-base.yaml"


def test_flow_mapping_flow_list():
    t = "bom: {items: [{id: a}, {id: b}]}\n"
    assert pdledit.remove_element(t, "bom.items[a]") == ("bom: {items: [{id: b}]}\n", {"id": "a"})
    assert pdledit.remove_element(t, "bom.items[b]")[0] == "bom: {items: [{id: a}]}\n"
    assert pdledit.remove_element("bom: {items: [{id: a}]}\n", "bom.items[a]")[0] == "bom: {items: []}\n"


def test_block_nested_middle_and_only():
    t = "bom:\n  items:\n    - {id: a, qty: 1}\n    - {id: b, qty: 2}\n    - {id: c, qty: 3}\nx: 1\n"
    t = pdledit.remove_element(t, "bom.items[b]")[0]
    assert t == "bom:\n  items:\n    - {id: a, qty: 1}\n    - {id: c, qty: 3}\nx: 1\n"
    t = pdledit.remove_element(t, "bom.items[a]")[0]
    t = pdledit.remove_element(t, "bom.items[c]")[0]
    assert t == "bom:\n  items: []\nx: 1\n"


def test_block_element_with_comment_and_nested_block_entry():
    t = "bom:\n  items:\n    # a is the motor\n    - id: a\n      qty: 1\n    - id: b\n      qty: 2\n"
    assert pdledit.remove_element(t, "bom.items[a]")[0] == "bom:\n  items:\n    - id: b\n      qty: 2\n"


def test_list_below_an_element():
    t = "components:\n  - id: w\n    children:\n      - {id: c1}\n      - {id: c2}\n"
    assert pdledit.remove_element(t, "components[w].children[c1]")[0] == "components:\n  - id: w\n    children:\n      - {id: c2}\n"


def test_refusals():
    t = "bom:\n  items:\n    - {id: a, qty: 1}\n"
    for key, msg in [("bom.items[0]", "by index"), ("bom.items", "not one"), ("bom.items[a].qty", "not one"),
                     ("bom.items[zzz]", "no element with id"), ("bom.items[a][b]", "named by a key")]:
        with pytest.raises(OpInputError, match=msg):
            pdledit.remove_element(t, key)
    with pytest.raises(OpInputError, match="named by a key"):
        pdledit.remove_element("a: [x]\n", "a[x][y]")


def test_crlf():
    t = "bom:\r\n  items:\r\n    - {id: a}\r\n    - {id: b}\r\nx: 1\r\n"
    out = pdledit.remove_element(t, "bom.items[b]")[0]
    assert out == "bom:\r\n  items:\r\n    - {id: a}\r\nx: 1\r\n"
    out = pdledit.remove_element(out, "bom.items[a]")[0]
    assert out == "bom:\r\n  items: []\r\nx: 1\r\n"
    assert "\n" not in out.replace("\r\n", "")


def _copy(tmp_path):
    d = tmp_path / "g"
    d.mkdir()
    shutil.copy(FIX, d / "plane.yaml")
    return d


def _load(d):
    return yaml.safe_load((d / "plane.yaml").read_text(encoding="utf-8"))


def _log(d):
    return yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))


def test_op_remove_bom_line(tmp_path):
    d = _copy(tmp_path)
    r = call("design.set", path=str(d), key="bom.items[battery]", kind="remove", why="t")
    assert r.ok, r.messages
    assert [i["id"] for i in _load(d)["bom"]["items"]] == ["motor"]
    e = _log(d)[-1]
    assert e["kind"] == "remove" and e["key"] == "bom.items[battery]" and yaml.safe_load(e["old"])["id"] == "battery"
    r = call("design.set", path=str(d), key="bom.items[motor]", kind="remove", why="t")
    assert r.ok, r.messages
    assert _load(d)["bom"]["items"] == []


def test_apply_remove_nested(tmp_path):
    d = _copy(tmp_path)
    f = tmp_path / "edits.yaml"
    f.write_text(yaml.safe_dump([{"remove": "bom.items[battery]"}, {"remove": "wiring.harnesses[esc_to_motor_l]"}], sort_keys=False), encoding="utf-8")
    r = call("design.apply", path=str(d), edits=f, why="t")
    assert r.ok, r.messages
    p = _load(d)
    assert [i["id"] for i in p["bom"]["items"]] == ["motor"]
    assert p["wiring"]["harnesses"] == []
