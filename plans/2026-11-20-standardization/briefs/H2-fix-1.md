# Brief H2 fix 1 (review round 1, 2026-11-20)

class: easy · role: builder (Haiku) · same worktree `/home/claude/wt/h2`, same branch `std/h2-agent-gate`. Everything in the H2 brief still holds except what this file changes.

## Blocking fixes
1. **UTF-8 stdin.** `agent_gate.py` reads `json.loads(sys.stdin.buffer.read().decode("utf-8"))` and calls `sys.stderr.reconfigure(encoding="utf-8", errors="replace")` before writing.

## Ruled by the conductor (plan updated to match)
2. **Agent table, not any mention.** A role is allowed only if it appears in backticks in a row of a markdown table whose header row contains `Pass criterion` (the agent-table format), in the newest `plans/*.md`. Implement `agent_table_roles(plan_text: str) -> set[str]` in `agent_gate.py`: walk lines; a line starting with `|` whose cells include `Pass criterion` starts a table; following `|` lines (skip the `|---|` separator) belong to it until a non-`|` line; collect every `` `name` `` in those rows.
3. **Launcher, so `python` vs `python3` doesn't matter.** Create `harness/hooks/run.sh` (LF line endings, `chmod +x`):
   ```sh
   #!/bin/sh
   # Runs a hangar hook with the first Python 3 found. Usage: run.sh <hook-name>
   for c in python3 python py; do
     if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
       exec "$c" "$(dirname "$0")/$1.py"
     fi
   done
   echo "hangar hook $1: no Python 3 found on PATH" >&2
   exit 0
   ```
   `.claude/settings.json` commands become `sh "$CLAUDE_PROJECT_DIR/harness/hooks/run.sh" <name>` for each of the four hooks (`log_prompt`, `agent_gate`, `reinject`, `stop_gate`). Keep everything else in settings.json as it was.
4. **Installer:** refuse when `target.resolve() == Path.home().resolve()` (raise `ValueError("install into a project folder, not your home folder")`; CLI prints it and exits 2). Append the lines `ledger/prompts.jsonl`, `ledger/events.jsonl`, `ledger/.stop_blocks.json` to `target/.gitignore`, each only if not already present (create the file if missing). Add `from __future__ import annotations` at the top of `install.py`.

## Tests to add to `tests/harness/test_agent_gate_install.py` (write first, see them fail)
```python
def test_role_must_be_in_an_agent_table_not_just_mentioned(root):
    (root / "plans" / "2026-11-21-y.md").write_text(
        "We might use `recon` later.\n\n| Step | Role | Model | Pass criterion |\n|---|---|---|---|\n| H1 | `builder` | Haiku | tests |\n", encoding="utf-8")
    assert gate(task("recon"), root).returncode == 2
    assert gate(task("builder", "Pass check: x. Stop rule: y."), root).returncode == 0

def test_non_ascii_prompt_cannot_slip_past_gate(root):
    r = subprocess.run([sys.executable, str(REPO / "harness/hooks/agent_gate.py")],
                       input=json.dumps(task("general-purpose", "Ángulo → σ"), ensure_ascii=False).encode("utf-8"),
                       capture_output=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root), PYTHONIOENCODING="cp1252"))
    assert r.returncode == 2

def test_settings_use_launcher():
    s = json.loads((REPO / ".claude/settings.json").read_text())
    cmds = [h["command"] for ev in s["hooks"].values() for e in ev for h in e["hooks"]]
    assert all(c.startswith('sh "$CLAUDE_PROJECT_DIR/harness/hooks/run.sh" ') for c in cmds)

def test_launcher_runs_a_hook(root):
    r = subprocess.run(["sh", str(REPO / "harness/hooks/run.sh"), "agent_gate"], input=json.dumps(task("general-purpose")),
                       capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
    assert r.returncode == 2

def test_install_refuses_home_and_writes_gitignore(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path)); monkeypatch.setenv("USERPROFILE", str(tmp_path))
    with pytest.raises(ValueError): installer.install(tmp_path)
    proj = tmp_path / "proj"; proj.mkdir()
    installer.install(proj); installer.install(proj)
    assert (proj / ".gitignore").read_text().count("ledger/prompts.jsonl") == 1
```
Update the existing `test_reviewer_in_plan_allowed` and `test_builder_needs_builder_ready_brief` fixture plan so its two roles sit in a table with a `Pass criterion` header:
`"| Step | Role | Model | Pass criterion |\n|---|---|---|---|\n| H1 | `builder` | Haiku | t |\n| HR | `reviewer` | Opus | t |\n"`.

## Pass check
`cd /home/claude/wt/h2 && python -m pytest tests/harness/test_agent_gate_install.py -q --rootdir=.` → 13 passed. Paste the last 3 lines.

## Commit
`git add .claude harness tests && git commit -m "harness: UTF-8 gate, agent-table rule, python launcher, safer installer (review 1)"` with your usual trailers. Do not push or merge.

## Stop rule
Same as the H2 brief.
