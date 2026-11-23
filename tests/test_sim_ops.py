"""sim.drop op (D23): wraps tier2_sim at the default drop height."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from click.testing import CliRunner

from hangar import pdledit
from hangar.design import load_standards
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


def _peak_n(r):
    return max(c["data"]["peak_n"] for c in r.data["checks"] if c["check_id"] == "T2.sim_drop_loads" and "peak_n" in c["data"])


def test_sim_drop_height_m_changes_the_peak_loads(monkeypatch):  # T20
    pytest.importorskip("mujoco")
    monkeypatch.chdir(REPO)
    low = call("sim.drop", path=EXAMPLE, height_m=0.1)
    high = call("sim.drop", path=EXAMPLE, height_m=1.0)
    assert (low.data["height_m"], high.data["height_m"]) == (0.1, 1.0)
    assert _peak_n(high) > _peak_n(low)
    assert call("sim.drop", path=EXAMPLE).data["height_m"] == load_standards()["sim"]["drop_height_m"]["value"]


def test_sim_drop_height_m_flag_on_the_cli(monkeypatch):  # T20
    pytest.importorskip("mujoco")
    monkeypatch.chdir(REPO)
    res = CliRunner().invoke(cli, ["sim", "drop", EXAMPLE, "--height-m", "0.2", "--json"])
    assert res.exit_code == 0, res.output
    assert json.loads(res.output)["data"]["height_m"] == 0.2


def test_sim_drop_negative_height_is_an_input_error(monkeypatch):  # T20
    monkeypatch.chdir(REPO)
    r = call("sim.drop", path=EXAMPLE, height_m=-1.0)
    assert r.exit_code == 2 and r.data.get("error") == "input"
    assert "must not be negative" in " ".join(r.messages)


def test_drop_test_at_the_standards_height_matches_tier2_sim(monkeypatch):  # T20: tier2 behaviour is unchanged
    pytest.importorskip("mujoco")
    from hangar.design import load_design
    from hangar.sim import drop_test, tier2_sim
    monkeypatch.chdir(REPO)
    design = load_design(REPO / EXAMPLE / "plane.yaml")
    std = load_standards()
    key = lambda rs: [(r.check_id, r.status, r.message) for r in rs]  # noqa: E731
    assert key(drop_test(design, float(std["sim"]["drop_height_m"]["value"]), std=std)) == key(tier2_sim(design, std, {}))
