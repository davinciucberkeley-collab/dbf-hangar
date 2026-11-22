# Brief W4c-pre-d21-test: the on-disk concept-a D21 test asserts the gates read the fields that are set, not a verdict

class: easy · role: builder · plan: §6l W4-C0b, ledger D39 · rules: R-a (done: the new code was dry-run on a tmp copy with the W4c data and on a pristine copy), R-b

## Environment
- Windows 11 + Git Bash. Use absolute paths only (e.g. `C:/Users/trist/wt/w4c-d21-test/...`); never `../` or `~`: they resolve from the wrong folder inside a worktree.
- Worktree: `git -C C:/Users/trist/dbf-hangar worktree add C:/Users/trist/wt/w4c-d21-test -b std/w4c-d21-test main`; work only there; create nothing outside `C:/Users/trist/wt/w4c-d21-test`.
- Venv per worktree: `python -m venv C:/Users/trist/wt/w4c-d21-test/.venv`, then `cd C:/Users/trist/wt/w4c-d21-test && C:/Users/trist/wt/w4c-d21-test/.venv/Scripts/python.exe -m pip install -e ".[mcp,dev]"`; use that python for every command.
- Venv via uv when `uv` is on PATH: `cd C:/Users/trist/wt/w4c-d21-test && uv venv`, then `uv pip install -e ".[mcp,dev]"`. Plain pip (above) is the fallback.
- CI status: use the GitHub CLI by full path, with the repo given explicitly: `"/c/Program Files/GitHub CLI/gh.exe" -R davinciucberkeley-collab/dbf-hangar run list --branch std/w4c-d21-test --limit 1` and `"/c/Program Files/GitHub CLI/gh.exe" -R davinciucberkeley-collab/dbf-hangar run view <id> --json headSha,jobs -q '.headSha, (.jobs[]|.name+" "+.conclusion)'` (`--log-failed` on failure). Never poll api.github.com with unauthenticated curl.
- Brief paths in launch prompts are repo-relative (`plans/<plan>/briefs/<name>.md`).
- `.gitattributes` forces LF (`* text=auto eol=lf`); do not change line endings. After your commit, `git ls-files --eol | grep -c "w/crlf"` must print `0`.
- Edit only the files the brief lists. No repo-wide `sed` or search-and-replace; nothing "while you are there".
- Tests: run targeted tests locally (the files the change touches). CI is the one full run (`pytest -q -n auto -m ""` in `validate.yml`); reviewers judge CI by `headSha`, not by a local full run.
- Logs only under `C:/Users/trist/wt/w4c-d21-test/.logs/`; no other log location.
- Push only the branch named in the brief and wait for CI; never push or merge `main`. No PRs (D30): the conductor merges after review.

## Where
Branch `std/w4c-d21-test`, worktree `C:/Users/trist/wt/w4c-d21-test`, base = newest local `main` (run `git -C C:/Users/trist/dbf-hangar log --oneline -1 main` first; verified on `0848956`). Test-only. You may change exactly one file: `tests/test_discipline_gates.py`, lines 340-348 on `0848956` (the `_on_disk_has_battery` helper, its decorators and `test_concept_a_d21_on_disk`).

Never touch: `designs/**`, `core/**`, `standards/**`, every other test file, `tests/fixtures/**`, the plan, `PROGRESS.md`; and in this file never `_check_concept_a`, `CONCEPT_A_D21`, `_concept_a_d21` or `test_concept_a_d21_in_memory` (the in-memory test keeps its stricter check on test values). Never `git add -A` or `git add .`.

## Known failures
Run on `main` `0848956` (tactician, 2026-11-22, `-m ""`): `tests/test_fea.py` and `tests/test_discipline_gates.py` together 45 passed, 1 skipped (`test_concept_a_d21_on_disk`: concept-a `pwr-001` has no `battery` key). None failing. Owner: none.
Why this brief exists: with the W4c data applied (battery, motor current and diameter, cruise L/D, harness `hrn-bat`) the OLD `test_concept_a_d21_on_disk` fails at `T2.joint_rf` (`no structural attachment declares a connection`), because two D21 fields have no source (`flight.transition_speed_mps`, `attachments[].connection`). D39: assert that each gate reads the fields that ARE set, not that concept-a passes.

## Plan coverage
| Item | Status |
|---|---|
| D39: on-disk test asserts each discipline gate reads the D21 fields set (no SKIP naming a set field), no verdict asserted | covered, step 1 |
| stays green on current concept-a | covered: the `skipif` stays, so it is skipped while `pwr-001` has no `battery` (as today) |
| stays green on concept-a with the W4c commands applied | covered: dry run on a tmp copy gives `OK` (below) |
| in-memory test and `_check_concept_a` | unchanged on purpose |

## Exact steps and outputs
Work in `C:/Users/trist/wt/w4c-d21-test`. Use the Edit tool.

### 1. Replace the on-disk test (lines 340-348)
Old text (exactly one match; it is the end of the file):
```
def _on_disk_has_battery() -> bool:
    data = yaml.safe_load((CONCEPT_A / "plane.yaml").read_text(encoding="utf-8"))
    return any(c["id"] == "pwr-001" and "battery" in c for c in data["components"])


@pytest.mark.slow
@pytest.mark.skipif(not _on_disk_has_battery(), reason="concept-a pwr-001 has no battery block yet (design PR)")
def test_concept_a_d21_on_disk():
    _check_concept_a(load_design(CONCEPT_A))
```
New text:
```
def _on_disk_has_battery() -> bool:
    data = yaml.safe_load((CONCEPT_A / "plane.yaml").read_text(encoding="utf-8"))
    return any(c["id"] == "pwr-001" and "battery" in c for c in data["components"])


D21_LEAVES = ("capacity_mah", "cells_s", "max_discharge_c", "max_current_a", "prop_diameter_mm", "cruise_ld",
              "cruise_ld_source", "transition_speed_mps", "transition_speed_source", "gauge_awg", "connection", "battery")


def _d21_leaves_set(data: dict) -> set:
    """Names of the D21 fields that the design file sets (components[].battery and its keys, propulsion, flight, harnesses, attachments)."""
    out = set()
    for c in data["components"]:
        if "battery" in c:
            out |= {"battery"} | set(c["battery"])
        out |= set(c.get("propulsion", {}))
    out |= set(data.get("flight", {}))
    for h in data.get("wiring", {}).get("harnesses", []):
        out |= set(h)
    for a in data.get("attachments", []):
        out |= set(a)
    return out & set(D21_LEAVES)


def _check_d21_fields_read(design: Design) -> set:
    """D39: every discipline gate gave a row, and no SKIP row names a D21 field the design sets. No verdict is asserted."""
    import re
    leaves = _d21_leaves_set(design.data)
    card = run(design, tiers={2, 3, 7})
    for cid in IDS:
        rs = rows(card, cid)
        assert rs, f"{cid}: the gate gave no row"
        for r in rs:
            if r.status == SKIP:
                named = sorted(k for k in leaves if re.search(rf"(?<!\w){k}(?!\w)", r.message))
                assert not named, f"{cid}: SKIP names a field that is set {named}: {r.message}"
    return leaves


@pytest.mark.slow
@pytest.mark.skipif(not _on_disk_has_battery(), reason="concept-a pwr-001 has no battery block yet (design PR)")
def test_concept_a_d21_on_disk():
    _check_d21_fields_read(load_design(CONCEPT_A))
```
`run`, `rows`, `IDS`, `SKIP`, `Design`, `load_design`, `yaml`, `pytest`, `CONCEPT_A` already exist in the file (grep-verified: `run` line 78, `rows` line 82, `IDS` line 23). Do not add module-level imports.

## Dry run already done (tactician, 2026-11-22)
The helper body above was run (as a scratch script importing this test module) on:
- a tmp copy of concept-a with the five W4c commands applied (`hangar.cli design set`): returned the set `battery, capacity_mah, cells_s, cruise_ld, cruise_ld_source, gauge_awg, max_current_a, max_discharge_c, prop_diameter_mm` and passed (`OK`);
- a pristine copy of concept-a: no leaves set, passed (`OK`; the live test is skipped there anyway);
- the detector regex fires on a message such as `motor prp-001-ll: propulsion.max_current_a missing` when `max_current_a` is set, and does not fire on `... not judged: operations.yaml#pack_sag_fraction pending` or on `battery_usable_fraction` (the `(?<!\w)`/`(?!\w)` guards).

## Pass check
From `C:/Users/trist/wt/w4c-d21-test`, venv python, `export PYTHONPATH=C:/Users/trist/wt/w4c-d21-test/core`, logs in `.logs/`. Use a 590000 ms timeout.
1. First on a clean `main` checkout state (before your edit), then after it: `.venv/Scripts/python.exe -m pytest -q -m "" tests/test_discipline_gates.py` prints `N passed, 1 skipped` with 0 failed, the same N and the same skip (`test_concept_a_d21_on_disk`) both times.
2. Prove the new test is live on D21 data (throwaway copy, never staged). From `C:/Users/trist/wt/w4c-d21-test`: `cp -r designs/concept-a .logs/d21-copy`; run the five `plane design set` commands of Step 2 in `plans/2026-11-20-standardization/briefs/W4c-concept-a-d21.md` with the path `C:/Users/trist/wt/w4c-d21-test/.logs/d21-copy` instead of `designs/concept-a` (use `.venv/Scripts/python.exe -m hangar.cli design set ...`); then run
   `.venv/Scripts/python.exe -c "import sys; sys.path.insert(0,'C:/Users/trist/wt/w4c-d21-test/tests'); from pathlib import Path; import test_discipline_gates as t; print(sorted(t._check_d21_fields_read(t.load_design(Path('C:/Users/trist/wt/w4c-d21-test/.logs/d21-copy/plane.yaml')))))"`
   It prints the nine names listed under "Dry run" (`battery, capacity_mah, cells_s, cruise_ld, cruise_ld_source, gauge_awg, max_current_a, max_discharge_c, prop_diameter_mm`) and no traceback. Then `rm -rf .logs/d21-copy`.
3. `git diff --name-only main` prints exactly `tests/test_discipline_gates.py`; `git ls-files --eol | grep -c "w/crlf"` prints `0`; `git status --short -- designs core` prints nothing.
4. After pushing: CI green by `headSha` (command in Environment).

## Commit
One commit: `test: on-disk concept-a D21 test asserts the gates read the fields set, not a verdict (D39)`; body line `migration: none (tests only; precedes the concept-a D21 data run)`. Trailers, exactly: `Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>` then the agent attribution line from your own system reminder. Do not run `plane progress --write`; do not edit the plan, `PROGRESS.md` or the ledger. Push `std/w4c-d21-test` and wait for CI.

## Stop rule
Stop and report (file, line, expected vs found) instead of improvising when: the old text is not found exactly once or not at lines 340-348; `run`, `rows` or `IDS` has a different signature than quoted; Pass check 1 differs from `main`; Pass check 2 raises (give the first assertion line; do not edit any other test, `core/` or `designs/**`); a fix would need a path outside Where. Two failed attempts at the same step: stop and report to the conductor (it goes to `advisor`). Do not add a verdict assertion (PASS/FAIL) to the on-disk test.
