"""U13.8: BOM verified.method accepts webfetch (an agent fetched the vendor page); T8 counts it like the other methods."""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from hangar.checks import validate
from hangar.design import FAIL, PASS, WARN, load_design
from hangar.ops import call

FIX = Path(__file__).parent / "fixtures"


def _design(tmp_path):
    g = tmp_path / "g" / "plane.yaml"
    g.parent.mkdir(parents=True)
    shutil.copy(FIX / "gates-base.yaml", g)
    lines = g.read_text(encoding="utf-8").splitlines(keepends=True)
    at = next(i for i, ln in enumerate(lines) if ln.startswith("    - {id: motor"))
    lines[at + 1:at + 1] = ["    - id: servo\n", "      qty: 1\n"]
    g.write_text("".join(lines), encoding="utf-8")
    return g


def _line(g, item):
    data = yaml.safe_load(g.read_text(encoding="utf-8"))
    return next(it for it in data["bom"]["items"] if it["id"] == item)


def _result(card, check_id):
    for t in card.tiers:
        for r in t.results:
            if r.check_id == check_id:
                return r
    raise KeyError(check_id)


def test_verify_accepts_webfetch(tmp_path):
    g = _design(tmp_path)
    r = call("bom.verify", path=str(g), item="servo", method="webfetch", evidence="vendor page fetched", by="agent")
    assert r.exit_code == 0
    assert _line(g, "servo")["verified"]["method"] == "webfetch"


def test_schema_accepts_it(tmp_path):
    g = _design(tmp_path)
    assert call("bom.verify", path=str(g), item="servo", method="webfetch", evidence="vendor page fetched",
                by="agent").exit_code == 0
    card = validate(load_design(g), max_tier=0)
    assert not [r for t in card.tiers for r in t.results if r.status == FAIL and "schema" in r.check_id.lower()]
    bad = _design(tmp_path / "bad")
    assert call("bom.verify", path=str(bad), item="servo", method="browser", evidence="x", by="agent").exit_code == 0
    text = bad.read_text(encoding="utf-8").replace("method: browser", "method: carrier-pigeon")
    bad.write_text(text, encoding="utf-8")
    card = validate(load_design(bad), max_tier=0)
    assert [r for t in card.tiers for r in t.results if r.status == FAIL]


def test_t8_row_names_the_method(tmp_path):
    g = _design(tmp_path)
    assert call("bom.verify", path=str(g), item="servo", method="webfetch", evidence="vendor page fetched",
                by="agent").exit_code == 0
    card = validate(load_design(g), max_tier=8)
    r = _result(card, "T8.bom.verified.servo")
    assert r.status in (PASS, WARN)
    assert "(webfetch)" in r.message


def test_old_methods_unchanged(tmp_path):
    for method in ("browser", "datasheet", "in-hand"):
        g = _design(tmp_path / method)
        assert call("bom.verify", path=str(g), item="servo", method=method, evidence="e", by="agent").exit_code == 0
        assert _line(g, "servo")["verified"]["method"] == method
    root = Path(__file__).resolve().parent.parent
    assert "webfetch" in (root / "docs" / "pdl" / "reference.md").read_text(encoding="utf-8")
    assert "webfetch" in (root / "docs" / "cli.md").read_text(encoding="utf-8")
