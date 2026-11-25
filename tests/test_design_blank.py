"""U13.2-2: `plane design new --blank` makes a minimal valid design with no template data."""
from __future__ import annotations

import shutil

import pytest

import hangar.cli
from hangar import design as design_mod
from hangar.design import load_design
from hangar.ops import call

BLANK_TEXT = """# Blank design from `plane design new --blank`. Add parts with `plane design add`, change values with `plane design set`.
schema_version: "1.2"
id: <id>
name: "<id>"
status: concept
description: "Blank start: one placeholder root component `datum` (a 1 g point mass). Add the real root component, point `root` at it, then remove `datum`."
lineage: {derived_from: [], inspired_by: []}
morphology: {lift: fixed-wing, vtol_method: none, tail: conventional, propulsion_count: 1}
root: datum
components:
  - id: datum
    type: other
    geometry: {point_mass: {}}
    position: [0, 0, 0]
    mass_g: 1
attachments: []
"""


@pytest.fixture
def designs(tmp_path, monkeypatch):
    d = tmp_path / "designs"
    d.mkdir()
    monkeypatch.setenv("PLANE_DESIGNS_DIR", str(d))
    monkeypatch.setattr(design_mod, "DESIGNS_DIR", d)
    monkeypatch.setattr(hangar.cli, "DESIGNS_DIR", d)
    return d


def test_blank_creates_only_plane_yaml(designs):
    r = call("design.new", new_id="blank-x", blank=True)
    assert r.ok, r.messages
    assert sorted(p.name for p in (designs / "blank-x").iterdir()) == ["plane.yaml"]


def test_blank_text_is_the_exact_text(designs):
    r = call("design.new", new_id="blank-x", blank=True)
    assert r.ok, r.messages
    raw = (designs / "blank-x" / "plane.yaml").read_bytes()
    assert raw == BLANK_TEXT.replace("<id>", "blank-x").encode("utf-8")
    assert b"\r" not in raw


def test_blank_passes_tier0(designs):
    assert call("design.new", new_id="blank-x", blank=True).ok
    r = call("design.validate", path=str(designs / "blank-x"), tier="0")
    assert r.ok is True
    assert "FAIL" not in " ".join(r.messages)


def test_blank_loads_and_has_one_component(designs):
    assert call("design.new", new_id="blank-x", blank=True).ok
    d = load_design(designs / "blank-x")
    assert d.data["components"][0]["id"] == "datum"
    assert d.data["root"] == "datum"


def test_blank_refuses_existing_and_bad_id_and_template_mix(designs):
    assert call("design.new", new_id="blank-x", blank=True).ok
    r = call("design.new", new_id="blank-x", blank=True)
    assert r.ok is False
    assert any("already exists" in m for m in r.messages)
    assert call("design.new", new_id="Bad Id", blank=True).ok is False
    r = call("design.new", new_id="b2", blank=True, template="concept-a")
    assert r.ok is False
    assert any("exclude each other" in m for m in r.messages)
    assert not (designs / "b2").exists()
