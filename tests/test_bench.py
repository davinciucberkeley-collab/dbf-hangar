from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from hangar.ops import bench, call, registry

REPO = Path(__file__).resolve().parents[1]
TASKS = ["mass-cut-10", "fix-static-margin", "add-working-flap"]
FLAP = "attachments[flap-l].articulation."
# Hand-made known-good solutions: (key, value, kind) applied with design.set on the workspace copy.
SOLUTIONS = {
    "mass-cut-10": [("components[pwr-001].mass_g", "140", "modify")],
    "fix-static-margin": [("components[fin-001-l].mass_g", "42.1", "modify"),
                          ("components[fin-001-r].mass_g", "42.1", "modify")],
    "add-working-flap": [(FLAP + "range_deg[0]", "-25", "modify"), (FLAP + "range_deg[1]", "25", "modify"),
                         (FLAP + "poses.up", "25", "modify"), (FLAP + "poses.down", "-25", "modify")],
}
TASK_PARAMS = [pytest.param(t, marks=pytest.mark.slow) if t == "fix-static-margin" else t for t in TASKS]


@pytest.fixture
def fake_repo(tmp_path):
    """A small stand-in for the repo root: concept-a (no fea/), bench/ (tasks + fixtures), agents, dummy core/schema/standards."""
    root = tmp_path / "repo"
    (root / "designs").mkdir(parents=True)
    shutil.copytree(REPO / "designs" / "concept-a", root / "designs" / "concept-a", ignore=shutil.ignore_patterns("fea"))
    shutil.copytree(REPO / "bench", root / "bench", ignore=shutil.ignore_patterns("results"))
    shutil.copytree(REPO / ".claude" / "agents", root / ".claude" / "agents")
    for top, name in (("core/hangar", "dummy.py"), ("schema", "s.json"), ("standards", "s.yaml")):
        (root / top).mkdir(parents=True, exist_ok=True)
        (root / top / name).write_text("original\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("", encoding="utf-8")
    return root


def apply_solution(design_folder, task_id):
    for key, value, kind in SOLUTIONS[task_id]:
        r = call("design.set", path=str(design_folder), key=key, value=value, why="known-good solution", kind=kind)
        assert r.ok, r.messages


def test_task_files_are_valid():
    assert bench.task_ids(REPO) == sorted(TASKS)
    ops = registry()
    for tid in TASKS:
        t = bench.load_task(REPO, tid)
        assert t["allowed"] == ["plane *"]
        assert (REPO / t["start_design"] / "plane.yaml").is_file()
        assert t["grader"] and all(r["op"] in ops and r["expect"] and r["path"] for r in t["grader"])
        assert "{design}" not in t["prompt"] and Path(t["start_design"]).name in t["prompt"]
    status = yaml.safe_load((REPO / "designs" / "concept-a" / "plane.yaml").read_text(encoding="utf-8"))["status"]
    assert status != "retired"


def test_pick_selector():
    data = {"tiers": [{"tier": 1, "status": "PASS", "results": [{"check_id": "T1.a", "status": "PASS"}]},
                      {"tier": 3, "status": "FAIL",
                       "results": [{"check_id": "T3.static_margin", "status": "FAIL", "data": {"static_margin": 0.168}}]}],
            "value": [-25, 25]}
    assert bench.pick(data, "tiers[tier=3].results[check_id=T3.static_margin].data.static_margin") == 0.168
    assert bench.pick(data, "tiers[tier=1].status") == "PASS"
    assert bench.pick(data, "value[0]") == -25
    for bad in ("tiers[tier=9].status", "nope", "value[5]", "tiers[tier=1].results[check_id=X]"):
        with pytest.raises((KeyError, IndexError, ValueError)):
            bench.pick(data, bad)


@pytest.mark.parametrize("task_id", TASK_PARAMS)
def test_grader_passes_on_known_good_solution(task_id, fake_repo, tmp_path):
    task = bench.load_task(fake_repo, task_id)
    ws = bench.prepare_workspace(task, tmp_path / "ws", fake_repo)
    apply_solution(bench.design_dir(ws, task), task_id)
    r = bench.grade(task, ws, fake_repo)
    assert r["passed"] is True, r
    assert r["score"] == 1.0


@pytest.mark.parametrize("task_id", TASK_PARAMS)
def test_grader_fails_on_start_design(task_id, fake_repo, tmp_path):
    task = bench.load_task(fake_repo, task_id)
    ws = bench.prepare_workspace(task, tmp_path / "ws", fake_repo)
    r = bench.grade(task, ws, fake_repo)
    assert r["passed"] is False and r["score"] < 1.0, r


def test_grader_fails_if_core_changed(fake_repo, tmp_path):
    task = bench.load_task(fake_repo, "add-working-flap")
    ws = bench.prepare_workspace(task, tmp_path / "ws", fake_repo)
    apply_solution(bench.design_dir(ws, task), "add-working-flap")
    assert bench.grade(task, ws, fake_repo)["passed"] is True            # control: the solution passes
    dummy = fake_repo / "core" / "hangar" / "dummy.py"
    dummy.write_text("edited\n", encoding="utf-8")                       # the agent "changed core"
    r = bench.grade(task, ws, fake_repo)
    assert r["passed"] is False and r["score"] == 0.0
    assert any("core" in m for m in r["messages"])
    dummy.write_text("original\n", encoding="utf-8")
    assert bench.grade(task, ws, fake_repo)["passed"] is True            # restored: passes again
    (ws / "standards").mkdir()                                           # a standards/ folder appears in the workspace
    r = bench.grade(task, ws, fake_repo)
    assert r["passed"] is False and any("standards" in m for m in r["messages"])


def _fake_claude(monkeypatch, seen, model_key):
    def fake_run(cmd, **kw):
        seen["cmd"], seen["kw"] = cmd, kw
        out = {"is_error": False, "result": "done", "total_cost_usd": 0.01,
               "modelUsage": {model_key: {"inputTokens": 10, "outputTokens": 5,
                                          "cacheReadInputTokens": 100, "cacheCreationInputTokens": 1000}}}
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(out), stderr="")
    monkeypatch.setattr(bench.subprocess, "run", fake_run)
    monkeypatch.setattr(bench.shutil, "which", lambda name, path=None: f"/fake/{name}")


def test_run_command_line_and_capture(fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    seen = {}
    _fake_claude(monkeypatch, seen, "claude-haiku-5-5")
    r = call("bench.run", task="add-working-flap", agent="design-engineer", model="haiku")
    assert r.ok, r.messages
    assert r.data["tokens"] == 1115 and r.data["passed"] is False and r.data["score"] < 1.0
    assert isinstance(r.data["minutes"], float)
    cmd = seen["cmd"]
    assert cmd[0] == "/fake/claude" and cmd[1] == "-p"
    assert cmd[cmd.index("--agent") + 1] == "design-engineer" and cmd[cmd.index("--model") + 1] == "haiku"
    assert cmd[cmd.index("--allowedTools") + 1] == "Bash(plane *),Read,Grep,Glob"
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    for flag in ("--output-format", "--max-budget-usd", "--no-session-persistence"):
        assert flag in cmd
    assert "designs/flap-start" in seen["kw"]["input"]
    assert Path(seen["kw"]["cwd"]).resolve().parent == (fake_repo / ".sweeps" / "bench").resolve()
    record = fake_repo / "bench" / "results" / "runs" / f"{r.data['run_id']}.json"
    assert json.loads(record.read_text(encoding="utf-8"))["tokens"] == 1115


def test_run_rejects_wrong_model(fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    _fake_claude(monkeypatch, {}, "claude-sonnet-5-5")
    r = call("bench.run", task="add-working-flap", agent="design-engineer", model="haiku")
    assert r.ok is False and any("model mismatch" in m for m in r.messages)
    assert not (fake_repo / "bench" / "results" / "runs").exists()


def test_report_table(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    runs = tmp_path / "bench" / "results" / "runs"
    runs.mkdir(parents=True)
    for model, passed, score, tokens, minutes in (("opus", True, 1.0, 5000, 3.5), ("haiku", False, 0.0, 9000, 7.25)):
        rec = {"task": "mass-cut-10", "agent": "design-engineer", "model": model, "passed": passed, "score": score,
               "tokens": tokens, "minutes": minutes, "date": "2026-11-28"}
        (runs / f"mass-cut-10-{model}.json").write_text(json.dumps(rec), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    r = call("bench.report")
    assert r.ok
    table = [ln for ln in r.data["markdown"].splitlines() if ln.startswith("|")]
    assert table[0] == "| task | agent | model | passed | score | tokens | minutes | date |"
    assert table[1] == "|---|---|---|---|---|---|---|---|"
    assert table[2] == "| mass-cut-10 | design-engineer | haiku | no | 0.0 | 9000 | 7.25 | 2026-11-28 |"
    assert table[3] == "| mass-cut-10 | design-engineer | opus | yes | 1.0 | 5000 | 3.5 | 2026-11-28 |"


def test_list_op(monkeypatch):
    monkeypatch.chdir(REPO)
    r = call("bench.list")
    assert r.ok and [t["id"] for t in r.data["tasks"]] == sorted(TASKS)
