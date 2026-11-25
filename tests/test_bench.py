from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
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
    shutil.copytree(REPO / "tests" / "fixtures" / "concept-a-frozen", root / "designs" / "concept-a", ignore=shutil.ignore_patterns("fea"))
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
    cwd = Path(seen["kw"]["cwd"]).resolve()
    assert fake_repo.resolve() not in cwd.parents and cwd != fake_repo.resolve()  # workspace is outside the repo tree
    record = fake_repo / "bench" / "results" / "runs" / f"{r.data['run_id']}.json"
    assert json.loads(record.read_text(encoding="utf-8"))["tokens"] == 1115


def test_every_bench_write_text_call_passes_newline_lf():  # T54: no CRLF in files bench.py writes on Windows
    import ast
    tree = ast.parse(Path(bench.__file__).read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "write_text"]
    assert len(calls) == 4
    for c in calls:
        kw = {k.arg: k.value for k in c.keywords}
        assert isinstance(kw.get("newline"), ast.Constant) and kw["newline"].value == "\n", f"line {c.lineno}"


def test_run_rejects_wrong_model(fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    _fake_claude(monkeypatch, {}, "claude-sonnet-5-5")
    r = call("bench.run", task="add-working-flap", agent="design-engineer", model="haiku")
    assert r.ok is False and any("model mismatch" in m for m in r.messages)
    assert not (fake_repo / "bench" / "results" / "runs").exists()


@pytest.mark.parametrize("key,bad", [("agent", "../../planted"), ("agent", "design-engineer\n"), ("agent", "a/b"),
                                      ("task", "../tasks/add-working-flap"), ("task", "add-working-flap\n")])
def test_run_rejects_non_id_agent_and_task(key, bad, fake_repo, monkeypatch):  # T89: exit 2 inside the op, before any file is read
    monkeypatch.chdir(fake_repo)
    seen = {}
    _fake_claude(monkeypatch, seen, "claude-haiku-5-5")
    shutil.copy(fake_repo / ".claude" / "agents" / "design-engineer.md", fake_repo / "planted.md")  # what '../../planted' would reach
    args = {"task": "add-working-flap", "agent": "design-engineer", "model": "haiku", key: bad}
    r = call("bench.run", **args)
    assert r.exit_code == 2 and r.data["error"] == "input" and "bare id" in " ".join(r.messages), r.messages
    assert "cmd" not in seen and not (fake_repo / "bench" / "results" / "runs").exists()


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


# ---- T54 (D56): the grader replays the run's logged plane commands and fails a designs/ that differs ----
REAL_RUN = subprocess.run     # the fakes above replace subprocess.run; the tests below that need a real plane use this
MASS_CUT = ["design", "set", "designs/concept-a", "components[pwr-001].mass_g", "--value", "140", "--why", "smaller pack", "--kind", "modify"]


def _plane(cwd, env, *args):
    r = REAL_RUN([sys.executable, "-m", "hangar.cli", *args], cwd=str(cwd), env=env, capture_output=True, text=True,
                 encoding="utf-8", timeout=300)
    assert r.returncode == 0, r.stderr


def _logged_env(log):
    return {**os.environ, "PLANE_BENCH_LOG": str(log)}


def _bench_ws(fake_repo, tmp_path):
    task = bench.load_task(fake_repo, "mass-cut-10")
    ws = bench.prepare_workspace(task, tmp_path / "ws", fake_repo)
    return task, ws, bench.snapshot_design(task, ws), tmp_path / "plane-commands.jsonl"


def test_main_logs_argv_and_cwd_only_when_bench_log_is_set(tmp_path, monkeypatch):
    from hangar import cli as cli_mod
    monkeypatch.setattr(sys, "argv", ["plane", "--version"])
    log = tmp_path / "log.jsonl"
    monkeypatch.delenv("PLANE_BENCH_LOG", raising=False)
    with pytest.raises(SystemExit):
        cli_mod.main()
    assert not log.exists()
    monkeypatch.setenv("PLANE_BENCH_LOG", str(log))
    monkeypatch.chdir(tmp_path)
    for _ in range(2):
        with pytest.raises(SystemExit):
            cli_mod.main()
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert rows == [{"argv": ["--version"], "cwd": str(tmp_path)}] * 2
    assert b"\r" not in log.read_bytes()


def test_replay_kind_skips_read_only_replays_the_allow_list_and_refuses_the_rest():
    for argv in (["design", "mass", "designs/x"], ["design", "get", "designs/x", "--key", "id"], ["validate", "designs/x"],
                 ["mass", "designs/x"], ["list"], ["--version"], [], ["design"], ["design", "bogus"], ["fea", "plan", "designs/x"],
                 ["--help"], ["validate", "designs/x", "--tier", "3"]):
        assert bench.replay_kind(argv) == "skip", argv
    for argv in (["design", "set", "designs/x", "k", "--value", "1", "--why", "w"], ["design", "copy", "designs/x", "y"],
                 ["design", "new", "y"], ["new", "y"]):
        assert bench.replay_kind(argv) == "replay", argv
    for argv in (["bench", "run", "--task", "t", "--agent", "a", "--model", "haiku"], ["fea", "run", "designs/x"], ["fea", "designs/x", "--all"],
                 ["design", "export", "designs/x", "--format", "stl", "--out", "/tmp/o"], ["ledger", "set", "T1"], ["import", "dbf"],
                 ["baseline", "update", "designs/x"], ["studio"], ["no-such-command", "x"],
                 ["--", "design", "export", "designs/x", "--out", "f"], ["design", "--", "export", "designs/x", "--out", "f"],
                 ["--foo", "design", "set", "designs/x", "k", "--value", "1", "--why", "w"], ["--", "design", "mass", "designs/x"],
                 ["design", "--", "mass", "designs/x"], ["--version", "design", "export", "designs/x"],
                 ["validate", "designs/x", "--out", "f"], ["validate", "designs/x", "--out=f"]):
        assert bench.replay_kind(argv) == "refuse", argv


def test_designs_diff_ignores_changelog_dates_and_nothing_else(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for d, date in ((a, "2026-01-01T00:00:00Z"), (b, "2026-02-02T00:00:00Z")):
        (d / "x").mkdir(parents=True)
        (d / "x" / "plane.yaml").write_bytes(b"id: x\n")
        (d / "x" / "CHANGELOG.yaml").write_bytes(f"- date: '{date}'\n  key: k\n  why: w\n".encode())
        (d / "x" / "fea").mkdir()
        (d / "x" / "fea" / "r.json").write_bytes(d.name.encode())     # fea/ is not compared
    assert bench.designs_diff(a, b) == []
    (b / "x" / "CHANGELOG.yaml").write_bytes(b"- date: '2026-02-02T00:00:00Z'\n  key: k\n  why: other\n")
    assert bench.designs_diff(a, b) == ["x/CHANGELOG.yaml"]
    (b / "x" / "plane.yaml").write_bytes(b"id: x \n")
    (b / "x" / "extra.txt").write_bytes(b"")
    assert bench.designs_diff(a, b) == ["x/CHANGELOG.yaml", "x/extra.txt", "x/plane.yaml"]


def test_grade_replay_passes_when_only_plane_changed_the_design(fake_repo, tmp_path):
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    _plane(ws, _logged_env(log), "design", "mass", "designs/concept-a")      # read-only: logged, not replayed
    _plane(ws, _logged_env(log), *MASS_CUT)
    assert len(log.read_text(encoding="utf-8").splitlines()) == 2
    g = bench.grade(task, ws, fake_repo, snap, log)
    assert g["passed"] is True and g["score"] == 1.0 and g["messages"] == [], g
    assert bench.replay(ws, snap, log) == []                                    # deterministic: a second replay gives the same answer
    assert bench.grade(task, ws, fake_repo)["passed"] is True                    # without snapshot and log nothing is replayed


def test_grade_replay_fails_a_direct_edit_after_a_plane_command(fake_repo, tmp_path):
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    _plane(ws, _logged_env(log), *MASS_CUT)
    p = bench.design_dir(ws, task) / "plane.yaml"
    assert b"mass_g: 140" in p.read_bytes()
    p.write_bytes(p.read_bytes().replace(b"mass_g: 140", b"mass_g: 139"))        # the rows still pass; the replay does not match
    assert bench.grade(task, ws, fake_repo)["passed"] is True
    g = bench.grade(task, ws, fake_repo, snap, log)
    assert g["passed"] is False and g["score"] == 0.0, g
    assert any("differs from a replay" in m and "concept-a/plane.yaml" in m for m in g["messages"]), g["messages"]


def test_grade_replay_fails_a_direct_edit_with_no_plane_command_at_all(fake_repo, tmp_path):
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)           # the log file does not exist: the agent ran no plane command
    p = bench.design_dir(ws, task) / "plane.yaml"
    text = p.read_text(encoding="utf-8")
    assert "pwr-001" in text
    p.write_bytes(text.replace("# ", "#  ", 1).encode("utf-8"))
    g = bench.grade(task, ws, fake_repo, snap, log)
    assert g["passed"] is False and g["score"] == 0.0 and any("differs from a replay" in m for m in g["messages"]), g


def test_grade_replay_fails_when_the_log_is_unreadable(fake_repo, tmp_path):
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    log.write_bytes(b"not json\n")
    g = bench.grade(task, ws, fake_repo, snap, log)
    assert g["passed"] is False and g["score"] == 0.0 and any("log is unreadable" in m for m in g["messages"]), g


def _agent_fake(monkeypatch, seen, direct_edit):
    """A fake `claude`: runs the known-good plane command with the env bench.run built (so the command is logged), optionally edits plane.yaml by hand."""
    def fake_run(cmd, **kw):
        if cmd[0] != "/fake/claude":
            return REAL_RUN(cmd, **kw)
        seen["env"], seen["cwd"] = kw["env"], Path(kw["cwd"])
        _plane(kw["cwd"], kw["env"], *MASS_CUT)
        if direct_edit:
            p = Path(kw["cwd"]) / "designs" / "concept-a" / "plane.yaml"
            p.write_bytes(p.read_bytes().replace(b"mass_g: 140", b"mass_g: 139"))
        out = {"is_error": False, "result": "done", "total_cost_usd": 0.01,
               "modelUsage": {"claude-haiku-5-5": {"inputTokens": 1, "outputTokens": 1, "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0}}}
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(out), stderr="")
    monkeypatch.setattr(bench.subprocess, "run", fake_run)
    monkeypatch.setattr(bench.shutil, "which", lambda name, path=None: f"/fake/{name}")


@pytest.mark.parametrize("direct_edit", [False, True])
def test_run_replays_the_agent_commands_and_fails_a_direct_edit(direct_edit, fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    seen = {}
    _agent_fake(monkeypatch, seen, direct_edit)
    r = call("bench.run", task="mass-cut-10", agent="design-engineer", model="haiku")
    assert r.ok, r.messages
    log = Path(seen["env"]["PLANE_BENCH_LOG"])
    assert log.parent == seen["cwd"].parent and seen["cwd"] not in log.parents       # the log is outside the workspace
    assert len(log.read_text(encoding="utf-8").splitlines()) == 1
    record = json.loads((fake_repo / "bench" / "results" / "runs" / f"{r.data['run_id']}.json").read_text(encoding="utf-8"))
    if direct_edit:
        assert r.data["passed"] is False and r.data["score"] == 0.0
        assert any("differs from a replay" in m for m in record["messages"]), record["messages"]
    else:
        assert r.data["passed"] is True and r.data["score"] == 1.0 and record["messages"] == []


# ---- U6.1 (T91, T92, T93): designs dir in the workspace, pinned snapshot, replay allow-list, path mapping, unwritable log ----
def _log_rows(log, *rows):
    log.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")


def test_design_dir_env_redirects_designs_dir_only_when_set(tmp_path):
    code = "from hangar.design import DESIGNS_DIR, REPO_ROOT; print(DESIGNS_DIR == REPO_ROOT / 'designs', DESIGNS_DIR)"
    plain = {k: v for k, v in os.environ.items() if k != "PLANE_DESIGNS_DIR"}
    r = REAL_RUN([sys.executable, "-c", code], env=plain, capture_output=True, text=True, timeout=120)
    assert r.stdout.split()[0] == "True", r
    r = REAL_RUN([sys.executable, "-c", code], env={**plain, "PLANE_DESIGNS_DIR": str(tmp_path)}, capture_output=True, text=True, timeout=120)
    assert r.stdout.split()[0] == "False" and Path(r.stdout.split(" ", 1)[1].strip()) == tmp_path, r


def test_design_new_in_a_bench_run_and_its_replay_stay_inside_the_workspace(fake_repo, tmp_path):
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    real = REPO / "designs" / "u48-bench-new"
    env = {**_logged_env(log), "PLANE_DESIGNS_DIR": str(ws / "designs")}
    try:
        _plane(ws, env, "design", "new", "u48-bench-new", "--template", "concept-a")
        assert (ws / "designs" / "u48-bench-new" / "plane.yaml").is_file()
        assert not real.exists()
        g = bench.grade(task, ws, fake_repo, snap, log, bench.tree_digest(snap))
        assert g["messages"] == [], g                  # the replay reproduced the new design (the mass row itself still fails: nothing was cut)
        assert not real.exists()
        assert (ws.parent / "replay" / "designs" / "u48-bench-new" / "plane.yaml").is_file()
    finally:
        if real.exists():
            shutil.rmtree(real)


def test_tree_digest_changes_with_any_file_change(tmp_path):
    (tmp_path / "d" / "x").mkdir(parents=True)
    (tmp_path / "d" / "x" / "plane.yaml").write_bytes(b"id: x\n")
    d0 = bench.tree_digest(tmp_path / "d")
    assert bench.tree_digest(tmp_path / "d") == d0
    (tmp_path / "d" / "x" / "plane.yaml").write_bytes(b"id: y\n")
    d1 = bench.tree_digest(tmp_path / "d")
    (tmp_path / "d" / "extra").write_bytes(b"")
    assert len({d0, d1, bench.tree_digest(tmp_path / "d")}) == 3


def test_tree_digest_docstring_names_the_empty_folder_gap():  # T101
    assert "empty folder" in bench.tree_digest.__doc__


@pytest.mark.parametrize("row", [
    {"argv": "design set x", "cwd": "C:/x"},                      # argv must be a list
    {"argv": ["design", 1], "cwd": "C:/x"},                       # every word a string
    {"argv": ["design"], "cwd": 5},                               # cwd a string
    {"argv": ["design"]},                                         # both keys
    {"argv": ["design"], "cwd": "C:/x", "extra": 1},              # no other key
])
def test_replay_refuses_a_log_line_that_cli_would_not_write(row, fake_repo, tmp_path, monkeypatch):  # T101: PLANE_BENCH_LOG content check
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    monkeypatch.setattr(bench.subprocess, "run", lambda *a, **k: pytest.fail("a command was started"))
    _log_rows(log, row)
    assert bench.replay(ws, snap, log) == ["the plane command log is unreadable; cannot replay"]


def test_replay_refuses_a_log_inside_the_workspace(fake_repo, tmp_path):  # T101: PLANE_BENCH_LOG location check
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    inside = ws / "plane-commands.jsonl"
    inside.write_bytes(b"")
    assert bench.replay(ws, snap, inside) == ["the plane command log is inside the workspace; cannot replay"]
    assert bench.replay(ws, snap, log) == []


def test_replay_fails_when_the_snapshot_changed_during_the_run(fake_repo, tmp_path):
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    digest = bench.tree_digest(snap)
    assert bench.replay(ws, snap, log, digest) == []
    p = snap / "designs" / "concept-a" / "plane.yaml"
    p.write_bytes(p.read_bytes() + b"# tampered\n")
    assert bench.replay(ws, snap, log, digest) == ["the pre-run snapshot changed during the run; cannot replay"]
    g = bench.grade(task, ws, fake_repo, snap, log, digest)
    assert g["passed"] is False and g["score"] == 0.0 and any("snapshot changed" in m for m in g["messages"]), g


def test_replay_refuses_a_command_off_the_allow_list_and_runs_nothing(fake_repo, tmp_path, monkeypatch):
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    _log_rows(log, {"argv": ["design", "set", "designs/concept-a", "status", "--value", "x", "--why", "w"], "cwd": str(ws)},
              {"argv": ["bench", "run", "--task", "mass-cut-10", "--agent", "design-engineer", "--model", "haiku"], "cwd": str(ws)})
    def boom(*a, **k):
        raise AssertionError("a command was started")
    monkeypatch.setattr(bench.subprocess, "run", boom)
    msgs = bench.replay(ws, snap, log)
    assert len(msgs) == 1 and "bench run" in msgs[0] and "not a command a bench run may use" in msgs[0], msgs


def test_replay_refuses_a_path_outside_the_workspace_and_runs_nothing(fake_repo, tmp_path, monkeypatch):
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    def boom(*a, **k):
        raise AssertionError("a command was started")
    monkeypatch.setattr(bench.subprocess, "run", boom)
    for target in (str(snap / "designs" / "concept-a"), "../snapshot/designs/concept-a", str(fake_repo / "designs" / "concept-a")):
        _log_rows(log, {"argv": ["design", "set", target, "status", "--value", "x", "--why", "w"], "cwd": str(ws)})
        msgs = bench.replay(ws, snap, log)
        assert len(msgs) == 1 and "outside the workspace" in msgs[0], (target, msgs)
    _log_rows(log, {"argv": ["design", "set", "designs/concept-a", "status", "--value", "x", "--why", "w"], "cwd": str(tmp_path)})
    msgs = bench.replay(ws, snap, log)
    assert len(msgs) == 1 and "outside the workspace" in msgs[0], msgs


def test_map_args_maps_only_the_declared_path_arguments(fake_repo, tmp_path):  # T101
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    fresh = ws.parent / "replay"
    cwd = str(ws / "designs")                     # here "concept-a" and "." both name existing paths
    key = "components[pwr-001].mass_g"
    mapped = str(fresh / "designs" / "concept-a")
    assert bench._map_args(["design", "set", "concept-a", key, "--value", ".", "--why", "concept-a", "--kind", "modify"], cwd, ws, fresh) \
        == ["design", "set", mapped, key, "--value", ".", "--why", "concept-a", "--kind", "modify"]
    assert bench._map_args(["design", "set", "--why=concept-a", "--value", "..", "concept-a", key], cwd, ws, fresh) \
        == ["design", "set", "--why=concept-a", "--value", "..", mapped, key]
    assert bench._map_args(["design", "copy", "concept-a", "concept-a"], cwd, ws, fresh) \
        == ["design", "copy", mapped, "concept-a"]                      # SRC is mapped, NEW_ID is not
    assert bench._map_args(["design", "new", "concept-a", "--template", "concept-a"], cwd, ws, fresh) \
        == ["design", "new", "concept-a", "--template", "concept-a"]    # no path argument at all
    assert bench._map_args(["new", "concept-a"], cwd, ws, fresh) == ["new", "concept-a"]    # the old command names no op
    with pytest.raises(ValueError, match="outside the workspace"):      # a path argument outside the workspace is still refused
        bench._map_args(["design", "set", str(snap / "designs" / "concept-a"), key], cwd, ws, fresh)
    kept = bench._map_args(["design", "set", "concept-a", key, "--value", str(snap), "--why", "x"], cwd, ws, fresh)
    assert kept[5] == str(snap) and kept[7] == "x"      # --value and --why stay unmapped (as logged), even an absolute path outside the workspace


def test_replay_runs_a_command_whose_why_text_names_an_existing_path(fake_repo, tmp_path):  # T101
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    _plane(ws / "designs", _logged_env(log), "design", "set", "concept-a", "components[pwr-001].mass_g",
           "--value", "140", "--why", "concept-a", "--kind", "modify")
    assert bench.replay(ws, snap, log) == []                            # the why text stayed "concept-a" in the replay


def _plane_result(cwd, env, *args):
    return REAL_RUN([sys.executable, "-m", "hangar.cli", *args], cwd=str(cwd), env=env, capture_output=True, text=True,
                    encoding="utf-8", timeout=300)


@pytest.mark.parametrize("cmd", [
    ["design", "new", "u-tpl-new", "--template", "{abs}"],            # absolute path
    ["design", "new", "u-tpl-new", "--template", "../designs/concept-a"],   # ../ form
    ["design", "new", "u-tpl-new", "--template={abs}"],               # one-word form
    ["new", "u-tpl-new", "--from", "{abs}"],                          # legacy command
])
def test_design_new_refuses_a_template_that_is_not_a_bare_id(cmd, fake_repo, tmp_path):  # T101 (W16-R)
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    env = {**_logged_env(log), "PLANE_DESIGNS_DIR": str(ws / "designs")}
    args = [a.replace("{abs}", str(ws / "designs" / "concept-a")) for a in cmd]
    r = _plane_result(ws, env, *args)
    assert r.returncode == 2, (r.returncode, r.stderr)
    assert "template must be a bare design id" in r.stderr, r.stderr
    assert not (ws / "designs" / "u-tpl-new").exists()


def test_design_new_accepts_a_bare_template_id(fake_repo, tmp_path):  # T101 (W16-R)
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    env = {**_logged_env(log), "PLANE_DESIGNS_DIR": str(ws / "designs")}
    _plane(ws, env, "design", "new", "u-tpl-new", "--template", "concept-a")
    assert (ws / "designs" / "u-tpl-new" / "plane.yaml").is_file()


def test_replay_maps_a_workspace_path_written_as_dot_dot_run_id(fake_repo, tmp_path):
    task, ws, snap, log = _bench_ws(fake_repo, tmp_path)
    _plane(ws, _logged_env(log), "design", "set", f"../{ws.name}/designs/concept-a", "components[pwr-001].mass_g",
           "--value", "140", "--why", "smaller pack")
    before = bench.tree_digest(ws / "designs")
    assert bench.replay(ws, snap, log) == []
    assert bench.tree_digest(ws / "designs") == before                 # the replay wrote into replay/, not into the graded workspace
    assert b"mass_g: 140" in (ws.parent / "replay" / "designs" / "concept-a" / "plane.yaml").read_bytes()


def test_main_unwritable_bench_log_is_one_line_and_exit_2(tmp_path, monkeypatch, capsys):
    from hangar import cli as cli_mod
    monkeypatch.setattr(sys, "argv", ["plane", "--version"])
    monkeypatch.setenv("PLANE_BENCH_LOG", str(tmp_path))               # a folder: cannot be opened for append
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    err = capsys.readouterr().err
    assert e.value.code == 2 and err.startswith("plane: cannot write PLANE_BENCH_LOG") and "Traceback" not in err and err.count("\n") == 1, err


def test_run_points_designs_dir_at_the_workspace(fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    seen = {}
    _agent_fake(monkeypatch, seen, False)
    r = call("bench.run", task="mass-cut-10", agent="design-engineer", model="haiku")
    assert r.ok and r.data["passed"] is True, r.messages
    assert Path(seen["env"]["PLANE_DESIGNS_DIR"]) == seen["cwd"] / "designs"
