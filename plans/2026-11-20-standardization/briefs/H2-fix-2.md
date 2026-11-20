# Brief H2 fix 2 (review round 2, 2026-11-20)

class: easy · role: builder (Haiku) · worktree `/home/claude/wt/h2`, branch `std/h2-agent-gate`. H2 and H2-fix-1 still hold except as changed here. This brief adds `.gitattributes` to H2's outputs.

## Fixes
1. Create `.gitattributes` at the repo root with exactly one line: `*.sh text eol=lf`.
2. `harness/hooks/run.sh`: insert before the `for` loop:
   `[ -f "$(dirname "$0")/$1.py" ] || exit 0`
   so a missing hook file never blocks. Keep LF endings and mode 755.
3. `harness/install.py`: append `*.sh text eol=lf` to `target/.gitattributes` if that exact line is not already there (create the file if missing); include it in the returned list when it changes.

## Tests to add (write first, see them fail)
```python
def test_repo_forces_lf_for_shell_scripts():
    assert "*.sh text eol=lf" in (REPO / ".gitattributes").read_text().splitlines()

def test_launcher_with_missing_hook_does_not_block(root):
    r = subprocess.run(["sh", str(REPO / "harness/hooks/run.sh"), "no_such_hook"], input="{}",
                       capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
    assert r.returncode == 0

def test_install_writes_gitattributes_once(tmp_path):
    proj = tmp_path / "p"; proj.mkdir()
    installer.install(proj); installer.install(proj)
    assert (proj / ".gitattributes").read_text().count("*.sh text eol=lf") == 1
```

## Pass check
`cd /home/claude/wt/h2 && python -m pytest tests/harness/test_agent_gate_install.py -q --rootdir=.` → 16 passed. Paste the last 3 lines.

## Commit
Stage the changed files explicitly (`.gitattributes harness/hooks/run.sh harness/install.py tests/harness/test_agent_gate_install.py`), message `harness: LF for shell scripts, launcher never blocks on a missing hook (review 2)`, your usual trailers. Do not push or merge.

## Stop rule
Same as the H2 brief.
