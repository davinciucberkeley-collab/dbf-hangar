"""sim.drop op (D23): wraps tier2_sim at the default drop height."""
from __future__ import annotations

from pathlib import Path

import pytest

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
    assert r.ok is False
    assert r.exit_code == 1
    text = "\n".join(r.messages)
    assert "mujoco not installed" in text
    assert FIX in text


def test_sim_drop_bad_path_is_input_error(monkeypatch):
    monkeypatch.chdir(REPO)
    r = call("sim.drop", path="designs/does-not-exist")
    assert r.exit_code == 2
    assert r.data.get("error") == "input"
