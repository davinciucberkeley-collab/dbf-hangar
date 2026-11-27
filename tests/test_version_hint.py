"""U16.5-3 (T177): a T0.version FAIL names the migrate command; a blank design starts at PDL 1.3."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import hangar.cli
from hangar import design as design_mod
from hangar.checks import validate
from hangar.design import load_design
from hangar.ops import call

FIX = Path(__file__).parent / "fixtures" / "linkage-op"
HINT = " (run: plane design migrate <path> --write)"


@pytest.fixture
def designs(tmp_path, monkeypatch):
    d = tmp_path / "designs"
    d.mkdir()
    monkeypatch.setenv("PLANE_DESIGNS_DIR", str(d))
    monkeypatch.setattr(design_mod, "DESIGNS_DIR", d)
    monkeypatch.setattr(hangar.cli, "DESIGNS_DIR", d)
    return d


def test_add_linkage_on_1_2_says_migrate(tmp_path):
    f = tmp_path / "f"
    shutil.copytree(FIX, f)
    text = (f / "plane.yaml").read_text(encoding="utf-8")
    assert 'schema_version: "1.3"' in text
    (f / "plane.yaml").write_text(text.replace('schema_version: "1.3"', 'schema_version: "1.2"'),
                                  encoding="utf-8", newline="\n")
    r = call("design.add-linkage", path=str(f), servo="servo", hinge="stab-elev", station=0,
             arm_length=6.0, why="x")
    assert r.ok, r.messages
    rows = [x for x in r.data["rows"] if x[0] == "T0.version"]
    assert rows, "expected a T0.version row"
    for row in rows:
        msg = row[2]
        assert "kinematics" in msg or "schema_version" in msg, msg
        assert msg.endswith(HINT), msg


def test_blank_new_design_has_no_version_fail(designs):
    r = call("design.new", new_id="blank-x", blank=True)
    assert r.ok, r.messages
    path = designs / "blank-x" / "plane.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "display: {}\n", encoding="utf-8", newline="\n")
    card = validate(load_design(path), 0)
    fails = [x for t in card.tiers for x in t.results if x.check_id == "T0.version" and x.status == "FAIL"]
    assert fails == []
    # the same design at 1.2 has one FAIL that names the migrate command
    path.write_text(path.read_text(encoding="utf-8").replace('schema_version: "1.3"', 'schema_version: "1.2"'),
                    encoding="utf-8", newline="\n")
    card = validate(load_design(path), 0)
    fails = [x for t in card.tiers for x in t.results if x.check_id == "T0.version" and x.status == "FAIL"]
    assert len(fails) == 1, [x.message for x in fails]
    assert 'display needs schema_version "1.3"' in fails[0].message
    assert fails[0].message.endswith(HINT)
