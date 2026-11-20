# Brief H1 fix 1 (review round 1, 2026-11-20)

class: easy · role: builder (Haiku) · same worktree `/home/claude/wt/h1`, same branch `std/h1-ledger-hooks`. Everything in the H1 brief still holds except what this file changes.

## Blocking fixes
1. **UTF-8 on every platform.** At the top of `main()` in each of `log_prompt.py`, `stop_gate.py`, `reinject.py`: read stdin as `sys.stdin.buffer.read().decode("utf-8")`, and call `sys.stdout.reconfigure(encoding="utf-8")` and `sys.stderr.reconfigure(encoding="utf-8", errors="replace")` before printing. `ledger.py` CLI: same reconfigure of stdout/stderr. All file reads/writes in `ledger.py` use `encoding="utf-8"`.

## Ruled by the conductor (plan updated to match)
2. **`deferred` status**, so a turn that ends by asking the user something is not blocked: `set_status(root, id, "deferred", evidence=<reason>)` (reason required, like `addressed`). `open_prompts` returns only `status == "open"`. CLI: `defer <ID> --reason TEXT`. The stop gate message's last line becomes:
   `Address each (python "<abs path to harness/ledger.py>" addressed <ID> --evidence "...") or, if you are waiting on the user, defer it (... defer <ID> --reason "..."). Override: HANGAR_ALLOW_STOP=1.`
3. **Absolute path** in every instruction the hooks print: `python "<root>/harness/ledger.py" ...` with `root` the resolved project root (quotes kept).

## Non-blocking, do them
4. Rename `ledger._line` → `ledger.format_line(p: dict) -> str` (public); `reinject.py` and the CLI use it.
5. A line in `prompts.jsonl` that is not valid JSON is skipped (and counted: `prompts()` keeps going); `log_event(root, {"event": "corrupt-line", "line_no": n})` once per read is not required — just skip.
6. Using `HANGAR_ALLOW_STOP=1` also resets the session's stop counter.

## Tests to add to `tests/harness/test_ledger_hooks.py` (write first, see them fail)
```python
def test_non_ascii_prompt_survives_cp1252_console(root):
    r = run_hook("log_prompt", {"session_id": "s1", "prompt": "Ángulo → σ ≤ 2"}, root, PYTHONIOENCODING="cp1252")
    assert r.returncode == 0 and ledger.open_prompts(root, "s1")[0]["text"] == "Ángulo → σ ≤ 2"
    out = run_hook("reinject", {"source": "compact", "session_id": "s1"}, root, PYTHONIOENCODING="cp1252")
    assert out.returncode == 0 and "Ángulo → σ ≤ 2" in out.stdout

def test_deferred_does_not_block_and_needs_reason(root):
    ledger.add_prompt(root, "s1", "which box size?")
    with pytest.raises(ValueError): ledger.set_status(root, "P1", "deferred", evidence="")
    ledger.set_status(root, "P1", "deferred", evidence="asked user for D5")
    assert run_hook("stop_gate", {"session_id": "s1"}, root).returncode == 0

def test_corrupt_line_is_skipped(root):
    ledger.add_prompt(root, "s1", "a")
    with open(root / "ledger" / "prompts.jsonl", "a", encoding="utf-8") as f: f.write("{not json\n")
    ledger.add_prompt(root, "s1", "b")
    assert [p["id"] for p in ledger.open_prompts(root, "s1")] == ["P1", "P2"]

def test_stop_message_has_absolute_ledger_path(root):
    ledger.add_prompt(root, "s1", "x")
    r = run_hook("stop_gate", {"session_id": "s1"}, root)
    assert str(root / "harness" / "ledger.py") in r.stderr or str(root) in r.stderr
```
Note for the first test: the hook must write UTF-8 even though `PYTHONIOENCODING=cp1252`; the test process decodes its stdout as UTF-8.

## Pass check
`cd /home/claude/wt/h1 && python -m pytest tests/harness -q` → 15 passed. Paste the last 3 lines.

## Commit
`git add harness tests .gitignore pytest.ini && git commit -m "harness: UTF-8 everywhere, deferred status, absolute paths, public format_line (review 1)"` with your usual trailers. Do not push or merge.

## Stop rule
Same as the H1 brief.
