"""U19.1 B6: check rows name parts one way (data.component one id, data.parts ids only, data.pair exactly two ids)."""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from hangar.design import load_design, load_standards
from hangar.checks import _kinematic_link_row, interference_rows, tier0_schema
from test_expressions import _boxes

FIXTURES = Path(__file__).parent / "fixtures"
CORE = Path(__file__).resolve().parent.parent / "core" / "hangar"


def test_schema_row_names_paths_not_parts(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    shutil.copy(FIXTURES / "mech-good.yaml", d / "plane.yaml")
    doc = yaml.safe_load((d / "plane.yaml").read_text())
    doc["components"][0]["mass_g"] = "heavy"
    (d / "plane.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    rows = [r for r in tier0_schema(load_design(d)).results if r.check_id == "T0.schema"]
    assert rows
    for r in rows:
        assert isinstance(r.data["paths"], list)
        assert all(isinstance(p, str) for p in r.data["paths"])
        assert "parts" not in r.data


def test_interference_row_pair_is_two_ids(tmp_path):
    d = _boxes(tmp_path, cz=15)
    rows = [r for r in interference_rows(load_design(d), load_standards()) if r.check_id == "T1.interference"]
    assert len(rows) == 1
    pair = rows[0].data["pair"]
    assert len(pair) == 2
    assert set(pair) <= {"a", "b", "c"}


def test_kinematic_link_row_names_ids_not_pair():
    r = _kinematic_link_row([("wng-009-r", "wng-010-r"), ("mec-003-r", "mec-004-r")])
    assert r.check_id == "T1.kinematic_link"
    assert r.status == "SKIP"
    assert r.data["unchecked_pairs"] == ["wng-009-r & wng-010-r", "mec-003-r & mec-004-r"]
    assert r.data["parts"] == ["mec-003-r", "mec-004-r", "wng-009-r", "wng-010-r"]
    assert "pair" not in r.data
    assert "2 pair(s) not checked" in r.message


def test_no_data_pair_holds_strings_with_ampersand():
    for name in ("checks.py", "gates/mechanisms.py"):
        text = (CORE / name).read_text()
        assert '{"pair": [f"' not in text
        assert '{"pair": row.data' not in text
