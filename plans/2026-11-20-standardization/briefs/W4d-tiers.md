# Brief W4d-tiers: tier semantics (`--tier N` runs 0..N, `all` = 0-9) and the nonexistent `validate --all`

class: hard · role: builder-plus · plan: §6l W4-D, whole-branch review B4 (reopens U2.1) and B5 (reopens U0.1) · rules: R-a (not applicable: no design handoff), R-b

## Environment
- Windows 11 + Git Bash. Use absolute paths only (e.g. `C:/Users/trist/wt/w4d-tiers/...`); never `../` or `~`: they resolve from the wrong folder inside a worktree.
- Worktree: `git -C C:/Users/trist/dbf-hangar worktree add C:/Users/trist/wt/w4d-tiers -b std/w4d-tiers main`; work only there; create nothing outside it.
- Venv: `python -m venv C:/Users/trist/wt/w4d-tiers/.venv`, then `cd C:/Users/trist/wt/w4d-tiers && C:/Users/trist/wt/w4d-tiers/.venv/Scripts/python.exe -m pip install -e ".[mcp,dev]"`; use that python for every command (with `uv` on PATH: `uv venv` then `uv pip install -e ".[mcp,dev]"`).
- `export PYTHONPATH=C:/Users/trist/wt/w4d-tiers/core`; run `plane` as `C:/Users/trist/wt/w4d-tiers/.venv/Scripts/plane.exe`.
- CI status: `"/c/Program Files/GitHub CLI/gh.exe" -R davinciucberkeley-collab/dbf-hangar run list --branch std/w4d-tiers --limit 1`, then `... run view <id> --json headSha,jobs -q '.headSha, (.jobs[]|.name+" "+.conclusion)'` (`--log-failed` on failure). Never poll api.github.com with curl.
- Brief paths in launch prompts are repo-relative (`plans/<plan>/briefs/<name>.md`).
- `.gitattributes` forces LF; do not change line endings. After your commit, `git ls-files --eol | grep -c "w/crlf"` must print `0`.
- Edit only the files listed under Where. No repo-wide search-and-replace; nothing "while you are there".
- Tests: run the named tests locally with `-m ""`, `-n 4`, in the foreground with a long timeout (this machine needs 3-5 minutes per few files). CI is the one full run; reviewers judge CI by `headSha`.
- Logs only under `C:/Users/trist/wt/w4d-tiers/.logs/`.
- Push only branch `std/w4d-tiers` and wait for CI. Never push or merge `main`. No PR (D30): the conductor merges after review.

## Where
Branch `std/w4d-tiers`, worktree `C:/Users/trist/wt/w4d-tiers`, base = newest local `main` (`git -C C:/Users/trist/dbf-hangar log --oneline -1 main`; verified on `7553ddd`). You may change exactly these files:
- `core/hangar/checks.py` (the `validate` function, lines 1092-1095)
- `core/hangar/design.py` (lines 75, 80, 89)
- `core/hangar/ops/design.py` (`validate_op`, lines 63-67)
- `core/hangar/cli.py` (lines 67-68, the `--tier` option of `validate_cmd`)
- `README.md` (line 43 only)
- `docs/mcp.md` (line 13 only)
- `.claude/agents/reviewer.md` (line 13 only)
- `tests/test_validate.py` (append one test), `tests/test_gates.py` (line 213), `tests/test_review_regressions.py` (line 107), `tests/test_ops_contract.py` (line 83)

Never touch: `designs/**`, `standards/**`, `schema/**`, `PROGRESS.md`, the plan, or any other test unless Pass check 3 shows it red; then change only a literal `5` that means "everything" to `9` and list the file:line in your report. Never `git add -A`; add only changed paths.

## Known failures
Run by the tactician on `main` `7553ddd` (venv python, `-m ""`, `-n 4`): `tests/test_surfaces_in_sync.py tests/test_pdl.py tests/test_adapters.py tests/test_ops_contract.py` gave 98 passed. A second set (`tests/test_gates.py tests/test_review_regressions.py tests/test_claims.py tests/test_point_mass.py tests/test_baseline.py`): 157 passed in 294 s (that run also held `tests/test_ops_contract.py`). `tests/test_seed.py::test_package_is_hangar_and_cli_still_plane` fails locally when `plane` is not on PATH; it is not in this brief's set. Owner for any other red: report to the conductor.

## Plan coverage
| Review item | Status |
|---|---|
| B4: `--tier 5` returns tiers 0-5,7,8 (`checks.py:1093`) | covered (step 1); measured on main: `validate(example, max_tier=5)` tiers `[0, 1, 2, 3, 4, 5, 7, 8]`, `partial False` |
| B4: `cli.py:68` "all = 5", `README.md:43` "T0 to T5 by default", `docs/mcp.md:13` "tiers 0-5", `--tier` offers only 0-5 and all (`ops/design.py:65`) | covered (steps 2-5) |
| B4: one test pinning which tiers run for 5 and for all | covered (step 7) |
| B5: `.claude/agents/reviewer.md:13` cites `plane design validate --all --json` (no such option) | covered (step 6) |
| B5: plan lines 333, 597, 1180 | NOT in this brief: the conductor amends them |

## Facts (tactician, verified on `7553ddd`)
- Today `checks.py:1093` is `card = run_gates(design, 9 if max_tier >= 5 else max_tier)`; `design.py:75` `max_tier: int = 5`; `design.py:80` `partial` is `self.max_tier < 5`; `ops/design.py:65` `tier: Literal["0", "1", "2", "3", "4", "5", "all"] = "5"` and line 67 `validate(design, max_tier=5 if tier == "all" else int(tier))`; `cli.py:67` offers 0-5 and all, default `"5"`, help `Highest validation tier to run (all = 5).`
- Callers relying on "default = everything": `cli.py:308` and `:371` (baseline update/check), `index.py:126`, `ops/edit.py:163`, `studio.py:262`, `mcp_server.py:102` all call `validate(design)` with no tier. `designs/*/baseline.json` hold no `max_tier`; their keys come from the rows of that default run. **Decision: the default stays "run every tier"; only its number changes from 5 to 9.** `validate(design)` returns the same rows as before, so no `baseline.json` key changes. Do not change what `validate(design)` (no argument) runs.
- After this change `--tier N` for N in 0..8 is a partial run (tiers 0..N only, `partial` true, never `accepted`); `--tier 9` and `all` are the full run.
- Tests with a literal 5 meaning "everything": `tests/test_gates.py:213` (`.max_tier == 5`), `tests/test_review_regressions.py:107` (`out["max_tier"] == 5` for `--tier all`), `tests/test_claims.py:233` (`validate(mini, max_tier=5)` expects tier 9 last), `tests/test_point_mass.py:42`, `tests/test_round5.py:238,365,375` (`tier=5`), `tests/test_baseline.py:18-19` (hand-built `Scorecard(..., max_tier=5)`). `tests/test_ops_contract.py:83` expects `tier="9"` to be a bad Literal; after this change `"9"` is valid, so use `"10"`.

## Exact steps and outputs
Work in `C:/Users/trist/wt/w4d-tiers`.

1. `core/hangar/checks.py`: replace the whole `validate` function (lines 1092-1095) with
```python
def validate(design: Design, max_tier: int = 9) -> Scorecard:
    """Run tiers 0..max_tier (9 = every tier, the full run)."""
    card = run_gates(design, max_tier)
    card.max_tier = max_tier
    return card
```
2. `core/hangar/design.py`: line 75 `max_tier: int = 5` becomes `max_tier: int = 9`; line 80 `return self.max_tier < 5` becomes `return self.max_tier < 9`; line 89 docstring `(max_tier < 5)` becomes `(max_tier < 9)`.
3. `core/hangar/ops/design.py` line 65 becomes
`def validate_op(path: str, tier: Literal["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "all"] = "all") -> OpResult:`
and line 67 becomes `card = validate(design, max_tier=9 if tier == "all" else int(tier))`.
4. `core/hangar/cli.py` lines 67-68 become
```python
@click.option("--tier", "max_tier", type=click.Choice(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "all"]),
              default="all", show_default=True, help="Run tiers 0 to N (a partial run, never accepted); all = 0 to 9.")
```
5. Replace these two whole lines (each must match exactly once before you edit).
`README.md` line 43, new text:
```
- **Validate a design:** `plane design validate designs/<id>` (runs every tier T0-T9 by default; `--tier N` runs only T0 to TN and is never accepted)
```
`docs/mcp.md` line 13, new text:
```
- `design_validate(path, tier)` - scorecard across the validation tiers (`tier` is `"0"` to `"9"`, which runs tiers 0 to N, or `"all"`, the default, which runs 0 to 9).
```
6. `.claude/agents/reviewer.md` line 13: replace the phrase `` `plane design validate --all --json` summary `` with `` `plane baseline check --all` (exit 0 = no regression on any design; there is no `validate --all`), and for the PR's design `plane design validate designs/<id> --json` ``. Keep the rest of the line.
7. Tests. Append to `tests/test_validate.py` (two blank lines before it):
```python
def test_tier_n_runs_zero_to_n_and_all_runs_every_tier(example):
    d = load_design(example)
    five = validate(d, max_tier=5)
    assert [t.tier for t in five.tiers] == [0, 1, 2, 3, 4, 5]
    assert five.partial is True and five.accepted is False
    full = validate(d)
    assert [t.tier for t in full.tiers] == [0, 1, 2, 3, 4, 5, 7, 8]
    assert full.max_tier == 9 and full.partial is False
    assert [t.tier for t in validate(d, max_tier=9).tiers] == [t.tier for t in full.tiers]
```
Edit `tests/test_gates.py:213` `.max_tier == 5` to `.max_tier == 9`; `tests/test_review_regressions.py:107` `out["max_tier"] == 5` to `out["max_tier"] == 9`; `tests/test_ops_contract.py:83` `tier="9"` to `tier="10"`. Then run Pass check 3 and fix red tests per Where.

## Pass check
From `C:/Users/trist/wt/w4d-tiers`:
1. Red first (add the test, run before step 1): `.venv/Scripts/python.exe -m pytest -q -m "" tests/test_validate.py -k tier_n_runs` prints `1 failed`.
2. Green after: the same command prints `1 passed`.
3. `.venv/Scripts/python.exe -m pytest -q -m "" -n 4 tests/test_validate.py tests/test_gates.py tests/test_review_regressions.py tests/test_claims.py tests/test_point_mass.py tests/test_baseline.py tests/test_ops_contract.py tests/test_round5.py tests/test_surfaces_in_sync.py` prints no `failed`.
4. Baseline unchanged: `.venv/Scripts/plane.exe baseline check --all; echo $?` prints `0` as its last line and every design block reports `Regressions: 0.`; `git status --short designs` prints nothing.
5. `.venv/Scripts/plane.exe design validate designs/example-tailsitter-wing --tier 5 --json | .venv/Scripts/python.exe -c "import sys,json; d=json.load(sys.stdin); print(d['max_tier'], d['partial'], [t['tier'] for t in d['tiers']])"` prints `5 True [0, 1, 2, 3, 4, 5]`; the same without `--tier` prints `9 False [0, 1, 2, 3, 4, 5, 7, 8]`.
6. `git grep -n "all = 5\|T0 to T5\|tiers 0-5\|validate --all" -- core README.md docs .claude` prints nothing.
7. `git diff --name-only main` lists only paths under Where; `git diff --name-only main | grep -c "^designs/"` prints `0`; `git ls-files --eol | grep -c "w/crlf"` prints `0`. After pushing: CI green by `headSha`.

## Commit
One commit: `fix(validate): --tier N runs tiers 0..N, all = 0-9; reviewer uses baseline check --all (B4, B5)`. Both trailers in one block, exactly:
```
Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>
Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```
Do not run `plane progress --write`; do not edit the plan, `PROGRESS.md` or the ledger. Push `std/w4d-tiers`; no PR.

## Stop rule
Stop and report (file, line, expected vs found) when: an old line is not found as quoted; Pass check 1 is green before step 1; Pass check 4 shows any `baseline.json` change or a regression (do not update baselines); a test outside the Where list is red for a reason other than a literal `5` meaning "everything"; or a fix needs a path outside Where. Two failed attempts at the same step: stop and report to the conductor (it goes to `advisor`).
