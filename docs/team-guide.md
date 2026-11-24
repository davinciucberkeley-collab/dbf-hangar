# Team guide: working in dbf-hangar

This guide is for Dillon, James and Vaibhav. Each of you runs your own Claude Code session on your own Windows machine. All of you work in one repo, `dbf-hangar`. You each use your own branch, so nothing interferes.

Read "The five rules" and "Team rules" first. Then jump to the section for your task.

## The five rules

1. One repo: `dbf-hangar`. No new repos, no forks for work. Everything lands on `main` after review.
2. Your own branch, one topic per branch. See section 9.
3. Designs are data. Change them with `plane design ...`, never by editing code. A commit changes `designs/` or `core/`, never both (unless its message has a line starting `migration:`).
4. Every threshold lives in `standards/*.yaml` with a source, or `pending`. Fix the design, not the threshold.
5. Use the `plane` CLI (or MCP) for every operation. Do not rewrite validation, mass, export or analysis yourself.

Who does what:

- Dillon: designs and concepts.
- James: tests, harness install, standards and connection types.
- Vaibhav: FEA on Windows.
- Tristan: owns the repo and merges.

## Team rules (Tristan to confirm)

These rules are not final. Tristan confirms or edits them (decision D63). Until then, follow them as written.

- O1 Access: Tristan asks the org owner to add you three as collaborators with write access. Until then you cannot push or run `plane design propose`.
- O2 No pushes to `main`: every change from you is a pull request (PR). The "push straight to `main`" rule (D30) is for Tristan and the conductor only.
- O3 Merging: Tristan merges everything, with a plain merge commit. Dillon must approve design PRs. James's review on test and standards PRs is advice only.
- O4 Work comes from ledger tasks: Tristan gives you a task with your name on it. Put its id in your branch and PR text. You do not edit `plans/`, `ledger/`, `reviews/` or `PROGRESS.md`. Tristan closes the task.
- O5 Agents: you do not run the `conductor`. Use `design-engineer`, `recon`, `scout` and plain Claude Code. For a builder, put the exact output, exact inputs, a pass check and a stop rule in your prompt, or ask Tristan for a brief.
- O6 Hooks: keep them on. If the Stop hook gets in the way, set `HANGAR_ALLOW_STOP=1`. You do not edit `.claude/` or `harness/` on a topic branch (James may on a harness branch).
- O7 Branch names: `std/<topic>` for tests, standards, knowledge and harness; `design/<id>/<slug>` for design changes. You may use `std/<person>-<topic>`.
- O8 Commit trailer: your commits keep your own git author. They also end with Tristan's `Co-authored-by` trailer (as `CLAUDE.md` says) plus the line Claude Code adds. Tristan may drop it for you.
- O9 `concept-a`: every change goes through `plane design set` and a PR. Dillon owns it. Tristan does not re-run the importer on it without telling Dillon. New concepts start with `plane design new` and belong to their author.
- O10 Python: 3.12 is recommended (CI uses it). 3.10 or later installs.
- O11 Ledger and weekly update: only Tristan adds ledger items. You add your weekly update once, on a branch `std/<person>-update-<week>`, and re-run it after a conflict.

## 1. Get set up

Read this once, on a new machine. You get a working `plane` in about 10 minutes.

You need:

- Git and Git LFS. Meshes (`*.stl`, `*.step`, `*.stp`, `*.glb`, `*.f3d`, `*.SLDPRT`) are LFS files. Check it is installed:

```
git lfs version
```

- Python 3.12 (see O10).
- Claude Code.
- GitHub access to the repo (see O1).

Clone the repo and go into it.

```
git clone https://github.com/davinciucberkeley-collab/dbf-hangar.git
cd dbf-hangar
```

Make a virtual environment and turn it on.

**Git Bash:**

```
python -m venv .venv
source .venv/Scripts/activate
```

**PowerShell:**

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell refuses to run the activate script, ask Tristan or James.

Install the package. This takes a few minutes (mujoco, scipy, trimesh). The extras are `mcp` (the MCP server) and `dev` (pytest and friends).

```
python -m pip install -e ".[mcp,dev]"
```

Check the version.

```
plane --version
```

It must print `plane, version 1.0.0.dev0`. If it prints something else, an older `plane` is earlier on your PATH. Call `.venv/Scripts/plane` (Git Bash) or `.\.venv\Scripts\plane` (PowerShell) instead.

Tell git who you are, before your first commit. The clone has no name or email.

```
git config user.name "<your name>"
git config user.email "<your email>"
```

See what is installed.

```
plane tools doctor
```

It prints one row per tool. On a fresh install it looks like this:

```text
opencae      missing  OpenCAE not found; run: plane fea setup --opencae-python <python of the environment with OpenCAE's libraries> --opencae-root <OpenCAE folder>
mujoco       ok       mujoco 4.0.1
aerosandbox  missing  aerosandbox not installed; run: python -m pip install aerosandbox
blender      planned  planned, not implemented in v1.0 (optional collision/transport check, will use Blender 4.5); nothing to run yet
sitl         planned  planned, not implemented in v1.0 (ArduPilot SITL flight-case plant, report-only)
davinci      missing  DaVinci API access not configured (D3 decided: skip until real calls after Dec 1); fix: configure access when that work starts
```

Only OpenCAE matters to Vaibhav. `missing` is not an error for everyone else. A missing tool gives SKIP with the fix, never a silent pass.

List the designs.

```
plane list
```

You get one row per design with the columns `id name status lift vtol_method`. The ids are `c0-a1 c0-a2 c0-a3 c0-lift-cruise concept-a example-tailsitter-wing tiltwing-cakir`.

Run the tests. The quick check takes about 2 seconds and is enough to know your setup works.

```
python -m pytest -q tests/test_cli_doc.py
```

The local suite skips slow tests. It printed `939 passed, 1 skipped` in about 6.5 minutes on Tristan's machine.

```
python -m pytest -q -m "not slow" -n auto
```

CI runs the slow ones too.

All commands are listed in [cli.md](cli.md).

## 2. Connect your Claude Code session

Read this to learn what your session does by itself and what is optional.

Nothing needs installing in the clone. Start Claude Code from the repo root and it is all active:

- `.claude/settings.json` sets the output style `quiet` and wires four hooks.
- `.claude/agents/` holds the 10 roles.
- `.claude/output-styles/quiet.md` is the style.

The hooks run with your system Python, not the venv. If no Python 3.8 or newer is found, they exit quietly and never block you.

What you will see:

- Session start: a line `hangar: roles in .claude/agents/ (launch only these); plan: plans/2026-11-20-standardization.md`. On resume you also see `Open prompts: ...`.
- Every prompt you type is logged and the session is told `Logged as P1. When done: ... addressed P1 --evidence "<what answered it>"`. The log is `ledger/prompts.jsonl`. It is git-ignored. It stays on your machine and Tristan never sees it.
- Stop: the session cannot stop while it has open prompts. You see `Open prompts in this session: P1` with the exact `addressed` and `defer` commands. Claude closes the prompt itself. If it keeps blocking, answer or defer the prompt. After 3 blocks in a row the stop is forced and logged. Setting `HANGAR_ALLOW_STOP=1` in the environment turns the gate off.
- Agent launch: checked by the agent gate. See section 8.

The output style `quiet` gives results, decisions and blockers, with no narration. Question answers are in full. An end-of-task report is at most five lines.

### MCP (optional)

The CLI does everything MCP does. If you want Claude to call `plane` as tools, run this from the repo root with the venv active.

```
claude mcp add dbf-hangar -- plane-mcp
```

It prints `Added stdio MCP server dbf-hangar with command: plane-mcp  to local config`. Check it.

```
claude mcp list
```

You should see a line for `dbf-hangar` that ends with `Connected`. Remove it with:

```
claude mcp remove dbf-hangar
```

It is stored per user and per folder, not in the repo. If you start Claude Code from a shell without the venv, give the full path to `.venv\Scripts\plane-mcp.exe` instead. This case was not tested. Tool names follow the operations (`design_validate`, `design_new`, ...). See [mcp.md](mcp.md).

### Studio (point and click, for Dillon)

Studio opens an app and a browser. It edits the same files as the CLI.

```
plane studio
```

To serve it without a browser, on a port you choose (default 8765):

```
plane studio --port 8765 --no-browser
```

Stop it with Ctrl+C in that terminal.

### Installing the harness in another folder (James)

You do not need this for this repo. It copies the 10 agents, the quiet style and `harness/` into another project and merges the four hooks into its `.claude/settings.json`. It keeps other hooks and an existing `outputStyle`. It refuses your home folder, and running it twice is safe.

```
python harness/install.py --target <project-folder>
```

It printed `Installed hangar harness into <dir> (25 files)`. The target gets the hooks and agents but not `plane`. Install the package there separately.

## 3. Create a design

Read this to start a new design. Three commands, no code. This is Dillon's main path.

Make a design from a template. The template is any existing design id. The default is `example-tailsitter-wing`.

```
plane design new my-test --template example-tailsitter-wing
```

It prints the path of the new `plane.yaml`. These are the errors you can hit. Each exits with code 2:

```text
plane: design 'my-test' already exists
plane: invalid id 'Bad_Id': must match ^[a-z0-9][a-z0-9_-]*$
plane: template 'nope' not found
```

Your own id and template look like this:

```
plane design new <new-id> --template <template-id>
```

You can also copy a design. This does not copy `fea/`, `.sweeps`, `CHANGELOG.yaml`, `baseline.json` or `import-report.json`.

```
plane design copy designs/<src> <new-id>
```

A design is a folder `designs/<id>/` with `plane.yaml` (written in PDL) and a `CHANGELOG.yaml` that fills in as you edit. For PDL, read [pdl/README.md](pdl/README.md).

Check the design. This runs tiers T0 to T9.

```
plane design validate designs/<id>
```

For the unmodified example you get `Accepted: yes` with some WARN rows (report-only until 2026-12-08). The scorecard starts like this:

```text
# Scorecard: my-test

**Accepted:** yes

| Tier | Status | Check | Result | Criterion |
|---|---|---|---|---|
| 0 schema | PASS | T0.schema | PASS: matches schema v1.0 | schema/plane.schema.json |
```

It ends with `Fidelity: 5 of 61 blocking checks use sourced thresholds; 0 components have measured mass.`

### Baselines

CI fails only on regressions against a design's `baseline.json`. If your design is accepted, it needs none.

```
plane baseline check designs/<id>
```

For an accepted design it prints `Accepted. No baseline needed.` and exits 0. If the design has known FAIL or SKIP rows (a copy of `concept-a` does), CI fails until you record them. You see:

```text
**Missing baseline.json.** Run "plane baseline update designs/ca-x" and commit it.
```

Record the known rows. A full design takes about 3 minutes.

```
plane baseline update designs/<id>
```

Never update a baseline to hide a regression. Update it only when you fixed rows (improvements) or created the design.

### Commit the design

Commit the whole `designs/<id>/` folder (with `baseline.json` when needed). Touch nothing under `core/` in that commit.

```
git add designs/<id>
git commit -m "<message>"
```

## 4. Iterate on a design

Read this for the loop: change one value, re-check, see the effect.

Read a value. The key is a dotted path into `plane.yaml`.

```
plane design get designs/my-test --key requirements
```

```text
{"mtow_g": 900, "stall_speed_max_mps": 9, "cruise_speed_mps": 14, "budget_usd": 250}
```

Change a value. `--why` is required.

```
plane design set designs/my-test requirements.mtow_g --value 950 --why "try a lighter airframe"
```

```text
requirements.mtow_g: 900 -> 950
```

Every set is appended to `designs/<id>/CHANGELOG.yaml` with the date, key, old value, new value, why and kind. The kind is `add`, `subtract`, `modify` or `remove` (`--kind`, default `modify`). Prefer subtract, then modify, then add. `--kind remove` deletes one list element, addressed as `name[id]`.

A bad value is refused and the file is not touched. The command exits 2 and prints the allowed type, for example:

```text
plane: requirements.mtow_g: 'abc' is not of type 'number' (data path requirements/mtow_g; schema path ...; allowed type number)
```

A bad key prints the keys that exist:

```text
plane: no.such.key: no key 'no' (have: ['attachments', 'authors', 'components', ...])
```

Add to a list, or remove from it. This works only on one-line `[list]` values.

```
plane design set designs/my-test authors --append Dillon --why "credit"
plane design set designs/my-test authors --remove "platform bootstrap" --why "tidy"
```

```text
authors: ['platform bootstrap'] -> ['platform bootstrap', 'Dillon']
authors: ['platform bootstrap', 'Dillon'] -> ['Dillon']
```

Change two keys in one go.

```
plane design set designs/my-test flight.cl_max --value 1.3 --also requirements.budget_usd=300 --why "two keys"
```

```text
flight.cl_max: 1.0 -> 1.3
requirements.budget_usd: 250 -> 300
```

Try several values without changing the design. A sweep edits a scratch copy in `.sweeps/` (git-ignored). Your file stays as it was. Give `--values` once per value. A single `--values 1.0,1.2` is rejected.

```
plane design sweep designs/my-test flight.cl_max --values 1.0 --values 1.2 --values 1.4
```

```text
1.0: accepted=True mass_g=759.0 static_margin=0.1404 stall_speed_mps=7.79 hover_tw=2.418 failures=[]
1.2: accepted=True mass_g=759.0 static_margin=0.1404 stall_speed_mps=7.12 hover_tw=2.418 failures=[]
1.4: accepted=True mass_g=759.0 static_margin=0.1404 stall_speed_mps=6.59 hover_tw=2.418 failures=[]
```

Not every key moves these numbers. `requirements.mtow_g` is a requirement, so sweeping it gives identical results. Use a key that drives the physics, such as `flight.cl_max`.

Compare two designs. It prints one line per differing key.

```
plane design diff designs/my-test designs/example-tailsitter-wing
```

```text
requirements.mtow_g: 950 -> 900
```

### Gates

The gates are the checks in tiers T0 to T9, each blocking or report-only.

```
plane gate list
```

```text
T0 T0.schema          blocking     schema/plane.schema.json
...
T7 T7.integration     report-only  gate-thresholds.yaml#wire_clearance_mm
T8 T8.sourcing        report-only  gate-thresholds.yaml#bom_verified_max_age_days
T9 T9.claims          blocking     claims.yaml#recompute_rel_tol
```

Ask why a check passes or fails, and where its threshold comes from:

```
plane gate explain T3.endurance --design designs/<id>
```

It prints `T3.endurance (tier 3, report-only): operations.yaml#energy_reserve_fraction`, then the threshold, its value, its source and what it checks.

### Claims

These examples use `concept-a`. They show claims and how each is recomputed.

```
plane claim list designs/concept-a
plane claim check designs/concept-a
plane claim explain designs/concept-a CL-A-CG
```

`claim list` prints rows like `CL-A-MASS-PRED            PASS         1.469758376 kg  +0.0%`. `claim check` prints `T9 PASS` and `note: 53 PASS recomputed, 40 PASS read from source (stored results checked against their limits, analyses not re-run)`. `claim explain` prints a tree: claim, calculation, parameter, source.

### Bill of materials

```
plane bom list designs/concept-a
plane bom cost designs/concept-a
```

`bom list` prints rows like `p01  x5  46.9  verified`. `bom cost` prints `total $1262.50 (42 lines costed; 0 without cost; 16 unverified)`. To mark an item verified, use `plane bom verify <path> <item> <method> <evidence> <by>`. It records how and by whom a part was checked.

### Mass and simulation

```
plane design mass designs/<id>
plane sim drop designs/<id>
plane design export designs/<id> --format glb --out <file>
```

`design mass` prints JSON with `mass_g`, `cg_mm` and the inertia. `sim drop` prints `drop height 0.3 m (standards drop_height_m)`, then one line per joint such as `T2.sim_drop_loads PASS: wing-body: peak 82.6 N <= 125 N in drop test`. `design export` writes the file and prints its path. For a mechanism, use `plane sim mechanism <path> <mechanism-id>`. It runs the mechanism simulation.

### FEA (Vaibhav)

Show the plan for one part. The plan lists the part, the material (`db_petg_um`), the allowable (12.6 MPa), the ultimate factor (1.5) and more.

```
plane fea plan designs/concept-a wng-004-l
```

Save where OpenCAE is, once, with `plane fea setup --opencae-python <path> --opencae-root <path>`. It writes `opencae.local.json`, which is git-ignored. Run it with `plane fea run designs/<id> --part <part>`, or `--all` for every part. OpenCAE (GPL-3.0) is an outside tool. The repo does not contain it. Until it is installed, `plane tools doctor` says `missing` and FEA results are SKIP. These two commands were checked with `--help` only.

### Schema migration

```
plane design migrate designs/<id>
```

This is a dry run. It printed `schema_version 1.0 -> 1.1` and `no fields added, removed or renamed ...`. Add `--write` to apply it.

## 5. Propose your change

Read this to get a design change onto `main`.

```
plane design propose designs/<id> "<title>"
```

This one needs `gh` (the GitHub CLI) installed and logged in, and push access to the repo (see O1). It was not run for this guide, because it pushes to the real remote. Here is what it does, from the code:

1. It needs uncommitted changes under that design folder. Otherwise it exits 2 with `no uncommitted changes under <dir>`.
2. It creates the branch `design/<id>/<slug>` from your current HEAD. The slug is your title in lowercase, with non-letters and non-digits turned into `-`, at most 40 characters.
3. It adds only that design folder and commits `design(<id>): <title>`, with the trailer `Co-authored-by: Tristan Hottier <...>`.
4. It pushes the branch.
5. It opens a PR against `main`, switches back to the branch you started on and prints the PR URL.

It looks for `gh` on your PATH, then in `C:/Program Files/GitHub CLI/gh.exe`. You can point it elsewhere with the environment variable `HANGAR_GH`.

Because the new branch starts at your current HEAD, run it from an up-to-date `main` with no other commits. Edits outside the design folder stay uncommitted on your branch.

Who reviews: several people may propose changes to the same design, and Dillon picks which merge (R25). Tristan clicks merge (O3). The branch is deleted after the merge. For example, PR #3 (`concept-a: elevon mechanisms declared with measured ratio (U3.4)`) was merged on 2026-11-22.

If you cannot use `propose`, do the same by hand: your own branch, commit, push, open a PR on GitHub (see section 9).

Never edit `designs/concept-a/plane.yaml` by hand. Use `plane design set` (O9).

## 6. Add a test

Read this to add or run tests. This is James's main path.

Tests live in `tests/` (`test_*.py`, pytest, about 60 files):

- `tests/harness/` holds hook and installer tests.
- `tests/team_tasks/` holds shell scripts that exercise team tasks.
- `tests/fixtures/` holds shared data.
- `tests/conftest.py` has the fixtures `example` and `mutate`. `mutate` changes a copy of the example design and runs the validator.
- `tests/testutil.py` has `EXAMPLE_PATH` and `statuses`.

`pytest.ini` skips slow tests by default (`-m "not slow"`). Mark a long test (MuJoCo, FEA, per-design validation) with `@pytest.mark.slow`. It is skipped locally and run in CI.

Run one file:

```
python -m pytest -q tests/test_cli_doc.py
```

Run one file without the parallel plugin. This helps when you debug a single test.

```
python -m pytest -q -p no:xdist tests/test_cli_doc.py
```

Run the whole local suite:

```
python -m pytest -q -m "not slow" -n auto
```

CI runs everything (`pytest -q -n auto -m ""`).

`docs/cli.md` is generated. The test `tests/test_cli_doc.py::test_cli_doc_is_current` fails when it is out of date. Regenerate it with:

```
plane docs cli --out docs/cli.md
```

Rules for tests:

- A test change touches `tests/` only. If the test needs a code change, make that a separate commit on a separate branch.
- Tests must not read files outside the repo. Use fixtures in the repo, or `skipif` with a CI fixture (see [agents.md](../standards/agents.md)).
- CI runs on Windows and Linux. Use `pathlib`. Do not hard-code `\` or `/` in assertions. The repo forces LF line endings.

## 7. Add a standard, a connection type, knowledge

Read this for the short recipe for each.

### Standards

Thresholds live only in `standards/*.yaml`. Each key has a `source:` or `source: pending`. The files are `claims.yaml`, `connection-types.yaml`, `design-standards.yaml`, `gate-thresholds.yaml`, `gates.yaml`, `load-cases.yaml`, `manufacturing.yaml`, `operations.yaml` and `program.yaml`.

Look at one threshold:

```
plane standards show static_margin
```

It prints `static_margin (aero)`, `min: 0.05`, `max: 0.15`, then `rule:`, `source: MIT 16.01 design rules; ...` and `note:`. List them all (columns key, section, value, source), or only the ones still waiting for a source:

```
plane standards list
plane standards pending
```

List the connection types (for example `CT-M3-SHCS-INSERT  mechanical  fastened  M3 SHCS into M3 brass heat-set insert`):

```
plane standards connections
```

Add `--kind <str>` to filter them (checked with `--help` only).

Rules:

- Fix the design, not the threshold.
- A source must be a knowledge entry you opened (see Knowledge below).
- A standards or connection-type change gets its own branch `std/<topic>`. It touches `standards/`, `tests/` and `knowledge/` only. It comes with a test that fails without it.
- A changed threshold can change gate results. In the PR, say which designs' baseline rows move. Check it locally:

```
plane baseline check --all --format md
```

It printed `**Result:** pass`. CI prints `# Baseline check` with unchanged, regressions and improvements per design.

### Knowledge

Make a new source entry from the template. Use [TEMPLATE-source.md](../knowledge/TEMPLATE-source.md). For a DIY project, use [TEMPLATE-diy-project.md](../knowledge/TEMPLATE-diy-project.md).

```
plane research new source <slug>
plane research new diy <slug>
```

They create `knowledge/sources/<slug>.md` and `knowledge/diy-projects/<slug>.md`. Fill in the fields, then check:

```
plane research check knowledge/sources/<slug>.md
```

On a fresh stub it prints `missing: title, authors, year, url, type, retrieved, verified, section:Summary, ...` and exits 1. When the entry is complete it prints nothing.

The fields are id, title, authors, year, url, type (paper, standard, regulation, textbook, website or video), retrieved and verified. The sections are Summary, Usable rules / numbers and How we could use it.

Cite only sources you opened. Set `verified: true` only if you read the relevant part.

Save an idea. It writes `knowledge/ideas/<date>-<slug>.md` and prints the path.

```
plane idea add "<title>" "<body>" <by>
```

### Imports

Code or data from other repos is adapted, never copied. Record each import in [PROVENANCE.md](../PROVENANCE.md) with the repo, commit and path.

## 8. Agents: the 10 roles

Read this to pick a role and launch it inside the rules. The full standard is [agents.md](../standards/agents.md).

The roles, with the model each one runs on:

- `conductor` (Opus): main-session role. Owns the plan, launches the others, and is the only one that declares a unit done.
- `advisor` (Opus): read-only. Asks "works, but is it what we meant?". Called after a unit fails twice.
- `tactician` (Sonnet): turns one unit into builder-ready briefs, and checks a finished unit against its spec.
- `builder` (Haiku): one easy brief.
- `builder-plus` (Sonnet): one hard brief.
- `scout` (Haiku): puts facts into the knowledge templates.
- `recon` (Sonnet): benchmarks 3 to 5 known approaches and returns a ranked recommendation.
- `design-engineer` (Sonnet): iterates a design with `plane` commands only and never edits code.
- `reviewer` (Opus): fresh for each wave. Scores against `standards/review-scorecard.md`.
- `auditor` (Haiku): read-only hourly check for open prompts, broken rules and stale ledger items.

Who gets the most from which role:

- Dillon: `design-engineer`, `recon`, `scout`.
- James: `tactician`, `builder`, `builder-plus`, `reviewer`.
- Vaibhav: `design-engineer` (for FEA), `scout`.

How to launch: ask your main Claude session. For example, "use the design-engineer to try three values of flight.cl_max". The main session starts the role. Role files live in `.claude/agents/*.md`. Do not edit them on a design or test branch (O6). The `conductor` is the main-thread role. Per O5 you do not run it. Tristan starts it with `claude --agent conductor`.

The agent gate stops a launch when:

- The role is not in the roster. You see `Agent "helper" is not in the hangar roster. Use one of: advisor, auditor, builder, builder-plus, conductor, design-engineer, recon, reviewer, scout, tactician. ...`
- The role is not named in backticks in an agent table of the newest plan (a table whose header has `Pass criterion`).
- A `builder` or `builder-plus` prompt is not builder-ready. You see `Brief for builder is not builder-ready: give a brief file ... or include exact outputs, exact inputs, a pass check and a stop rule`.

Builder-ready has four items:

1. Exact output: paths and format.
2. Exact inputs: nothing to "find".
3. A mechanical pass check: a command and the expected result.
4. A stop rule: report the blocker, do not improvise.

A brief file lives in `plans/<plan>/briefs/<unit>-<n>.md` and follows the template in [agents.md](../standards/agents.md).

Model rule: Haiku builds, hard work goes one tier up, and a unit that fails review twice goes to `advisor`. The clearer the goal, the cheaper the agent.

The plan, briefs, reviews and ledger:

- The plan is `plans/2026-11-20-standardization.md`. It holds the spec and the units (`### Unit U<n>.<m>`, with checkboxes).
- Briefs are in `plans/<plan>/briefs/`. Reviews are in `reviews/`.
- [PROGRESS.md](../PROGRESS.md) is generated from the plan, reviews and ledger. Do not edit it.

Check that it is current. If it is not, regenerate it (usually Tristan does this).

```
plane progress --check
plane progress --write
```

`--check` prints `PROGRESS.md is up to date`. For the project overview, see [ROADMAP.md](../ROADMAP.md) and [CLAUDE.md](../CLAUDE.md).

Agents avoid stepping on each other the way people do: one branch per topic, each in its own clone, touching only that branch type's folders (section 9). None of them edits the plan, `PROGRESS.md` or the ledger.

## 9. Branches, ownership, review and merge

Read this before you make your first branch. It is the core of the guide.

Everything in the numbered rules below is a proposed rule. Tristan confirms it (see "Team rules").

### What the repo does for you

- CI (`.github/workflows/validate.yml`) runs on every pull request, and on every push to `main` and to `std/**` only. It runs on `ubuntu-latest` and `windows-latest`, with Python 3.12.
- CI steps: install `".[mcp,dev]"`, run `pytest -q -n auto -m ""`, run `harness/ci/check_separation.py`, run `plane progress --check`, and run `plane baseline check --all --format md` against the base.
- The separation check works per commit, not per PR. No single commit may change both `designs/**` and `core/**`, unless its message has a line starting `migration:` or the PR has the `migration` label. A PR may hold a `designs/` commit and a `core/` commit if they are separate commits.
- When a PR changes only `plans/**`, `reviews/**`, `ledger/**` or `PROGRESS.md`, `progress.yml` runs `plane progress --check`.
- `pages.yml` publishes the viewer and weekly updates to GitHub Pages on every push to `main`.
- `plane design propose` makes branches named `design/<id>/<slug>`. Git cannot hold both `design/<id>` and `design/<id>/<slug>`. Never make a branch called just `design/<id>`.
- Each design has its own `baseline.json` and `CHANGELOG.yaml`. One design per branch means no overlap.
- These shared files conflict when two branches change them: `PROGRESS.md`, `ledger/items.yaml`, `updates/<week>/updates.yaml`, `docs/cli.md` and `plans/*.md`.
- The repo has no branch protection yet. Merge, squash and rebase are all allowed.
- The repo keeps only `main` (D47). Delete your branch when it is merged or abandoned.

### The rules

1. Branch names. `std/<unit-or-topic>` for tests, standards, knowledge, harness and core (CI runs on every push). `design/<id>/<slug>` for design changes (made by `plane design propose`; CI runs when the PR opens). With your name: `std/<person>-<topic>`.
2. One topic and one owner per branch. Branch from the latest `origin/main`:

```
git fetch origin
git switch -c <branch> origin/main
```

3. Stay in your folders:

| Branch type | May touch |
|---|---|
| `design/<id>/<slug>` | only `designs/<one id>/` |
| test branch | only `tests/` |
| standards branch | `standards/`, `knowledge/`, `tests/` |
| knowledge branch | `knowledge/` (and `PROVENANCE.md` for imports) |
| harness, core, schema | Tristan's, and James for harness install work. Never `designs/`. |

Nobody but Tristan edits `plans/`, `reviews/`, `ledger/`, `PROGRESS.md`, `.github/`, `.claude/`, `CLAUDE.md` or `ROADMAP.md`.

4. Sync by merging. Never force push. Never rebase a branch you have pushed.

```
git fetch origin
git merge origin/main
```

If `PROGRESS.md` or `docs/cli.md` conflicts, do not hand-merge. Regenerate them with `plane progress --write` and `plane docs cli --out docs/cli.md`.

5. Before you ask for review, check your work. For design branches, run `plane design validate designs/<id>`. Then run the tests (the targeted file, or the local suite). Then run the separation check, which exits 0 with no output when fine.

```
python harness/ci/check_separation.py --base origin/main
git status
git push -u origin <branch>
```

CI must be green on both operating systems.

6. Review and merge. Open a PR on GitHub from your branch to `main`. Design PRs need Dillon's OK (R25). Tests, standards and core PRs need Tristan's. Only Tristan merges (O3).
7. After the merge, delete the branch on GitHub and on your machine (D47):

```
git switch main
git pull
git branch -d <branch>
git push origin --delete <branch>
```

8. Commits are small and have one topic. Designs and core never go in the same commit. Message format: `<area>: <what> (<ledger id if any>)`. Every commit ends with Tristan's trailer `Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>`, plus any agent line (O8).
9. Work comes from ledger tasks (O4). Tristan sets the owner. Your branch and PR text name the ledger id. You do not edit the ledger. Tell Tristan, who closes the item with evidence.
10. Two people at once. Dillon works on `design/concept-a/<slug>` and touches only `designs/concept-a/`. James works on `std/james-drop-test-fixtures` and touches only `tests/`. They share no file, so both merge in any order. Neither touches the shared generated files (`PROGRESS.md`, `docs/cli.md`).

## 10. Ledger and weekly update

Read this to see project status and post your weekly update.

The ledger tracks tasks, rulings and decisions. Look at it:

```
plane ledger report
plane ledger check
```

`ledger report` prints counts per kind and status, then `## Overdue as of <date>`. `ledger check` prints `ledger check: no problems`. A `dropped` item never counts as overdue.

Only Tristan adds ledger items and closes them (O4, O11). He adds an item like this, for example:

```
plane ledger add task "Run drop test on my-test" --source "team guide check" --owner <person> --due 2026-12-01
```

It prints the new id (for example `T111`) and changes only `ledger/items.yaml`. If two branches both add an item, both get the same next id and conflict. That is why only Tristan adds them. To close one, Tristan uses `plane ledger set <item-id> <status> --evidence <text>` (statuses `open`, `done`, `dropped`, `superseded`, `decided`).

Your prompt log (`ledger/prompts.jsonl`) is separate. It is local and git-ignored (section 2).

### Weekly update

Create the week once (Tristan usually does), then add your entry on your branch `std/<person>-update-<week>`.

```
plane update new <week>
plane update add <week> <person> <link> "<changed>"
```

`update new` creates `updates/<week>/updates.yaml` (`week: '2026-11-30'`, `entries: []`). For example, `plane update add 2026-11-30 james https://example.com/pr/1 "Added drop test"` prints `{"count": 1}`. It adds or replaces your own entry, so run it again after a merge conflict. `plane update publish <week>` builds the page into `viewer/updates/<week>/index.html` (git-ignored). CI publishes merged weeks to GitHub Pages on every push to `main`.

## 11. Common problems

| Problem | What to do |
|---|---|
| `plane --version` shows an old version | An older `plane` is first on PATH. Call `.venv/Scripts/plane` or `.\.venv\Scripts\plane`. |
| `plane design set` exits 2 | The value or key is wrong. The message shows the schema path and allowed type. Your file is untouched. |
| `plane baseline check` exits 1 with `Missing baseline.json` | Run `plane baseline update designs/<id>` and commit the file (section 3). |
| CI separation check fails | Split the commit so `designs/` and `core/` are in separate commits. |
| `plane progress --check` fails | Run `plane progress --write` and commit (section 8). |
| `plane tools doctor` says OpenCAE is missing | This is Vaibhav's setup (section 4, FEA). Everyone else can ignore it. |
| The Stop hook blocks the session | Answer or defer the open prompt (section 2). |
| The agent gate blocks a launch | Use a role from the roster, and give a builder a builder-ready brief (section 8). |
| `git push` is denied | You are not a collaborator yet (O1). Ask Tristan. |
