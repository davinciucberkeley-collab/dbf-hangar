"""U4.36-3: removing a list's only element leaves an empty list."""
from __future__ import annotations

import shutil

import pytest
import yaml

from hangar import design as design_mod
from hangar import pdledit
from hangar.ops import call

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
ATT = "wing-body mount-l mount-r motor-l motor-r prop-l prop-r fin-l fin-r battery-bay fc-mount".split()
COMP = "center_body wing mount_l mount_r motor_l motor_r prop_l prop_r fin_l fin_r battery flight_controller".split()


@pytest.fixture
def d(tmp_path):
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE_DIR, dst)
    return dst


def test_only_block_element_becomes_empty_list():
    out = pdledit.remove_element("a: 1\nitems:\n  - id: x\n    n: 1\nb: 2\n", "items[x]")
    assert out == ("a: 1\nitems: []\nb: 2\n", {"id": "x", "n": 1})


def test_only_flow_element_and_header_comment():
    out = pdledit.remove_element("items:  # the list\n  - {id: x, n: 1}\nb: 2\n", "items[x]")[0]
    assert out == "items: []  # the list\nb: 2\n"


def test_preceding_id_comment_goes_with_it():
    assert pdledit.remove_element("items:\n  # x is the only one\n  - id: x\n", "items[x]")[0] == "items: []\n"


def test_crlf():
    out = pdledit.remove_element("a: 1\r\nitems:\r\n  - id: x\r\n    n: 1\r\nb: 2\r\n", "items[x]")[0]
    assert out == "a: 1\r\nitems: []\r\nb: 2\r\n"
    assert "\n" not in out.replace("\r\n", "")


def test_other_cases_unchanged():
    assert pdledit.remove_element("items:\n  - id: x\n  - id: y\n", "items[x]")[0] == "items:\n  - id: y\n"


def test_op_empties_attachments_of_a_design(d):
    r = call("design.set", path=str(d), key="attachments[wing-body]", kind="remove", why="t",
             also=[f"attachments[{i}]=" for i in ATT[1:]])
    assert r.ok, r.messages
    text = (d / "plane.yaml").read_text(encoding="utf-8")
    assert yaml.safe_load(text)["attachments"] == []
    assert "\nattachments: []" in text
    log = yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert len(log) == 11 and all(e["kind"] == "remove" for e in log)


def test_components_cannot_be_emptied(d):
    before = (d / "plane.yaml").read_bytes()
    r = call("design.set", path=str(d), key="components[center_body]", kind="remove", why="t",
             also=[f"components[{i}]=" for i in COMP[1:]])
    assert r.ok is False and "non-empty" in " ".join(r.messages), r.messages
    assert (d / "plane.yaml").read_bytes() == before
