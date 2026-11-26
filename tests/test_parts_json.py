"""parts.json: the part tree, attachment labels and per-part flags the viewer reads (U19.1 B2)."""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from test_expressions import _boxes

from hangar.design import load_design
from hangar.index import parts_json

REPO = Path(__file__).resolve().parents[1]


def test_concept_a_tree():
    pj = parts_json(load_design(REPO / "designs" / "concept-a"))
    assert len(pj["parts"]) == 115
    assert pj["root"] == "wng-001"
    assert max(p["depth"] for p in pj["parts"]) == 8
    root = next(p for p in pj["parts"] if p["id"] == pj["root"])
    assert root["parent"] is None and root["depth"] == 0
    assert len(pj["attachments"]) == 142
    assert sum(1 for p in pj["parts"] if p["parent"] is None) == 3
    assert all(len(p["position_mm"]) == 3 for p in pj["parts"])


def test_small_fixture(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    shutil.copy(REPO / "tests" / "fixtures" / "gates-base.yaml", d / "plane.yaml")
    pj = parts_json(load_design(d))
    root = next(p for p in pj["parts"] if p["id"] == "body")
    assert root["depth"] == 0 and pj["root"] == "body"
    assert not any(p["articulated"] for p in pj["parts"])
    labels = {a["label"] for a in pj["attachments"]}
    for p in pj["parts"]:
        if p["parent"] is not None:
            assert p["attachment"] in labels


def test_expression_positions_are_resolved(tmp_path):
    pj = parts_json(load_design(_boxes(tmp_path)))
    b = next(p for p in pj["parts"] if p["id"] == "b")
    assert b["position_mm"] == [20.0, 0.0, 0.0]


def test_expression_flag_and_cavity_flag(tmp_path):
    pj = parts_json(load_design(_boxes(tmp_path)))
    by = {p["id"]: p for p in pj["parts"]}
    assert by["b"]["position_expr"] is True
    assert by["a"]["position_expr"] is False
    assert all(p["has_cavities"] is False for p in pj["parts"])


def test_unreached_part_has_no_parent(tmp_path):
    d = _boxes(tmp_path)
    doc = yaml.safe_load((d / "plane.yaml").read_text())
    doc["attachments"] = []
    (d / "plane.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    by = {p["id"]: p for p in parts_json(load_design(d))["parts"]}
    for k in "bc":
        assert by[k]["parent"] is None and by[k]["depth"] == 0
