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

from . import op, call, registry, OpResult, OpInputError
from ..design import DESIGNS_DIR_ENV
from ..ids import ID_RE
from ._paths import repo_root, rel

PROTECTED = ("core", "schema", "standards")
REPLAY_TIMEOUT_S = 600
PATH_PARAM_NAMES = ("path", "src")    # T101: an op argument with one of these names (or of type Path) holds a design path; no other word is mapped
# T92: a logged command is replayed only when it is one of these (they write only below the design folders they are given,
# or, for design new, below DESIGNS_DIR, which the grader points into the workspace); read-only commands are skipped;
# any other command that can write (bench run, fea run, design export, ledger, update, import, baseline, ...) fails the run unexecuted.
REPLAY_ALLOW = (("design", "set"), ("design", "copy"), ("design", "new"), ("new",))
READ_ONLY_LEGACY = ("validate", "mass", "list")       # old top-level commands that only read
NOT_COMPARED = ("fea", ".sweeps", "__pycache__")      # the folders prepare_workspace does not copy; designs_diff skips them too
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
    (dest / "pyproject.toml").write_text("", encoding="utf-8", newline="\n")
    agents = dest / ".claude" / "agents"
    agents.mkdir(parents=True)
    shutil.copy(repo / ".claude" / "agents" / f"{agent}.md", agents / f"{agent}.md")
    (dest / ".bench-protected.json").write_text(json.dumps(fingerprint(repo)), encoding="utf-8", newline="\n")
    return dest


def snapshot_design(task: dict, ws) -> Path:
    """T54: copy the prepared workspace design (before the agent runs) to <ws parent>/snapshot/designs/<name>; return
    <ws parent>/snapshot. It lies next to the workspace, so a command could name it: T92 pins it with tree_digest
    (taken in memory right after this call, checked before the replay) and replay refuses any argument that names a path outside the workspace."""
    snap = Path(ws).parent / "snapshot"
    shutil.copytree(design_dir(ws, task), snap / "designs" / Path(task["start_design"]).name)
    return snap


def tree_digest(root) -> str:
    """T92: sha256 over every file below `root` (relative path and content), so any added, removed or changed file changes it.
    Folders are not hashed: an added empty folder goes undetected (harmless today: designs_diff compares files only too)."""
    root, h = Path(root), hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def replay_kind(argv: list[str]) -> Literal["skip", "replay", "refuse"]:
    """T92: "skip" for a command that cannot write (no words, an option such as --version, a group without a known verb,
    an op with mutates=False matched on its first two words, validate/mass/list); "replay" for REPLAY_ALLOW;
    "refuse" for everything else."""
    if not argv:
        return "skip"
    if argv[0].startswith("-"):      # click takes `plane -- design export ...` and `plane --foo design set ...`: only a lone --version/--help is read-only
        return "skip" if argv in (["--version"], ["--help"]) else "refuse"
    if argv[0] in READ_ONLY_LEGACY:
        return "refuse" if any(a == "--out" or a.startswith("--out=") for a in argv[1:]) else "skip"      # validate --out FILE writes FILE
    if any(argv[:len(a)] == list(a) for a in REPLAY_ALLOW):
        return "replay"
    if len(argv) > 1 and argv[1].startswith("-"):      # `plane design -- export ...`: an option or -- between group and verb is never read-only
        return "refuse"
    specs = registry().values()
    for spec in specs:
        if argv[:2] == [spec.group, spec.verb]:
            return "refuse" if spec.mutates else "skip"
    if any(argv[0] == spec.group for spec in specs):      # a registered group with a missing or unknown verb: click prints help or a usage error ...
        from ..cli import cli, _FallbackGroup
        return "refuse" if isinstance(cli.commands.get(argv[0]), _FallbackGroup) else "skip"      # ... except where the old command runs (plane fea PATH)
    return "refuse"


def _path_positions(argv: list[str]) -> set[int]:
    """T101: indices into argv of the words that are declared path arguments of the op the first two words name (an argument,
    not an option, whose name is in PATH_PARAM_NAMES or whose type is Path): `design set PATH`, `design copy SRC`. Option values
    (the word after --why, --value, ...) and the other arguments (KEY, NEW_ID) are never listed. A command that names no op gives an empty set."""
    spec = next((s for s in registry().values() if argv[:2] == [s.group, s.verb]), None)
    if spec is None:
        return set()
    options = {p.cli_name: p for p in spec.params if p.kind == "option"}
    arguments = [p for p in spec.params if p.kind == "argument"]
    found, n, i, only_words = set(), 0, 2, False
    while i < len(argv):
        a = argv[i]
        if not only_words and a == "--":
            only_words = True
        elif not only_words and a.startswith("-"):
            opt = options.get(a.lstrip("-").split("=", 1)[0])
            if "=" not in a and opt is not None and opt.type_name != "bool":
                i += 1                                   # the next word is this option's value
        else:
            if n < len(arguments) and (arguments[n].type_name == "path" or arguments[n].name in PATH_PARAM_NAMES):
                found.add(i)
            n += 1
        i += 1
    return found


def _map_args(argv: list[str], cwd: str, ws: Path, fresh: Path) -> list[str]:
    """T93/T92/T101: a declared path argument (see _path_positions) that names an existing path is resolved against the logged cwd;
    inside the workspace it becomes the same path inside `fresh` (short names, case and ../ forms included, because the comparison
    is on resolved paths); outside the workspace is a ValueError. Every other word (options, option values, KEY, NEW_ID) is kept as logged."""
    base, ws_r, out, positions = Path(cwd), ws.resolve(), [], _path_positions(argv)
    for i, a in enumerate(argv):
        if i not in positions or not a or a.startswith("-"):
            out.append(a)
            continue
        try:
            p = base / a
            found = p.exists()
            r = p.resolve() if found else None
        except (OSError, ValueError):
            found, r = False, None
        if not found:
            out.append(a)
            continue
        try:
            out.append(str(fresh / r.relative_to(ws_r)))
        except ValueError:
            raise ValueError(f"`plane {' '.join(argv)}` names a path outside the workspace: {a}") from None
    return out


def _files(root: Path) -> dict[str, Path]:
    out = {}
    for p in sorted(root.rglob("*")):
        parts = p.relative_to(root).parts
        if p.is_file() and not any(x in NOT_COMPARED for x in parts):
            out["/".join(parts)] = p
    return out


def _content(p: Path):
    data = p.read_bytes()
    if p.name == "CHANGELOG.yaml":         # design.set stamps each entry with the time it ran: compare the entries without their date
        try:
            rows = yaml.safe_load(data)
        except yaml.YAMLError:
            return data
        if isinstance(rows, list):
            return [{k: v for k, v in r.items() if k != "date"} if isinstance(r, dict) else r for r in rows]
    return data


def designs_diff(a, b) -> list[str]:
    """Sorted relative paths of files that exist on one side only or differ in content (CHANGELOG.yaml: ignoring each entry's date)."""
    fa, fb = _files(Path(a)), _files(Path(b))
    return sorted(n for n in set(fa) | set(fb) if n not in fa or n not in fb or _content(fa[n]) != _content(fb[n]))


def replay(ws, snapshot, log, digest=None) -> list[str]:
    """T54 (D56): run the logged plane commands that replay_kind says to replay on a fresh copy of `snapshot` and compare
    its designs/ with ws/designs. Returns [] when they match, else one message. Exit codes of the replayed commands are
    ignored: a command that failed for the agent fails the same way here. T92: with `digest` (tree_digest of the snapshot
    taken before the agent ran) a changed snapshot is a message; a command replay_kind refuses, or one that names a path
    outside the workspace, is a message and nothing is run."""
    ws, snapshot, log = Path(ws), Path(snapshot), Path(log)
    try:
        log.resolve().relative_to(ws.resolve())
        return ["the plane command log is inside the workspace; cannot replay"]      # T101: the log must lie outside what the agent can edit
    except ValueError:
        pass
    try:
        rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()] if log.is_file() else []
        if not all(isinstance(e, dict) and set(e) == {"argv", "cwd"} and isinstance(e["cwd"], str)
                   and isinstance(e["argv"], list) and all(isinstance(a, str) for a in e["argv"]) for e in rows):
            raise ValueError("log line is not {argv: [str], cwd: str}")      # T101: exactly what cli._log_invocation writes
        entries = [(list(e["argv"]), e["cwd"]) for e in rows]
    except (ValueError, KeyError, TypeError, OSError):
        return ["the plane command log is unreadable; cannot replay"]
    if digest is not None and tree_digest(snapshot) != digest:
        return ["the pre-run snapshot changed during the run; cannot replay"]
    from ..cli import BENCH_LOG_ENV
    fresh = ws.parent / "replay"
    todo = []
    for argv, cwd in entries:                       # check every command before running any
        kind = replay_kind(argv)
        if kind == "refuse":
            return [f"`plane {' '.join(argv)}` is not a command a bench run may use (allowed: read-only commands and "
                    + ", ".join(" ".join(a) for a in REPLAY_ALLOW) + "); not replayed"]
        if kind == "skip":
            continue
        try:
            where = fresh / Path(cwd).resolve().relative_to(ws.resolve())
        except ValueError:
            return [f"`plane {' '.join(argv)}` ran in {cwd}, outside the workspace; not replayed"]
        try:
            todo.append((_map_args(argv, cwd, ws, fresh), where))
        except ValueError as e:
            return [str(e)]
    if fresh.exists():
        shutil.rmtree(fresh)
    shutil.copytree(snapshot / "designs", fresh / "designs")
    (fresh / "pyproject.toml").write_bytes(b"")
    env = {k: v for k, v in os.environ.items() if k != BENCH_LOG_ENV}
    env[DESIGNS_DIR_ENV] = str(fresh / "designs")
    for argv, where in todo:
        try:
            subprocess.run([sys.executable, "-m", "hangar.cli", *argv], cwd=str(where if where.is_dir() else fresh), env=env,
                           capture_output=True, text=True, encoding="utf-8", timeout=REPLAY_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return [f"replay of `plane {' '.join(argv)}` timed out"]
    diff = designs_diff(ws / "designs", fresh / "designs")
    if diff:
        return ["designs/ differs from a replay of the logged plane commands: " + ", ".join(diff[:10]) + (" ..." if len(diff) > 10 else "")]
    return []


def grade(task: dict, ws, repo, snapshot=None, log=None, digest=None) -> dict:
    """Run every grader row through the ops. passed = every row ok and nothing protected changed
    (and, when `snapshot` and `log` are given, designs/ equals the replay of the logged plane commands on the snapshot);
    score = rows ok / rows, or 0.0 if anything protected changed or the replay differs."""
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
    if snapshot is not None:
        messages += replay(ws, snapshot, log, digest)
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
    for label, value in (("task", task), ("agent", agent)):   # T89: both name a file under the repo; only a bare id may
        if not ID_RE.fullmatch(value):
            raise OpInputError(f"{label} {value!r} must be a bare id matching {ID_RE.pattern}")
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
    from ..cli import BENCH_LOG_ENV
    snapshot, log = snapshot_design(t, ws), ws.parent / "plane-commands.jsonl"     # T54: both outside the workspace
    digest = tree_digest(snapshot)                                                   # T92: kept in memory, checked before the replay
    env = {**env, BENCH_LOG_ENV: str(log), DESIGNS_DIR_ENV: str(ws / "designs")}     # T91: design new/copy write into the workspace
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
        (logs / f"{run_id}.log").write_text(f"exit {proc.returncode}\n--- stdout\n{proc.stdout}\n--- stderr\n{proc.stderr}\n", encoding="utf-8", newline="\n")
        try:
            out = json.loads(proc.stdout)
        except ValueError:
            return OpResult(False, {"error": "internal"}, [f"claude gave no JSON (exit {proc.returncode}): {(proc.stderr or proc.stdout)[:500]}"])
        usage = out.get("modelUsage") or {}
        if not any(model in k.lower() for k in usage):
            return OpResult(False, {"error": "internal"}, [f"model mismatch: asked for {model}, claude used {sorted(usage) or 'nothing'}"])
        tokens, cost, final = _tokens(usage), float(out.get("total_cost_usd") or 0.0), str(out.get("result") or "")
    g = grade(t, ws, root, snapshot, log, digest)
    data = {"task": task, "agent": agent, "model": model, "passed": g["passed"], "score": g["score"], "tokens": tokens,
            "minutes": minutes, "cost_usd": cost, "timed_out": timed_out, "run_id": run_id, "workspace": str(ws)}
    record = root / "bench" / "results" / "runs" / f"{run_id}.json"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps({**data, "date": datetime.now().strftime("%Y-%m-%d"), "rows": g["rows"],
                                  "messages": g["messages"], "final_text": final[:2000]}, indent=2), encoding="utf-8", newline="\n")
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
