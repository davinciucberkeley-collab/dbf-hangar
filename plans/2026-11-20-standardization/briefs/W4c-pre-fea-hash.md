# Brief W4c-pre-fea-hash: gate-only propulsion keys no longer feed the FEA result hash

class: easy · role: builder · plan: §6l W4-C0a, ledger D40 (gap G1 of `W4c-concept-a-d21.md`; D13/D18 hash) · rules: R-a (not applicable: core only; the data handoff is checked in Pass check 4), R-b

## Environment
- Windows 11 + Git Bash. Use absolute paths only (e.g. `C:/Users/trist/wt/w4c-fea-hash/...`); never `../` or `~`: they resolve from the wrong folder inside a worktree.
- Worktree: `git -C C:/Users/trist/dbf-hangar worktree add C:/Users/trist/wt/w4c-fea-hash -b std/w4c-fea-hash main`; work only there; create nothing outside `C:/Users/trist/wt/w4c-fea-hash`.
- Venv per worktree: `python -m venv C:/Users/trist/wt/w4c-fea-hash/.venv`, then `cd C:/Users/trist/wt/w4c-fea-hash && C:/Users/trist/wt/w4c-fea-hash/.venv/Scripts/python.exe -m pip install -e ".[mcp,dev]"`; use that python for every command.
- Venv via uv when `uv` is on PATH: `cd C:/Users/trist/wt/w4c-fea-hash && uv venv`, then `uv pip install -e ".[mcp,dev]"`. Plain pip (above) is the fallback.
- CI status: use the GitHub CLI by full path, with the repo given explicitly: `"/c/Program Files/GitHub CLI/gh.exe" -R davinciucberkeley-collab/dbf-hangar run list --branch std/w4c-fea-hash --limit 1` and `"/c/Program Files/GitHub CLI/gh.exe" -R davinciucberkeley-collab/dbf-hangar run view <id> --json headSha,jobs -q '.headSha, (.jobs[]|.name+" "+.conclusion)'` (`--log-failed` on failure). Never poll api.github.com with unauthenticated curl.
- Brief paths in launch prompts are repo-relative (`plans/<plan>/briefs/<name>.md`).
- `.gitattributes` forces LF (`* text=auto eol=lf`); do not change line endings. After your commit, `git ls-files --eol | grep -c "w/crlf"` must print `0`.
- Edit only the files the brief lists. No repo-wide `sed` or search-and-replace; nothing "while you are there".
- Tests: run targeted tests locally (the files the change touches). CI is the one full run (`pytest -q -n auto -m ""` in `validate.yml`); reviewers judge CI by `headSha`, not by a local full run.
- Logs only under `C:/Users/trist/wt/w4c-fea-hash/.logs/`; no other log location.
- Push only the branch named in the brief and wait for CI; never push or merge `main`. No PRs (D30): the conductor merges after review.

## Where
Branch `std/w4c-fea-hash`, worktree `C:/Users/trist/wt/w4c-fea-hash`, base = newest local `main` (run `git -C C:/Users/trist/dbf-hangar log --oneline -1 main` first; verified on `0848956`). You may change exactly these two files:
- `core/hangar/fea.py` (the block around `FEA_COMPONENT_KEYS` and `part_inputs_fingerprint`, lines 188-199 on `0848956`)
- `tests/test_fea_hash.py` (append two tests at the end)

Never touch: `designs/**` (the committed `fea/*.json` must stay byte-identical), `standards/**`, `core/hangar/sim.py`, `core/hangar/opencae_runner.py`, every other test file, the plan, `PROGRESS.md`. Never `git add -A` or `git add .`.

## Known failures
Run on `main` `0848956` (tactician, 2026-11-22, any venv python with `PYTHONPATH=C:/Users/trist/dbf-hangar/core`, `-m ""`): `tests/test_fea_hash.py` 17 passed; `tests/test_fea.py` plus `tests/test_discipline_gates.py` 45 passed, 1 skipped (`test_concept_a_d21_on_disk`, skipped until concept-a has a battery block). None failing. Owner: none.

## Plan coverage
| Item | Status |
|---|---|
| D40: exclude gate-only propulsion keys `max_current_a`, `prop_diameter_mm` from the hash | covered, step 1 |
| "allow-list of what FEA reads (axis, max_thrust_n)" | covered with one difference: the allow-list is `max_thrust_n`, `axis` AND `role`. Verified by the tactician on a copy of concept-a: an allow-list without `role` changes the hashed bytes of every motor (`role: both` is in the committed hashes) and stales all 28 `fea/*.json`; with `role` kept, 0 stale (also with the D21 data applied). FEA does not read `role` (`sim.py:357-361` reads `axis`, `max_thrust_n`; no other `propulsion` read in `fea.py`, `geometry.py`, `sim.py`: grep-verified). `role` stays only for byte compatibility. |
| a part that is itself a motor (own entry hashed whole) | unchanged: motors are not FEA-eligible (`STRUCTURAL` in `fea.py` has no `motor`) |
| D13 narrowed-hash tests | covered: the whole existing `tests/test_fea_hash.py` must still pass (Pass check 1) |

## Exact steps and outputs
Work in `C:/Users/trist/wt/w4c-fea-hash`. Use the Edit tool.

### 1. `core/hangar/fea.py`
a) Insert this block immediately before the line `def part_inputs_fingerprint(design: Design, part_id: str) -> bytes:` (and after the `FEA_COMPONENT_KEYS = ...` line with its comment, which stay unchanged):
```python
# Propulsion keys of OTHER components that are hashed: sim.py (joint_load_cases) reads axis and max_thrust_n; role stays
# only so the committed hashes stay valid. Gate-only keys (max_current_a, prop_diameter_mm) are left out; add a key here
# when fea.py or sim.py starts reading another one.
FEA_PROPULSION_KEYS = ("max_thrust_n", "axis", "role")


def _other_entry(c: dict) -> dict:
    """The load-relevant keys of a component other than the part being hashed."""
    e = {k: c[k] for k in FEA_COMPONENT_KEYS if k in c}
    if "propulsion" in e:
        e["propulsion"] = {k: v for k, v in e["propulsion"].items() if k in FEA_PROPULSION_KEYS}
    return e


```
b) In `part_inputs_fingerprint`, replace exactly one line.
- old (exactly one match):
```
    comps = [c if c["id"] == part_id else {k: c[k] for k in FEA_COMPONENT_KEYS if k in c} for c in design.components]
```
- new:
```
    comps = [c if c["id"] == part_id else _other_entry(c) for c in design.components]
```
Nothing else in `fea.py` changes (`FEA_COMPONENT_KEYS` keeps `"propulsion"` in its tuple).

### 2. `tests/test_fea_hash.py`: append at the end of the file (two blank lines before the first `def`)
```python
def test_gate_only_propulsion_keys_leave_hash_unchanged(tmp_path):
    def fn(d):
        for c in d["components"]:
            if c["type"] == "motor":
                c["propulsion"]["max_current_a"] = 11.2
                c["propulsion"]["prop_diameter_mm"] = 228.6
    assert fea.part_hash(edit_plane(tmp_path, fn, "a"), PART) == \
        fea.part_hash(edit_plane(tmp_path, lambda d: None, "b"), PART)


def test_max_thrust_change_changes_hash(tmp_path):
    def fn(d):
        next(c for c in d["components"] if c["type"] == "motor")["propulsion"]["max_thrust_n"] += 1.0
    assert fea.part_hash(edit_plane(tmp_path, fn, "a"), PART) != \
        fea.part_hash(edit_plane(tmp_path, lambda d: None, "b"), PART)
```
(`edit_plane`, `PART`, `fea` already exist in the file.) Dry run by the tactician: on `main` the first test fails (`AssertionError` at its `assert`) and the second passes; with step 1 applied both pass and the whole file is 19 passed.

## Pass check
From `C:/Users/trist/wt/w4c-fea-hash`, venv python, `export PYTHONPATH=C:/Users/trist/wt/w4c-fea-hash/core`, logs in `.logs/`. Use a 590000 ms timeout.
1. `.venv/Scripts/python.exe -m pytest -q -m "" tests/test_fea_hash.py` prints `19 passed`.
2. `.venv/Scripts/python.exe -m pytest -q -m "" -n 3 tests/test_fea.py tests/test_discipline_gates.py` prints `45 passed, 1 skipped`.
3. `git diff --name-only main` prints exactly `core/hangar/fea.py` and `tests/test_fea_hash.py`; `git diff --name-only main | grep -c "^designs/"` prints `0`; `git ls-files --eol | grep -c "w/crlf"` prints `0`.
4. Zero stale on the live concept-a: `.venv/Scripts/python.exe -m hangar.cli baseline check designs/concept-a` prints `Result: pass` and `Regressions: 0` (about 80 s). `test_committed_concept_a_results_are_fresh` in Pass check 1 is the same assertion at hash level. If either shows a stale part: stop (the rule changed the hashed bytes).
5. After pushing: CI green by `headSha` (command in Environment).

## Commit
One commit: `fea: gate-only propulsion keys (max_current_a, prop_diameter_mm) no longer feed the result hash (D40)`; body line `migration: none (hash input narrowed; committed results stay valid, 0 stale)`. Trailers, exactly: `Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>` then the agent attribution line from your own system reminder. Do not run `plane progress --write`; do not edit the plan, `PROGRESS.md` or the ledger. Push `std/w4c-fea-hash` and wait for CI.

## Stop rule
Stop and report (file, line, expected vs found) instead of improvising when: an old string is not found exactly once; the committed concept-a results show any stale part after step 1 (Pass check 4) or `tests/test_fea_hash.py` has a failure other than the first new test before step 1; a count above differs; a fix would need a path outside Where. Two failed attempts at the same step: stop and report to the conductor (it goes to `advisor`). Do not change `FEA_COMPONENT_KEYS`, do not drop `role` from the allow-list, do not regenerate any `fea/*.json`.
