"""U13.8-1: propulsion.max_thrust_n may be `pending`; every reader skips with a reason, never multiplies the text."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from hangar import design as design_mod
from hangar.checks import validate
from hangar.design import load_design
from hangar.ops import call
from hangar.propulsion import pending_motors
from hangar.sim import joint_load_cases

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
RECIPE_DIR = design_mod.REPO_ROOT / "tests" / "fixtures" / "mechanism-recipe"
KEY = "components[{}].propulsion.max_thrust_n"
# sha256 of the sorted (id, status, message) rows of an unmodified copy of example-tailsitter-wing, recorded on main
MAIN_ROWS_SHA = "349ef48f092c9e51da8d7a06a1e2ceaadae717cb53d3b49432ece743713e6f25"


@pytest.fixture
def tmp_example(tmp_path) -> Path:
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE_DIR, dst)
    return dst


def rows(d) -> list[tuple[str, str, str]]:
    card = validate(load_design(d))
    return [(r.check_id, r.status, r.message) for t in card.tiers for r in t.results]


def _set(d, motor, value):
    return call("design.set", path=str(d), key=KEY.format(motor), value=value, why="t")


def test_schema_accepts_pending_and_numbers(tmp_example):
    assert _set(tmp_example, "motor_l", "pending").ok
    assert "max_thrust_n: pending" in (tmp_example / "plane.yaml").read_text(encoding="utf-8")
    for bad in ("0", "nonsense"):
        r = _set(tmp_example, "motor_r", bad)
        assert not r.ok
        assert any("max_thrust_n" in m for m in r.messages), r.messages  # anyOf message names no type


def test_hover_rows_skip_with_reason(tmp_example):
    for m in ("motor_l", "motor_r"):
        assert _set(tmp_example, m, "pending").ok
    rs = rows(tmp_example)
    by = {i: (s, m) for i, s, m in rs}
    for cid in ("T3.hover_tw", "T2.hover_moment"):
        status, msg = by[cid]
        assert status == "SKIP", (cid, status, msg)
        assert "max_thrust_n is pending" in msg and "motor_l" in msg
    for i, s, m in rs:
        if i.startswith(("T3.control_authority", "T3.transition_margin", "T3.endurance")):
            assert s not in ("PASS", "FAIL"), (i, s, m)


def test_never_zero_or_one(tmp_example):
    assert _set(tmp_example, "motor_l", "pending").ok
    by = {i: (s, m) for i, s, m in rows(tmp_example)}
    for cid in ("T3.hover_tw", "T2.hover_moment"):
        assert by[cid][0] == "SKIP"
    for _, _, m in rows(tmp_example):
        assert "hover T/W 0.00" not in m and "hover T/W 1" not in m


def test_joint_thrust_case_skipped(tmp_example, tmp_path):
    ref = joint_load_cases(load_design(tmp_example))
    for m in ("motor_l", "motor_r"):
        assert _set(tmp_example, m, "pending").ok
    out = joint_load_cases(load_design(tmp_example))
    assert out["thrust"] == {}
    assert "max_thrust_n is pending" in out["thrust_skipped"]
    assert out["landing"].keys() == ref["landing"].keys()
    for k, v in ref["landing"].items():
        for a, b in zip(v["force_n"], out["landing"][k]["force_n"]):
            assert abs(a - b) < 1e-9


def test_numeric_designs_bit_identical(tmp_example):
    blob = json.dumps(sorted(rows(tmp_example)))
    assert hashlib.sha256(blob.encode()).hexdigest() == MAIN_ROWS_SHA


def test_docs_and_helpers(tmp_example):
    ref = (design_mod.REPO_ROOT / "docs" / "pdl" / "reference.md").read_text(encoding="utf-8")
    line = next(ln for ln in ref.splitlines() if "propulsion.max_thrust_n" in ln)
    assert "pending" in line
    for m in ("motor_l", "motor_r"):
        assert _set(tmp_example, m, "pending").ok
    d = load_design(tmp_example)
    assert pending_motors(d, ("cruise",)) == []
    assert pending_motors(d, ("lift", "both")) == ["motor_l", "motor_r"]
    assert pending_motors(d) == ["motor_l", "motor_r"]


def _recipe(tmp_path, name, thrust):
    dst = tmp_path / name
    shutil.copytree(RECIPE_DIR, dst)
    p = dst / "plane.yaml"
    text = p.read_text(encoding="utf-8")
    text = text.replace("attachments:\n", (
        "  - {id: motor, type: motor, geometry: {cylinder: {radius: 14, length: 30, axis: x}}, position: [-10, 0, 0], "
        "mass_g: 60, manufacturing: {method: purchased, part_number: \"x\"}, "
        f"propulsion: {{max_thrust_n: {thrust}, axis: [-1, 0, 0], role: cruise}}}}\n"
        "attachments:\n"
        "  - {id: stab-motor, parent: stab, child: motor, method: bolted, location: [0, 0, 0], rated_load_n: 50}\n"), 1)
    p.write_text(text, encoding="utf-8", newline="\n")
    return dst


def test_fixed_wing_cruise_motor_pending_changes_nothing_else(tmp_path):
    a, b = rows(_recipe(tmp_path, "pend", "pending")), rows(_recipe(tmp_path, "num", "12"))
    assert [r[:2] for r in a] == [r[:2] for r in b]
    assert [r for r in a if r not in b] == [r for r in b if r not in a] == []
