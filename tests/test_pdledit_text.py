"""T34 (and T8): design.set on a text value such as Name or Description saves it, or refuses with exit 2 and writes nothing."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from hangar import design as design_mod, pdledit
from hangar.ops import OpInputError, call

FROZEN = design_mod.REPO_ROOT / "tests" / "fixtures" / "concept-a-frozen"


@pytest.fixture
def tmp_concept_a(tmp_path) -> Path:
    dst = tmp_path / "concept-a"
    dst.mkdir()
    shutil.copy(FROZEN / "plane.yaml", dst / "plane.yaml")
    return dst


def test_name_with_a_comma_saves_and_only_that_line_changes(tmp_concept_a):
    plane = tmp_concept_a / "plane.yaml"
    before = plane.read_bytes()
    r = call("design.set", path=str(tmp_concept_a), key="name", value="Concept A, second try", why="t", kind="modify")
    assert r.ok, r.messages
    after = plane.read_bytes()
    assert yaml.safe_load(after)["name"] == "Concept A, second try"
    a, b = before.splitlines(), after.splitlines()
    assert len(a) == len(b)
    assert [i for i, (x, y) in enumerate(zip(a, b)) if x != y] == [7]


def test_folded_description_saves_as_one_quoted_line(tmp_concept_a):
    plane = tmp_concept_a / "plane.yaml"
    before = plane.read_text(encoding="utf-8")
    r = call("design.set", path=str(tmp_concept_a), key="description", value="A shorter description, with a comma.",
             why="t", kind="modify")
    assert r.ok, r.messages
    after = plane.read_text(encoding="utf-8")
    assert yaml.safe_load(after)["description"] == "A shorter description, with a comma."
    assert 'description: "A shorter description, with a comma."\nlineage:' in after
    start = before.index("description: >")
    assert before[:start] == after[:start]
    assert before[before.index("\nlineage:"):] == after[after.index("\nlineage:"):]


def test_plain_text_value_stops_before_a_trailing_comment():
    text = "name: Old, name  # keep me\nx: 1\n"
    assert pdledit.patch_text(text, "name", "New, name") == 'name: "New, name"  # keep me\nx: 1\n'


def test_a_value_inside_a_flow_list_still_stops_at_the_comma():
    assert pdledit.patch_text("a: [x, y]\n", "a[1]", "z") == "a: [x, z]\n"


def test_unparseable_result_exits_2_and_writes_nothing(tmp_concept_a, monkeypatch):
    plane = tmp_concept_a / "plane.yaml"
    before = plane.read_bytes()
    monkeypatch.setattr(pdledit, "render_scalar", lambda v: '"never closed')
    r = call("design.set", path=str(tmp_concept_a), key="name", value="x", why="t", kind="modify")
    assert r.ok is False and r.exit_code == 2
    assert plane.read_bytes() == before
    assert not (tmp_concept_a / "CHANGELOG.yaml").exists()


def test_patch_text_turns_a_parse_error_into_op_input_error(monkeypatch):
    monkeypatch.setattr(pdledit, "render_scalar", lambda v: '"never closed')
    with pytest.raises(OpInputError):
        pdledit.patch_text("name: Old\n", "name", "x")
