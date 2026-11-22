# Brief W4d-viewer-flake: raise the listen backlog of the test HTTP servers (ledger T57)

class: easy · role: builder · plan: §6l W4-D, ledger T57 (Windows CI flake `ERR_CONNECTION_REFUSED`) · rules: R-a (not applicable), R-b

## Environment
- Windows 11 + Git Bash. Use absolute paths only (e.g. `C:/Users/trist/wt/w4d-viewer-flake/...`); never `../` or `~`.
- Worktree: `git -C C:/Users/trist/dbf-hangar worktree add C:/Users/trist/wt/w4d-viewer-flake -b std/w4d-viewer-flake main`; work only there; create nothing outside it.
- Venv: `python -m venv C:/Users/trist/wt/w4d-viewer-flake/.venv`, then `cd C:/Users/trist/wt/w4d-viewer-flake && C:/Users/trist/wt/w4d-viewer-flake/.venv/Scripts/python.exe -m pip install -e ".[mcp,dev]"`; use that python for every command (with `uv` on PATH: `uv venv`, `uv pip install -e ".[mcp,dev]"`). `export PYTHONPATH=C:/Users/trist/wt/w4d-viewer-flake/core`.
- CI status: `"/c/Program Files/GitHub CLI/gh.exe" -R davinciucberkeley-collab/dbf-hangar run list --branch std/w4d-viewer-flake --limit 1`, then `... run view <id> --json headSha,jobs -q '.headSha, (.jobs[]|.name+" "+.conclusion)'` (`--log-failed` on failure). Never poll api.github.com with curl.
- `.gitattributes` forces LF; do not change line endings. After your commit, `git ls-files --eol | grep -c "w/crlf"` must print `0`.
- Edit only the file listed under Where. Logs only under `C:/Users/trist/wt/w4d-viewer-flake/.logs/`.
- Push only branch `std/w4d-viewer-flake` and wait for CI. Never push or merge `main`. No PR (D30).

## Where
Branch `std/w4d-viewer-flake`, base = newest local `main` (verified on `7553ddd`). You may change exactly one file: `tests/test_viewer_static.py` (lines 36-39 and one appended test). Never touch `core/**`, `viewer/**`, `designs/**`, the plan, `PROGRESS.md`, the ledger, or any other test. `git add tests/test_viewer_static.py` only. This file is not touched by `W4d-tiers` or `U4.1-docs`: merge in any order.

## Known failures
Run by the tactician on `main` `7553ddd` locally: `pytest -q -m "" tests/test_viewer_static.py -k every_mode` printed `1 skipped` (the main venv has no `playwright`, so the module is skipped outside CI: `pytest.importorskip` at line 22). So the flake has no local repro: it appears only on Windows CI (T57: run 44993145329 attempt 1; two failures in all, a re-run passed). Verified: `ThreadingHTTPServer.request_queue_size` is `5` (the `socketserver.TCPServer` default, used as the `listen()` backlog) and `daemon_threads` is `True`. Hypothesis (W4-RA, not proven): Chromium opens many parallel connections in Compare mode (two viewports, three.js modules, glb files), more than 5 pending connections overflow the Windows backlog and the browser sees `ERR_CONNECTION_REFUSED`. The fix is cheap and harmless even if the hypothesis is only partly right; the ledger item stays open until CI shows no repeat over the next several runs (conductor decides).

## Plan coverage
| Ledger T57 text | Status |
|---|---|
| the static `pages_base` server refuses connections under parallel requests | covered (step 1: backlog 64 on every test server made by `_serve`, which also serves the Studio fixture at line 80) |
| evidence | local repro not possible (playwright missing locally); one pinning test (step 2) |

## Facts (tactician, verified on `7553ddd`)
- `tests/test_viewer_static.py:11` imports `from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer`; lines 36-39 are
```python
def _serve(handler):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd
```
- `_serve` is called at line 65 (`pages_base`) and line 80 (`_start_studio`); both use the returned object's `server_port`, `shutdown`, `server_close`; a subclass keeps all of those.
- The last test in the file may not be line-stable: append the new test at the very end.

## Exact steps and outputs
Work in `C:/Users/trist/wt/w4d-viewer-flake`.
1. Replace lines 36-39 with
```python
class _Server(ThreadingHTTPServer):
    request_queue_size = 64   # default 5 overflows under Chromium's parallel requests on Windows CI (T57)


def _serve(handler):
    httpd = _Server(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd
```
2. Append to the end of the file (two blank lines before it):
```python
def test_test_servers_listen_with_a_large_backlog():
    httpd = _serve(SimpleHTTPRequestHandler)
    try:
        assert httpd.request_queue_size >= 64
    finally:
        httpd.shutdown()
        httpd.server_close()
```

## Pass check
From `C:/Users/trist/wt/w4d-viewer-flake`:
1. Locally (no playwright): `.venv/Scripts/python.exe -m pytest -q -m "" tests/test_viewer_static.py` prints only skips (`1 skipped`); that is expected, not a failure. If playwright is installed in your venv, instead the file runs: `... -k "backlog"` prints `1 passed` and `... -k every_mode` prints `6 passed`.
2. Syntax and import check that does not need playwright: `.venv/Scripts/python.exe -c "import ast,sys; ast.parse(open('tests/test_viewer_static.py',encoding='utf-8').read()); print('ok')"` prints `ok`; `git diff main -- tests/test_viewer_static.py | grep -c "^[+-] "` prints at most `18`.
3. `git diff --name-only main` prints exactly `tests/test_viewer_static.py`; `git ls-files --eol | grep -c "w/crlf"` prints `0`.
4. After pushing: CI green on both OS by `headSha`, and the job log shows `test_test_servers_listen_with_a_large_backlog PASSED` (`--log` of the test job; the CI step runs `pytest -q -n auto -m ""`).

## Commit
One commit: `test(viewer): raise the test servers' listen backlog to 64 (T57 flake)`. Both trailers in one block, exactly:
```
Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>
Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```
Do not edit the ledger, plan or `PROGRESS.md`. Push `std/w4d-viewer-flake`; no PR.

## Stop rule
Stop and report when lines 36-39 do not match the quoted text exactly, CI fails in any test other than a repeat of T57 (give the id and first error line), or the fix would need a file outside Where. If CI fails with `ERR_CONNECTION_REFUSED` again with this change in, stop and report (the hypothesis is wrong; do not try other fixes). Two failed attempts: stop and report to the conductor.
