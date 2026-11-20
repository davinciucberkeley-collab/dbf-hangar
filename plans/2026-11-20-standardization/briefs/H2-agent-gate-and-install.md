# Brief H2: agent_gate hook, settings.json, quiet output style, installer

class: easy · role: builder (Haiku) · plan: §6c step H2 · R18, R19, R24

## Where
- Repo `/home/claude/dbf-hangar`. Work in worktree `/home/claude/wt/h2` on branch `std/h2-agent-gate`:
  `git -C /home/claude/dbf-hangar worktree add /home/claude/wt/h2 -b std/h2-agent-gate main`
- Python standard library only in `harness/`. Tests use pytest. Must run on Windows and Linux.

## Exact outputs
- `harness/hooks/agent_gate.py`
- `harness/install.py`
- `.claude/settings.json`
- `.claude/output-styles/quiet.md`
- `tests/harness/test_agent_gate_install.py`. **No `__init__.py` in `tests/` or `tests/harness/`** (it would shadow the `harness` package).

Do NOT create `harness/ledger.py`, `harness/hooks/{log_prompt,stop_gate,reinject}.py`, `harness/__init__.py`, `harness/hooks/__init__.py`, `pytest.ini`, `tests/harness/conftest.py` or `.gitignore` (brief H1 owns them). Your tests must not import them. Your tests run with `python -m pytest tests/harness/test_agent_gate_install.py -q --rootdir=.` and must not need `pytest.ini`.

## Exact behaviour

### `harness/hooks/agent_gate.py` (PreToolUse; stdin JSON has `tool_name`, `tool_input`)
- Root: env `CLAUDE_PROJECT_DIR`, else stdin `cwd`, else `Path(__file__).resolve().parents[2]`.
- If `tool_name` not in `("Task", "Agent")` → exit 0.
- `role = tool_input.get("subagent_type") or ""`.
- Roster = the `name:` value from the YAML frontmatter (between the first two `---` lines) of every `<root>/.claude/agents/*.md`. Parse with plain string handling (no PyYAML).
- If `role` not in roster → stderr, exit 2:
  `Agent "<role>" is not in the hangar roster. Use one of: <comma-separated sorted roster>. See .claude/agents/ and the plan's agent table. Builds go to builder (Haiku).`
- Active plan = newest `<root>/plans/*.md` by file name. If it exists and its text does not contain `` `<role>` `` (the role in backticks) → stderr, exit 2:
  `Agent "<role>" is not in the active plan's agent table (<plan relative path>). Add it to the table first.`
- If `role` in `("builder", "builder-plus")`: prompt = `tool_input.get("prompt", "")`. Builder-ready when it matches regex `plans/\S+/briefs/\S+\.md` OR contains both `pass check` and `stop rule` (case-insensitive). Otherwise stderr, exit 2:
  `Brief for <role> is not builder-ready: give a brief file (plans/<plan>/briefs/*.md) or include exact outputs, exact inputs, a pass check and a stop rule (standards/agents.md).`
- Otherwise exit 0. On any unexpected exception (including bad JSON on stdin): print it to stderr and exit 0.

### `.claude/settings.json` (exact content)
```json
{
  "outputStyle": "quiet",
  "hooks": {
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/harness/hooks/log_prompt.py\""}]}],
    "PreToolUse": [{"matcher": "Task|Agent", "hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/harness/hooks/agent_gate.py\""}]}],
    "SessionStart": [{"matcher": "startup|resume|clear|compact", "hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/harness/hooks/reinject.py\""}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/harness/hooks/stop_gate.py\""}]}]
  }
}
```

### `.claude/output-styles/quiet.md` (exact content)
```
---
name: quiet
description: Answers questions fully; otherwise reports only results, decisions needed and blockers. No step-by-step narration.
---

Work silently. Between tool calls, write nothing unless a draft is ready, the direction changes, a decision is needed from the user, or something is blocked.

When the user asks a question, answer it fully and directly.

When a task ends, report in at most five lines: what changed (with paths or links), what was verified and how, and what is still open. Do not recap the steps you took.
```

### `harness/install.py`
- `install(target: Path, source: Path | None = None) -> list[Path]` — `source` defaults to `Path(__file__).resolve().parents[1]` (the hangar repo). Copies into `target`:
  - every `source/.claude/agents/*.md` → `target/.claude/agents/`
  - `source/.claude/output-styles/quiet.md` → `target/.claude/output-styles/quiet.md`
  - every file under `source/harness/` except `__pycache__` folders → `target/harness/` (same relative paths)
  - merges `source/.claude/settings.json` into `target/.claude/settings.json`: load the target's file (or `{}`), set `outputStyle` only if the target has none; for each hook event, append each source matcher-entry whose command string is not already present anywhere under that event in the target. Write with `indent=2`.
  - Returns the list of files written (copied or merged), as absolute paths.
- Idempotent: running twice gives the same target files and no duplicate hook entries.
- CLI: `python harness/install.py --target PATH` → prints `Installed hangar harness into PATH (<n> files)`; exit 0. Missing `--target` → argparse error (exit 2).

## Exact tests (`tests/harness/test_agent_gate_install.py`; write first, see fail, then implement)

```python
import json, os, subprocess, sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "harness"))
import install as installer  # harness/install.py

ROLES = ["advisor","auditor","builder","builder-plus","conductor","design-engineer","recon","reviewer","scout","tactician"]

@pytest.fixture
def root(tmp_path):
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    for r in ROLES:
        (tmp_path / ".claude" / "agents" / f"{r}.md").write_text(f"---\nname: {r}\nmodel: haiku\n---\n# {r}\n", encoding="utf-8")
    (tmp_path / "plans").mkdir()
    (tmp_path / "plans" / "2026-11-20-x.md").write_text("| H1 | `builder` |\n| HR | `reviewer` |\n", encoding="utf-8")
    return tmp_path

def gate(event, root):
    return subprocess.run([sys.executable, str(REPO / "harness/hooks/agent_gate.py")], input=json.dumps(event),
                          capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))

def task(role, prompt="x"):
    return {"tool_name": "Task", "tool_input": {"subagent_type": role, "prompt": prompt}}

def test_unknown_role_blocked_with_roster(root):
    r = gate(task("general-purpose"), root)
    assert r.returncode == 2 and "builder" in r.stderr and "not in the hangar roster" in r.stderr

def test_roster_role_missing_from_plan_blocked(root):
    r = gate(task("recon"), root)
    assert r.returncode == 2 and "agent table" in r.stderr

def test_builder_needs_builder_ready_brief(root):
    assert gate(task("builder", "make it better"), root).returncode == 2
    assert gate(task("builder", "Follow plans/2026-11-20-x/briefs/H1-a.md"), root).returncode == 0
    assert gate(task("builder", "Pass check: pytest. Stop rule: report."), root).returncode == 0

def test_reviewer_in_plan_allowed(root):
    assert gate(task("reviewer", "review"), root).returncode == 0

def test_agent_tool_name_also_gated(root):
    assert gate({"tool_name": "Agent", "tool_input": {"subagent_type": "Explore"}}, root).returncode == 2

def test_other_tools_and_bad_input_pass(root):
    assert gate({"tool_name": "Bash", "tool_input": {"command": "ls"}}, root).returncode == 0
    r = subprocess.run([sys.executable, str(REPO / "harness/hooks/agent_gate.py")], input="not json",
                       capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
    assert r.returncode == 0

def test_settings_wire_all_four_hooks_and_quiet_style():
    s = json.loads((REPO / ".claude/settings.json").read_text())
    assert s["outputStyle"] == "quiet"
    assert set(s["hooks"]) == {"UserPromptSubmit", "PreToolUse", "SessionStart", "Stop"}
    assert (REPO / ".claude/output-styles/quiet.md").read_text().startswith("---\nname: quiet")

def test_install_is_idempotent_and_merges_settings(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/settings.json").write_text(json.dumps({"outputStyle": "mine", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo hi"}]}]}}))
    installer.install(tmp_path); installer.install(tmp_path)
    s = json.loads((tmp_path / ".claude/settings.json").read_text())
    assert s["outputStyle"] == "mine"
    stop_cmds = [h["command"] for e in s["hooks"]["Stop"] for h in e["hooks"]]
    assert stop_cmds.count("echo hi") == 1 and sum("stop_gate.py" in c for c in stop_cmds) == 1
    assert len(list((tmp_path / ".claude/agents").glob("*.md"))) == 10
    assert (tmp_path / "harness/hooks/agent_gate.py").exists()
```
The idempotency test copies from the real repo (`source` default), which has the 10 real agent files in `.claude/agents/`.

## Pass check
`cd /home/claude/wt/h2 && python -m pytest tests/harness/test_agent_gate_install.py -q --rootdir=.` → all 8 pass. Paste the last 3 lines.

## Commit
`git add -A && git commit -m "harness: agent gate (roster, plan table, builder-ready bar), settings, quiet style, installer"` with the attribution trailer lines your own session instructions specify (they name your model), for example:
```
Co-Authored-By: Claude <model> <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01QqEWVKLu3zpA2K1nz9MZxU
```
Do not push. Do not merge.

## Stop rule
If a test fails for a reason other than missing code, or anything here is ambiguous, stop and report the exact error and the line of this brief. After two failed attempts on the same failure, stop and report both.
