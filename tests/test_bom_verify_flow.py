"""U13.8: bom verify stamps flow-style BOM lines byte-preservingly (T149)."""
from __future__ import annotations

import difflib
import shutil
from datetime import date
from pathlib import Path

import yaml

from hangar.checks import validate
from hangar.cli import BLANK_DESIGN_TEXT
from hangar.design import FAIL, load_design
from hangar.ops import call

FIX = Path(__file__).parent / "fixtures"


def _gates(tmp_path):
    g = tmp_path / "g" / "plane.yaml"
    g.parent.mkdir(parents=True)
    shutil.copy(FIX / "gates-base.yaml", g)
    return g


def _blank(tmp_path, text=None):
    g = tmp_path / "b" / "plane.yaml"
    g.parent.mkdir(parents=True)
    g.write_text(text if text is not None else BLANK_DESIGN_TEXT.replace("<id>", "x"), encoding="utf-8")
    return g


def _changed(before: str, after: str):
    return [ln for ln in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0)
            if (ln.startswith("+") or ln.startswith("-")) and not ln.startswith(("+++", "---"))]


def _item(g, item):
    data = yaml.safe_load(g.read_text(encoding="utf-8"))
    return next(it for it in data["bom"]["items"] if it.get("id") == item)


def test_verify_a_line_added_by_design_add(tmp_path):
    g = _gates(tmp_path)
    assert call("design.add", path=str(g), key="bom.items", value="{id: servo, qty: 1}", why="t").exit_code == 0
    before = g.read_text(encoding="utf-8")
    r = call("bom.verify", path=str(g), item="servo", method="webfetch", evidence="vendor page fetched", by="agent")
    assert r.exit_code == 0
    today = date.today().isoformat()
    assert _item(g, "servo")["verified"] == {"by": "agent", "date": today, "method": "webfetch",
                                              "evidence": "vendor page fetched"}
    after = g.read_text(encoding="utf-8")
    changed = _changed(before, after)
    assert changed == ["-    - {id: servo, qty: 1}",
                       f'+    - {{id: servo, qty: 1, verified: {{by: agent, date: "{today}", method: webfetch, '
                       f'evidence: "vendor page fetched"}}}}'], changed


def test_flow_list_inside_flow_mapping(tmp_path):
    g = _blank(tmp_path)
    assert call("design.set", path=str(g), key="bom", kind="add", value="{items: [{id: s1, qty: 1}]}",
                why="t").exit_code == 0
    before = g.read_text(encoding="utf-8")
    r = call("bom.verify", path=str(g), item="s1", method="datasheet", evidence="datasheet p3", by="agent")
    assert r.exit_code == 0
    after = g.read_text(encoding="utf-8")
    changed = _changed(before, after)
    assert len(changed) == 2 and changed[0].startswith("-") and changed[1].startswith("+"), changed
    assert _item(g, "s1")["verified"] == {"by": "agent", "date": date.today().isoformat(),
                                           "method": "datasheet", "evidence": "datasheet p3"}


def test_block_style_line_is_unchanged(tmp_path):
    text = BLANK_DESIGN_TEXT.replace("<id>", "x") + "bom:\n  items:\n    - id: a\n      qty: 1\n"
    g = _blank(tmp_path, text)
    r = call("bom.verify", path=str(g), item="a", method="webfetch", evidence="e", by="agent")
    assert r.exit_code == 0
    today = date.today().isoformat()
    expected = text + f'      verified: {{by: "agent", date: "{today}", method: webfetch, evidence: "e"}}\n'
    assert g.read_text(encoding="utf-8") == expected


def test_multiline_flow_element_is_refused(tmp_path):
    text = BLANK_DESIGN_TEXT.replace("<id>", "x") + "bom:\n  items:\n    - {id: a,\n       qty: 1}\n"
    g = _blank(tmp_path, text)
    r = call("bom.verify", path=str(g), item="a", method="webfetch", evidence="e", by="agent")
    assert r.ok is False
    assert "edit the file by hand" in " ".join(r.messages)
    assert g.read_text(encoding="utf-8") == text


def test_already_verified_and_crlf(tmp_path):
    g = _gates(tmp_path)
    r = call("bom.verify", path=str(g), item="battery", method="browser", evidence="x", by="agent")
    assert r.ok is False
    assert "already verified by team" in " ".join(r.messages)

    assert call("design.add", path=str(g), key="bom.items", value="{id: servo, qty: 1}", why="t").exit_code == 0
    crlf = g.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    g.write_bytes(crlf)
    r = call("bom.verify", path=str(g), item="servo", method="webfetch", evidence="vendor page fetched", by="agent")
    assert r.exit_code == 0
    out = g.read_bytes()
    assert b"\r\n" in out
    assert out.count(b"\n") == out.count(b"\r\n")
    assert _item(g, "servo")["verified"]["method"] == "webfetch"


def test_t8_sees_the_stamp(tmp_path):
    g = _gates(tmp_path)
    assert call("design.add", path=str(g), key="bom.items", value="{id: servo, qty: 1}", why="t").exit_code == 0
    assert call("bom.verify", path=str(g), item="servo", method="webfetch", evidence="vendor page fetched",
                by="agent").exit_code == 0
    card = validate(load_design(g))
    rows = [r for t in card.tiers for r in t.results if "servo" in (r.message or "") and "(webfetch)" in (r.message or "")]
    assert rows, [r.message for t in card.tiers for r in t.results if "servo" in (r.message or "")]
