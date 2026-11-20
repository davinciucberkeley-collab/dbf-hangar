# Brief H1: prompt ledger + log_prompt, stop_gate, reinject hooks

class: easy · role: builder (Haiku) · plan: §6c step H1 · R20, R21

## Where
- Repo `/home/claude/dbf-hangar`. Work in worktree `/home/claude/wt/h1` on branch `std/h1-ledger-hooks`:
  `git -C /home/claude/dbf-hangar worktree add /home/claude/wt/h1 -b std/h1-ledger-hooks main`
- Python standard library only in `harness/` (no third-party imports). Tests use pytest. Must run on Windows and Linux.

## Exact outputs
- `harness/__init__.py` (empty)
- `harness/ledger.py`
- `harness/hooks/__init__.py` (empty)
- `harness/hooks/log_prompt.py`, `harness/hooks/stop_gate.py`, `harness/hooks/reinject.py`
- `tests/harness/conftest.py`, `tests/harness/test_ledger_hooks.py`. **No `__init__.py` in `tests/` or `tests/harness/`** (fix 2026-11-20: a `tests/harness/__init__.py` shadows the `harness` package).
- `.gitignore` with these lines: `ledger/prompts.jsonl`, `ledger/events.jsonl`, `ledger/.stop_blocks.json`, `__pycache__/`, `.pytest_cache/`

Do NOT create or edit `.claude/settings.json`, `harness/hooks/agent_gate.py` or `harness/install.py` (brief H2 owns them).

## Exact behaviour

### `harness/ledger.py`
Data file `<root>/ledger/prompts.jsonl`, append-only, one JSON object per line. The latest line for an id wins.
- New prompt line: `{"id": "P<n>", "session": str, "ts": ISO-8601 UTC str, "text": str (first 2000 chars), "status": "open"}`
- Status line: `{"id": "P<n>", "ts": str, "status": "addressed" | "open", "evidence": str}`

Functions (all take `root: Path` first):
- `project_root(event: dict | None = None) -> Path` — env `CLAUDE_PROJECT_DIR` if set, else `event["cwd"]` if present, else `Path(__file__).resolve().parents[1]`.
- `add_prompt(root, session: str, text: str) -> str` — next id is `P<max existing number + 1>` (P1 when empty); creates `ledger/` if missing; returns the id.
- `set_status(root, item_id: str, status: str, evidence: str = "") -> None` — `status` must be `"open"` or `"addressed"`, else `ValueError`; `"addressed"` with empty/whitespace `evidence` → `ValueError("evidence")`; unknown id → `KeyError`.
- `prompts(root, session: str | None = None) -> list[dict]` — merged state per id (fields of the first line updated by later lines), sorted by id number; filtered by session when given.
- `open_prompts(root, session: str | None = None) -> list[dict]` — those with `status == "open"`.
- `log_event(root, event: dict) -> None` — append `event` + `ts` to `ledger/events.jsonl`.
- CLI (`python harness/ledger.py ...`, argparse):
  - `addressed <ID> --evidence TEXT` → set_status addressed; prints `P<n> addressed`
  - `reopen <ID>` → set_status open
  - `list [--open] [--session S]` → one line per prompt: `P3 [open] s=<first 8 chars of session> <first 80 chars of text>`
  Exit 0 on success, 2 on ValueError/KeyError (message on stderr).

### Hooks (each reads one JSON object from stdin; never raise: on any unexpected exception print it to stderr and exit 0, so a bug never blocks the user)
- `log_prompt.py` (UserPromptSubmit; stdin has `session_id`, `prompt`): if `prompt.strip()` is empty → exit 0 silently. Else `add_prompt` and print exactly one line to stdout:
  `Logged as P<n>. When done: python harness/ledger.py addressed P<n> --evidence "<what answered it>"`
  Exit 0.
- `stop_gate.py` (Stop; stdin has `session_id`, `stop_hook_active`):
  - env `HANGAR_ALLOW_STOP` == `"1"` → exit 0.
  - `open = open_prompts(root, session_id)`; none → reset this session's counter in `ledger/.stop_blocks.json` (a JSON object `{session_id: int}`) and exit 0.
  - otherwise increment the counter. If the counter is now > 3 → `log_event(root, {"event": "stop-forced", "session": session_id, "ids": [ids]})`, reset counter, exit 0.
  - else write to stderr, exit 2:
    ```
    Open prompts in this session: P2, P5
    - P2: <first 100 chars>
    - P5: <first 100 chars>
    Address each (python harness/ledger.py addressed <ID> --evidence "...") or say why it is not done. Override: HANGAR_ALLOW_STOP=1.
    ```
- `reinject.py` (SessionStart; stdin has `source`, `session_id`): prints to stdout, exit 0.
  - Always: `hangar: roles in .claude/agents/ (launch only these); plan: <relative path of newest plans/*.md by name>`
  - If `source` in `("compact", "resume")`: then `Open prompts:` and one line per open prompt (all sessions) as in `list`, or `Open prompts: none`; then `Unfinished units:` and one line per `### Unit ...` heading of the newest plan whose section (up to the next `### ` or `## ` heading) contains `- [ ]`, printed as the heading text without `### `.
  - If `source` is `"startup"` or `"clear"`: only the first line plus `Open prompts: <count>`.

## Exact tests (`tests/harness/test_ledger_hooks.py`; write these first, run, see them fail, then implement)

`conftest.py` provides:
```python
import json, os, subprocess, sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[2]

@pytest.fixture
def root(tmp_path):
    (tmp_path / "plans").mkdir()
    (tmp_path / "plans" / "2026-11-20-x.md").write_text(
        "# P\n## 7. Units\n### Unit U9.1: Done thing\n- [x] a\n### Unit U9.2: Open thing\n- [ ] b\n## 8. End\n", encoding="utf-8")
    return tmp_path

def run_hook(name, event, root, **env):
    e = dict(os.environ, CLAUDE_PROJECT_DIR=str(root), **env)
    return subprocess.run([sys.executable, str(REPO / "harness" / "hooks" / f"{name}.py")],
                          input=json.dumps(event), capture_output=True, text=True, env=e)
```

Tests (names and assertions exact):
```python
import os, subprocess, sys
import pytest
from conftest import REPO, run_hook   # fix 2026-11-20: helpers come from conftest
from harness import ledger

def test_ids_increment_and_state_merges(root):
    assert ledger.add_prompt(root, "s1", "a") == "P1"
    assert ledger.add_prompt(root, "s1", "b") == "P2"
    ledger.set_status(root, "P1", "addressed", evidence="commit abc")
    assert [p["id"] for p in ledger.open_prompts(root, "s1")] == ["P2"]

def test_addressed_needs_evidence_and_known_id(root):
    ledger.add_prompt(root, "s1", "a")
    with pytest.raises(ValueError): ledger.set_status(root, "P1", "addressed", evidence="  ")
    with pytest.raises(KeyError): ledger.set_status(root, "P9", "addressed", evidence="x")

def test_log_prompt_hook_logs_and_tells_id(root):
    r = run_hook("log_prompt", {"session_id": "s1", "prompt": "add a BOM gate"}, root)
    assert r.returncode == 0 and "Logged as P1" in r.stdout
    assert ledger.open_prompts(root, "s1")[0]["text"] == "add a BOM gate"

def test_empty_prompt_not_logged(root):
    run_hook("log_prompt", {"session_id": "s1", "prompt": "   "}, root)
    assert ledger.prompts(root) == []

def test_stop_blocked_while_open_then_allowed_when_addressed(root):
    ledger.add_prompt(root, "s1", "keep FEA envelope")
    r = run_hook("stop_gate", {"session_id": "s1", "stop_hook_active": False}, root)
    assert r.returncode == 2 and "P1" in r.stderr
    ledger.set_status(root, "P1", "addressed", evidence="U2.3")
    assert run_hook("stop_gate", {"session_id": "s1"}, root).returncode == 0

def test_other_sessions_prompts_do_not_block(root):
    ledger.add_prompt(root, "s2", "x")
    assert run_hook("stop_gate", {"session_id": "s1"}, root).returncode == 0

def test_override_and_forced_stop_after_three_blocks(root):
    ledger.add_prompt(root, "s1", "x")
    assert run_hook("stop_gate", {"session_id": "s1"}, root, HANGAR_ALLOW_STOP="1").returncode == 0
    codes = [run_hook("stop_gate", {"session_id": "s1", "stop_hook_active": True}, root).returncode for _ in range(4)]
    assert codes == [2, 2, 2, 0]
    assert "stop-forced" in (root / "ledger" / "events.jsonl").read_text()

def test_reinject_after_compaction_lists_open_prompts_and_units(root):
    ledger.add_prompt(root, "s1", "keep FEA envelope")
    out = run_hook("reinject", {"source": "compact", "session_id": "s1"}, root).stdout
    assert "keep FEA envelope" in out and "Unit U9.2: Open thing" in out and "U9.1" not in out

def test_reinject_startup_is_short(root):
    out = run_hook("reinject", {"source": "startup", "session_id": "s1"}, root).stdout
    assert "plans/2026-11-20-x.md" in out and "Open prompts: 0" in out

def test_hook_never_crashes_on_bad_input(root):
    r = subprocess.run([sys.executable, str(REPO / "harness/hooks/stop_gate.py")], input="not json",
                       capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
    assert r.returncode == 0

def test_cli_list_and_addressed(root):
    ledger.add_prompt(root, "s1", "a")
    cli = [sys.executable, str(REPO / "harness/ledger.py")]
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
    assert subprocess.run(cli + ["addressed", "P1"], env=env, capture_output=True).returncode == 2
    assert subprocess.run(cli + ["addressed", "P1", "--evidence", "done"], env=env).returncode == 0
    assert "[addressed]" in subprocess.run(cli + ["list"], env=env, capture_output=True, text=True).stdout
```
For `from harness import ledger` to work in tests, add `pytest.ini` at the repo root (H2 must not create one) with:
```
[pytest]
testpaths = tests
pythonpath = .
```
The CLI uses `project_root()` (env `CLAUDE_PROJECT_DIR`); hooks import `ledger` by adding `Path(__file__).resolve().parents[1]` to `sys.path` and `import ledger`.

## Pass check
`cd /home/claude/wt/h1 && python -m pytest tests/harness -q` → all pass (11 tests). Paste the last 3 lines.

## Commit
`git add -A && git commit -m "harness: prompt ledger; log_prompt, stop_gate, reinject hooks"` with the attribution trailer lines your own session instructions specify (they name your model), for example:
```
Co-Authored-By: Claude <model> <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01QqEWVKLu3zpA2K1nz9MZxU
```
Do not push. Do not merge.

## Stop rule
If a test fails for a reason other than missing code, or anything here is ambiguous, stop and report the exact error and the line of this brief. After two failed attempts on the same failure, stop and report both.
