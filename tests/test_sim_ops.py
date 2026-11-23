"""sim.drop op (D23): wraps tier2_sim at the default drop height."""
from __future__ import annotations

from pathlib import Path

import pytest

from click.testing import CliRunner

from hangar import pdledit
from hangar.cli import cli
from hangar.ops import call, registry

REPO = Path(__file__).resolve().parents[1]
EXAMPLE = "designs/example-tailsitter-wing"
FIX = "python -m pip install 'mujoco>=3'"


def test_sim_drop_is_registered():
    assert "sim.drop" in registry()


def test_sim_drop_runs_on_example_design(monkeypatch):
    pytest.importorskip("mujoco")
    monkeypatch.chdir(REPO)
    r = call("sim.drop", path=EXAMPLE)
    assert r.exit_code == 0, r.messages
    assert r.ok is True
    checks = r.data["checks"]
    ids = {c["check_id"] for c in checks}
    assert {"T2.sim_drop_loads", "T2.sim_rest", "T2.sim_stable"} <= ids
    assert all(c["status"] != "FAIL" for c in checks)


def test_sim_drop_without_mujoco_gives_skip_with_fix(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "mujoco", None)  # makes `import mujoco` raise ImportError
    monkeypatch.chdir(REPO)
    r = call("sim.drop", path=EXAMPLE)
    assert r.ok is True  # D37: a missing tool is SKIP, not FAIL
    assert r.exit_code == 0
    assert r.data["status"] == "SKIP"
    assert r.skipped == ["sim.drop"]
    text = "\n".join(r.messages)
    assert "mujoco not installed" in text
    assert FIX in text


def test_sim_drop_without_mujoco_prints_skip_first_and_exits_0(monkeypatch):  # D37
    monkeypatch.setitem(__import__("sys").modules, "mujoco", None)
    monkeypatch.chdir(REPO)
    res = CliRunner().invoke(cli, ["sim", "drop", EXAMPLE])
    assert res.exit_code == 0, res.output
    assert res.output.startswith("SKIP: mujoco not installed")


def test_sim_drop_resolves_the_design_path_through_pdledit(monkeypatch):  # T21
    monkeypatch.setitem(__import__("sys").modules, "mujoco", None)
    monkeypatch.chdir(REPO)
    seen = []
    real = pdledit.resolve_design_path
    monkeypatch.setattr(pdledit, "resolve_design_path", lambda p: seen.append(str(p)) or real(p))
    call("sim.drop", path=EXAMPLE)
    assert seen == [EXAMPLE]


def test_sim_drop_bad_path_is_input_error(monkeypatch):
    monkeypatch.chdir(REPO)
    r = call("sim.drop", path="designs/does-not-exist")
    assert r.exit_code == 2
    assert r.data.get("error") == "input"
