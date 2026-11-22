# Brief W4d-concept-a-readme: fix the stale importer path in the concept-a README

class: easy · role: builder · plan: §6l W4-D, subtraction pass (W4-AuS) "Docs" item · rules: R-a (not applicable), R-b

## Environment
- Windows 11 + Git Bash. Use absolute paths only (e.g. `C:/Users/trist/wt/w4d-concept-a-readme/...`); never `../` or `~`.
- Worktree: `git -C C:/Users/trist/dbf-hangar worktree add C:/Users/trist/wt/w4d-concept-a-readme -b std/w4d-concept-a-readme main`; work only there; create nothing outside it. No venv needed: the pass check uses git and grep only.
- CI status: `"/c/Program Files/GitHub CLI/gh.exe" -R davinciucberkeley-collab/dbf-hangar run list --branch std/w4d-concept-a-readme --limit 1`, then `... run view <id> --json headSha,jobs -q '.headSha, (.jobs[]|.name+" "+.conclusion)'`.
- `.gitattributes` forces LF; do not change line endings. After your commit, `git ls-files --eol | grep -c "w/crlf"` must print `0`.
- Push only branch `std/w4d-concept-a-readme` and wait for CI. Never push or merge `main`. No PR (D30).

## Where
Branch `std/w4d-concept-a-readme`, base = newest local `main` (verified on `7553ddd`). You may change exactly one file: `designs/concept-a/README.md` (line 3, one phrase). Never touch `core/**` (a commit that touches both `designs/` and `core/` is rejected by CI), `designs/concept-a/plane.yaml`, `CHANGELOG.yaml`, `baseline.json`, `PROGRESS.md`, or any file outside that one. Disjoint from `W4d-tiers`, `U4.1-docs` and `W4d-viewer-flake`: merge in any order.

## Known failures
Nothing to run: no code or design data changes. Tactician checks on `7553ddd`: `git grep -n "aircraft_platform" -- designs` prints exactly one line, `designs/concept-a/README.md:3`; `ls core/hangar/importers` lists `__init__.py`, `_dbf_dump.py`, `dbf.py` (and more), `ls core/aircraft_platform` does not exist; `plane design set` addresses keys in `plane.yaml` only, and the importer's own text (lines 4-6 of the same README) says "This README and `validator-comparison.md` are hand-written and are not touched by the importer".

## Hand edit or `plane` op (decision)
Hand edit. `CLAUDE.md` says to change designs (data in `plane.yaml`, PDL) with `plane design set`; this README is prose, not PDL, no op writes it, and the importer never regenerates it, so `plane design set` cannot and need not be used. No CHANGELOG entry is needed (the CHANGELOG logs `plane.yaml` value changes). This commit touches `designs/` only, so the designs/core separation rule is met.

## Plan coverage
| Source | Status |
|---|---|
| W4-AuS Docs: `designs/concept-a/README.md:3` cites `core/aircraft_platform/importers/` (now `core/hangar/importers`) | covered (step 1) |

## Exact steps and outputs
In `C:/Users/trist/wt/w4d-concept-a-readme`, in `designs/concept-a/README.md` line 3, replace the text `core/aircraft_platform/importers/` with `core/hangar/importers/` (the phrase occurs once; the rest of the line is unchanged: `(importer: ` + backtick + path + backtick + `).`).

## Pass check
1. `git grep -n "aircraft_platform" -- designs` prints nothing.
2. `git diff --stat main` shows exactly one file, `designs/concept-a/README.md`, `1 insertion(+), 1 deletion(-)`.
3. `git diff --name-only main | grep -c "^core/"` prints `0`; `git ls-files --eol | grep -c "w/crlf"` prints `0`.
4. After pushing: CI green by `headSha` (the designs-only check passes).

## Commit
One commit: `docs(concept-a): README cites core/hangar/importers (was core/aircraft_platform)`. Both trailers in one block, exactly:
```
Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>
Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```
Do not run `plane progress --write`. Push `std/w4d-concept-a-readme`; no PR.

## Stop rule
Stop and report if the phrase is not found exactly once on line 3, or if any other `aircraft_platform` match appears in `designs/`. Do not fix other README text. Two failed attempts: stop and report to the conductor.
