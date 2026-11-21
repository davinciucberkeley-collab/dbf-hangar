"""PlaneBench v0 (U3.3): graded design tasks for an agent that may only run `plane` commands."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml

from . import op, call, OpResult, OpInputError
from ._paths import repo_root, rel

PROTECTED = ("core", "schema", "standards")
MODEL_ORDER = {"haiku": 0, "sonnet": 1, "opus": 2}
TIMEOUT_S = 1200
BUDGET_USD = "4.00"
USAGE_KEYS = ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")
_SPLIT = re.compile(r"\.(?![^\[]*\])")
_SEG = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)((?:\[[^\[\]]+\])*)$")
_SEL = re.compile(r"\[([^\[\]]+)\]")


def task_ids(root) -> list[str]:
    return sorted(p.stem for p in (Path(root) / "bench" / "tasks").glob("*.yaml"))


def load_task(root, task_id: str) -> dict:
    p = Path(root) / "bench" / "tasks" / f"{task_id}.yaml"
    if not p.is_file():
        raise OpInputError(f"no such task: {task_id}; tasks: {', '.join(task_ids(root)) or 'none'}")
    t = yaml.safe_load(p.read_text(encoding="utf-8"))
    for k in ("id", "prompt", "start_design", "allowed", "grader"):
        if k not in t:
            raise OpInputError(f"{p.name}: missing {k}")
    if t["id"] != task_id:
        raise OpInputError(f"{p.name}: id {t['id']!r} does not match the file name")
    return t


def pick(data, path: str):
    """Read one value: dot-separated keys; a key may be followed by [n] (list index) or [field=value]
    (first list item whose field, as text, equals value). Raises KeyError, IndexError or ValueError."""
    node = data
    for seg in _SPLIT.split(path):
        m = _SEG.match(seg)
        if not m:
            raise ValueError(f"bad selector segment {seg!r}")
        if not isinstance(node, dict) or m.group(1) not in node:
            raise KeyError(m.group(1))
        node = node[m.group(1)]
        for sel in _SEL.findall(m.group(2)):
            if sel.isdigit():
                node = node[int(sel)]
            else:
                field, _, want = sel.partition("=")
                found = [x for x in node if isinstance(x, dict) and str(x.get(field)) == want]
                if not found:
                    raise KeyError(sel)
                node = found[0]
    return node


def _check(value, expect: dict):
    (kind, want), = expect.items()
    num = isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "eq":
        ok = value == want
    elif kind == "ne":
        ok = value != want
    elif kind == "le":
        ok = num and value <= want
    elif kind == "ge":
        ok = num and value >= want
    else:
        raise ValueError(f"unknown expect {kind!r}")
    return bool(ok), f"{value!r} {kind} {want!r}"


def _fill(v, design: str):
    if isinstance(v, str):
        return v.replace("{design}", design)
    if isinstance(v, dict):
        return {k: _fill(x, design) for k, x in v.items()}
    if isinstance(v, list):
        return [_fill(x, design) for x in v]
    return v


def fingerprint(repo) -> dict[str, str]:
    repo = Path(repo)
    out = {}
    for top in PROTECTED:
        for p in sorted((repo / top).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and not any(x.endswith(".egg-info") for x in p.parts):
                out[p.relative_to(repo).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def design_dir(ws, task: dict) -> Path:
    return Path(ws) / "designs" / Path(task["start_design"]).name


def prepare_workspace(task: dict, dest, repo, agent: str = "design-engineer") -> Path:
    """Scratch workspace: designs/<name> (a copy of start_design), an empty pyproject.toml (marks the repo root for
    the ops), .claude/agents/<agent>.md, and .bench-protected.json (fingerprint of core/, schema/, standards/)."""
    repo, dest = Path(repo), Path(dest)
    src = repo / task["start_design"]
    if not (src / "plane.yaml").is_file():
        raise OpInputError(f"start_design {task['start_design']}: no plane.yaml")
    if dest.exists():
        raise OpInputError(f"{dest} already exists")
    shutil.copytree(src, design_dir(dest, task), ignore=shutil.ignore_patterns("fea", ".sweeps", "__pycache__"))
    (dest / "pyproject.toml").write_text("", encoding="utf-8")
    agents = dest / ".claude" / "agents"
    agents.mkdir(parents=True)
    shutil.copy(repo / ".claude" / "agents" / f"{agent}.md", agents / f"{agent}.md")
    (dest / ".bench-protected.json").write_text(json.dumps(fingerprint(repo)), encoding="utf-8")
    return dest


def grade(task: dict, ws, repo) -> dict:
    """Run every grader row through the ops. passed = every row ok and nothing protected changed;
    score = rows ok / rows, or 0.0 if anything protected changed."""
    ws, repo = Path(ws), Path(repo)
    design = design_dir(ws, task).as_posix()
    rows, cache = [], {}
    for row in task["grader"]:
        label = row.get("label", row["op"])
        args = _fill(row.get("args", {}), design)
        key = (row["op"], json.dumps(args, sort_keys=True))
        try:
            if key not in cache:
                cache[key] = call(row["op"], **args)
            res = cache[key]
            if res.data.get("error"):
                rows.append({"label": label, "ok": False, "detail": "op error: " + "; ".join(res.messages)})
                continue
            ok, detail = _check(pick(res.data, row["path"]), row["expect"])
        except (KeyError, IndexError, TypeError, ValueError) as e:
            ok, detail = False, f"cannot read {row['path']}: {type(e).__name__} {e}"
        rows.append({"label": label, "ok": ok, "detail": detail})
    messages = []
    saved = json.loads((ws / ".bench-protected.json").read_text(encoding="utf-8"))
    if fingerprint(repo) != saved:
        messages.append("core, schema or standards changed during the run")
    for name in PROTECTED:
        if (ws / name).exists():
            messages.append(f"{name}/ exists in the workspace")
    n_ok = sum(1 for r in rows if r["ok"])
    passed = bool(rows) and n_ok == len(rows) and not messages
    score = round(n_ok / len(rows), 3) if rows and not messages else 0.0
    return {"passed": passed, "score": score, "rows": rows, "messages": messages}


def build_command(claude: str, task: dict, agent: str, model: str) -> list[str]:
    """The prompt is sent on stdin (no quoting problems on Windows); these are the flags."""
    allowed = ",".join([f"Bash({p})" for p in task["allowed"]] + ["Read", "Grep", "Glob"])
    return [claude, "-p", "--agent", agent, "--model", model, "--output-format", "json",
            "--permission-mode", "dontAsk", "--allowedTools", allowed,
            "--max-budget-usd", BUDGET_USD, "--no-session-persistence"]


def _tokens(model_usage: dict) -> int:
    return sum(int(u.get(k, 0)) for u in model_usage.values() for k in USAGE_KEYS)


@op(name="bench.list", summary="List the PlaneBench tasks (id, start design, number of grader rows).",
    render=lambda r: "\n".join(f"{t['id']}  {t['start_design']}  {t['grader_rows']} rows" for t in r.data["tasks"]) or "no tasks")
def list_op() -> OpResult:
    root = repo_root()
    tasks = []
    for tid in task_ids(root):
        t = load_task(root, tid)
        tasks.append({"id": tid, "start_design": t["start_design"], "grader_rows": len(t["grader"])})
    return OpResult(True, {"tasks": tasks})


@op(name="bench.run", summary="Run one PlaneBench task with a headless agent (claude -p) in a scratch copy of the design, then grade it.",
    mutates=True,
    render=lambda r: json.dumps({k: r.data[k] for k in ("task", "agent", "model", "passed", "score", "tokens", "minutes")}))
def run_op(task: str, agent: str, model: Literal["haiku", "sonnet", "opus"]) -> OpResult:
    root = repo_root()
    t = load_task(root, task)
    claude = shutil.which("claude")
    if claude is None:
        raise OpInputError("claude CLI not found on PATH")
    env = {**os.environ, "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")}
    if shutil.which("plane", path=env["PATH"]) is None:
        raise OpInputError("plane not found next to the python that runs this op")
    if not (root / ".claude" / "agents" / f"{agent}.md").is_file():
        raise OpInputError(f"no such agent: {agent}")
    run_id = f"{task}-{model}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    # Outside any git tree: the repo's .claude hooks must not load into the headless run.
    ws = prepare_workspace(t, Path(tempfile.mkdtemp(prefix="planebench-")) / run_id, root, agent)
    cmd = build_command(claude, t, agent, model)
    started = time.monotonic()
    proc, timed_out = None, False
    try:
        proc = subprocess.run(cmd, input=t["prompt"], cwd=str(ws), env=env, capture_output=True, text=True,
                              encoding="utf-8", timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        timed_out = True
    minutes = round((time.monotonic() - started) / 60, 2)
    tokens, cost, final = 0, 0.0, ""
    logs = root / ".logs" / "bench"
    logs.mkdir(parents=True, exist_ok=True)
    if proc is not None:
        (logs / f"{run_id}.log").write_text(f"exit {proc.returncode}\n--- stdout\n{proc.stdout}\n--- stderr\n{proc.stderr}\n", encoding="utf-8")
        try:
            out = json.loads(proc.stdout)
        except ValueError:
            return OpResult(False, {"error": "internal"}, [f"claude gave no JSON (exit {proc.returncode}): {(proc.stderr or proc.stdout)[:500]}"])
        usage = out.get("modelUsage") or {}
        if not any(model in k.lower() for k in usage):
            return OpResult(False, {"error": "internal"}, [f"model mismatch: asked for {model}, claude used {sorted(usage) or 'nothing'}"])
        tokens, cost, final = _tokens(usage), float(out.get("total_cost_usd") or 0.0), str(out.get("result") or "")
    g = grade(t, ws, root)
    data = {"task": task, "agent": agent, "model": model, "passed": g["passed"], "score": g["score"], "tokens": tokens,
            "minutes": minutes, "cost_usd": cost, "timed_out": timed_out, "run_id": run_id, "workspace": str(ws)}
    record = root / "bench" / "results" / "runs" / f"{run_id}.json"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps({**data, "date": datetime.now().strftime("%Y-%m-%d"), "rows": g["rows"],
                                  "messages": g["messages"], "final_text": final[:2000]}, indent=2), encoding="utf-8")
    return OpResult(True, data, changed_files=[rel(root, record)])


@op(name="bench.report", summary="Markdown table of every recorded PlaneBench run (bench/results/runs/*.json).",
    render=lambda r: r.data["markdown"])
def report_op() -> OpResult:
    runs_dir = repo_root() / "bench" / "results" / "runs"
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(runs_dir.glob("*.json"))] if runs_dir.is_dir() else []
    if not runs:
        return OpResult(True, {"runs": 0, "markdown": "no runs yet"})
    runs.sort(key=lambda r: (r["task"], MODEL_ORDER.get(r["model"], 9), r["date"]))
    lines = ["# PlaneBench v0 results", "",
             "| task | agent | model | passed | score | tokens | minutes | date |", "|---|---|---|---|---|---|---|---|"]
    for r in runs:
        lines.append(f"| {r['task']} | {r['agent']} | {r['model']} | {'yes' if r['passed'] else 'no'} | {r['score']} | "
                     f"{r['tokens']} | {r['minutes']} | {r['date']} |")
    return OpResult(True, {"runs": len(runs), "markdown": "\n".join(lines) + "\n"})
