# Team guide: working in dbf-hangar

This guide is for the three teammates, for example Dillon, James and Vaibhav. Each of you has your own Claude on your own machine. All of you work in one repo, `dbf-hangar`, each on your own branch, so nothing interferes.

You talk to Claude. Claude runs the tools. Read "The five rules", "Team rules" and "Pick your setup". Then jump to the task you need. The commands Claude runs are in the Appendix at the end.

## The five rules

1. One repo: `dbf-hangar`. No new repos, no forks for work. Everything lands on `main` after review.
2. Your own branch, one topic per branch. See "Branches, review and merge".
3. Designs are data. Change them with the `plane` tools, never by editing code. A commit changes `designs/` or `core/`, never both (unless its message has a line starting `migration:`).
4. Every threshold lives in `standards/*.yaml` with a source, or `pending`. Fix the design, not the threshold.
5. Use the `plane` tools (CLI or MCP) for every operation. Do not rewrite validation, mass, export or analysis yourself.

You talk to Claude; Claude runs the tools.

## Team rules (Tristan to confirm)

These rules are not final. Tristan confirms or edits them (decisions D63 and D64). Until then, follow them as written.

- O1 Access: Tristan asks the org owner to add the three of you as collaborators with write access. Until then you cannot push or open a PR.
- O2 No pushes to `main`: every change from you is a pull request (PR). The "push straight to `main`" rule (D30) is for Tristan and the conductor only.
- O3 Merging: Tristan merges everything, with a plain merge commit. Dillon must approve design PRs. James's review on test and standards PRs is advice only. Tristan is asked to turn on branch protection (CI must pass, one review) so nobody can push `main` by accident. The checks to require are the six `validate` jobs, `validate (ubuntu-latest, 1)` to `validate (ubuntu-latest, 3)` and `validate (windows-latest, 1)` to `validate (windows-latest, 3)`; do not require `progress`, which runs only when a PR changes `plans/`, `reviews/`, `ledger/` or `PROGRESS.md` (teammate PRs never do, rule O4), so a required check that never runs would block the merge. Keep the admin bypass on for Tristan and the conductor, whose direct pushes to `main` (D30) would otherwise be rejected.
- O4 Work comes from ledger tasks: Tristan gives you a task with your name on it. Put its id in your branch and PR text. You do not edit `plans/`, `ledger/`, `reviews/` or `PROGRESS.md`. Tristan closes the task. Your task is your unit of work: you never need a plan unit.
- O5 Agents: you do not run the `conductor`. Use `design-engineer`, `recon`, `scout` and plain Claude. For a builder, give it exact output, exact inputs, a pass check and a stop rule, or ask Tristan for a brief. `tactician` and `reviewer` are Tristan's; he may allow them for James if he confirms it.
- O6 Hooks: keep them on. If the Stop hook gets in the way, tell Claude to set `HANGAR_ALLOW_STOP=1`. Nobody edits `.claude/` or `harness/` on a topic branch (James may on a harness branch).
- O7 Branch names: `std/<topic>` for tests, standards, knowledge, harness and gates; `design/<id>/<slug>` for design changes. You may use `std/<person>-<topic>`.
- O8 Commit trailer: your commits keep your own git author. They also end with Tristan's `Co-authored-by` trailer (as `CLAUDE.md` says) plus the line Claude adds. Tristan may drop it for you.
- O9 `concept-a`: every change goes through `design_set` (or `plane design set`) and a PR. Dillon owns it. Tristan does not re-run the importer on it without telling Dillon. New concepts start from a template and belong to their author.
- O10 Python: 3.12 is recommended (CI uses it). 3.10 or later installs.
- O11 Ledger and weekly update: only Tristan adds ledger items. You add your weekly update once, on a branch `std/<person>-update-<week>` that touches only `updates/<week>/`, and re-run it after a conflict.
- O12 Gate work: a gate branch `std/gate-<name>` may touch `core/hangar/gates/`, `core/hangar/checks.py`, `standards/`, `knowledge/` and `tests/`. The `baseline.json` update is a second commit in the same PR, touching only `designs/*/baseline.json`. New gates start report-only. Tristan decides whether to also require the `migration` label, or to reword the `CLAUDE.md` sentence from "PR" to "commit". A teammate's gate work (D69) ends in a PR that Tristan reviews with a fresh reviewer agent before he merges; no plan unit is needed.
- O13 Desktop chat: Setup B is optional and is set up once with Tristan. If it does not work for you, use Setup A. The Desktop Code tab counts as Setup A only after its three "check on first run" items pass.

## 1. Pick your setup

Read this once, before you install anything.

| Setup | Good for | What you get | What you lack |
|---|---|---|---|
| A. Claude Code (terminal, VS Code, or the Claude Desktop app's Code tab with the Local environment) | Everything | `CLAUDE.md` rules, the 10 agents, hooks, git, tests, MCP | Nothing |
| B. Claude Desktop chat + plane MCP server | Design work only | The `plane` tools as chat tools | No shell, no git, no tests, no `CLAUDE.md`, no agents, no hooks |

Which task needs which setup:

- Design work: A or B.
- Gate work: A.
- Standards and connection types: A.
- Knowledge: A.
- FEA and simulation: A. FEA needs OpenCAE on that machine (`plane tools doctor` shows it). B can run read-only analyses, and `sim_drop` and `design_validate`, through MCP.
- Branches, review, ledger, weekly update: A.

If you are unsure, use A.

## 2. Setup A: Claude Code

Read this once on a new machine. You get a working `plane` in about 10 minutes.

You need Git, Git LFS (meshes are LFS files), Python 3.12 (see O10), Claude Code, the GitHub CLI `gh` logged in (for anyone who opens PRs) and GitHub access to the repo (see O1). On Windows, use Git Bash: PowerShell blocks the venv activation script by default. The Appendix has the commands for each step. Steps:

1. Clone the repo.
2. Make a virtual environment in it and turn it on.
3. Install the package with `".[mcp,dev]"`. It takes a few minutes.
4. Check `plane --version`. It must print `plane, version 1.0.0.dev0`. If not, an older `plane` is earlier on your PATH.
5. Tell git your name and email, before your first commit.
6. Run `plane tools doctor`. Only OpenCAE matters to the FEA person. `missing` is not an error for everyone else.
7. Run the quick test `python -m pytest -q tests/test_cli_doc.py`. About 2 seconds.

Then start Claude Code from the repo root (terminal: `claude` in the repo folder).

### The Desktop app's Code tab

Choose the environment **Local** and open the cloned `dbf-hangar` folder. It runs on your machine with direct file access. Not everything is confirmed for this tab, so do the three checks below. Each one is "check on first run".

- Check on first run (i): the session shows the line `hangar: roles in .claude/agents/ (launch only these); plan: plans/2026-11-20-standardization.md`. That means the start hook ran.
- Check on first run (ii): Claude knows the repo rules without being told. That means `CLAUDE.md` loaded. Ask it "what are the five rules of this repo?".
- Check on first run (iii): when you type a prompt, you see `Logged as P<n>`. That means the prompt hook ran.

If any check fails, use the terminal route (`claude` in the repo folder) and tell Tristan. Do not assume the Code tab works.

### What your session does by itself

Nothing needs installing in the clone. When you start Claude from the repo root, these are active:

- `.claude/settings.json` sets the output style `quiet` and wires four hooks.
- `.claude/agents/` holds the 10 roles.
- The hooks use your system Python (3.8 or newer). If none is found they exit quietly and never block you.

What you will see:

- Every prompt you type is logged. Claude is told to close it when it has answered. The log is `ledger/prompts.jsonl`. It is git-ignored. It stays on your machine and Tristan never sees it.
- Claude cannot stop while a prompt is open. You see `Open prompts in this session: P1`. Claude closes the prompt itself. If it keeps blocking, answer or defer the prompt. After 3 blocks in a row the stop is forced.
- Agent launches are checked by the agent gate (see "Agents").
- Answers are short: results, decisions, blockers. No narration.

### MCP in Claude Code (optional)

The CLI does everything MCP does. If you want the tools as chat tools, ask Claude to add the server, or see the Appendix. It is stored per user and per folder, not in the repo. See [mcp.md](mcp.md).

## 3. Setup B: Claude Desktop chat + plane MCP (set up once with Tristan; tell Tristan what breaks, not tested on a teammate machine)

Read this only if you want design work in the Desktop chat. Do it with Tristan, once.

Order of steps:

1. Install the package first: Setup A steps 1 to 4 (clone, venv, `".[mcp,dev]"`). The server is the `plane-mcp.exe` in that venv.
2. Open the config file. On Windows it is `%APPDATA%\Claude\claude_desktop_config.json`. On macOS it is `~/Library/Application Support/Claude/claude_desktop_config.json`. Open it from Settings > Developer > Edit Config. The newer layout is Settings > Desktop app > Extensions. If there is no Edit Config button, open the file by its path.
3. Add the server. On Windows, double every backslash. Replace `<you>` with your Windows user name. The `env` entry is only needed to open PRs: Desktop passes servers a limited environment, and `design_propose` needs `gh`. The path must match where `gh` is installed.

```json
{
  "mcpServers": {
    "dbf-hangar": {
      "command": "C:\\Users\\<you>\\dbf-hangar\\.venv\\Scripts\\plane-mcp.exe",
      "env": {
        "HANGAR_GH": "C:\\Program Files\\GitHub CLI\\gh.exe"
      }
    }
  }
}
```

On macOS the command is `/Users/<you>/dbf-hangar/.venv/bin/plane-mcp`. This was not tested in Desktop.

4. Fully quit and reopen Desktop. Closing the window is not enough. Do this after every change.
5. Check it connected: click "+" in the chat box, then Connectors, and hover the server to see its tools. Logs are in the Appendix. If some tools are missing, tell Tristan which. Tool names with a `-` in them (for example `ledger_import-dbf`) may be refused by Desktop. This is unverified.

### Which folder the server edits

The server finds the repo from where the package is installed, not from the folder it starts in. It edits the clone you installed it from. But the tools that take a design `path` use it as given. A relative path like `designs/example-tailsitter-wing` failed when tested from another folder. The absolute path worked. So always give the absolute design folder, for example `C:/Users/<you>/dbf-hangar/designs/<id>`. The Project text below says so. Tools that take a design id (`save_design`, `list_structural_parts`, `design_new` with `new_id`) are not affected.

### Permissions

Desktop asks before it uses a tool ("Allow once" or "Always allow"). Change it later on the connector page under Tool permissions. That the same menu applies to servers set up in the config file is presumed, not verified.

- Keep every write tool on "Needs approval": at least `design_set`, `design_new`, `design_copy`, `design_propose`, `design_migrate`, `save_design`, `fea_run`, `fea_setup`, `ledger_*`, `update_*`, `idea_add`, `research_new`.
- "Always allow" only readers: `design_get`, `design_validate`, `design_diff`, `design_sweep`, `design_mass`, `gate_*`, `claim_check`, `claim_explain`, `claim_list`, `bom_cost`, `bom_list`, `standards_*`, `tools_doctor`.

Never use `save_design` for edits. It writes the whole file and bypasses `design_set` and `CHANGELOG.yaml`. It checks only tier 0. Edits go through `design_set`.

### A Project for the team

A Claude Desktop Project holds custom instructions that apply to every chat in it. Make one Project, and paste this as its instructions (replace `<you>`). Upload nothing sensitive. Do not upload copies of the standards or schema: the server's `get_standards` and `get_schema` tools return the live ones.

```text
You are the design-engineer for the DBF team's repo, dbf-hangar.
Change designs only with design_set. Never use save_design.
Give a reason in `why` every time. Prefer subtract, then modify, then add.
Always pass absolute design paths: C:/Users/<you>/dbf-hangar/designs/<id>.
After any change run design_validate and report the failing and WARN rows.
Then run claim_check when the design has claims.
Never edit code, standards or thresholds. Fix the design, not the threshold.
Thresholds live in standards/ with a source or pending.
A commit changes designs/ or core/, never both.
To hand a change over, use design_propose with a short title.
It opens a PR. CI runs the tests. A person approves the merge.
Never say a change is merged.
Keep answers short: results, decisions needed, blockers.
If a tool errors twice, stop and ask.
```

Test it once: open a chat in the Project and check that the Connectors list shows the server. Whether connectors work inside a Project, and the size limits, are not confirmed.

### Limits of Setup B

- No tests run in the chat. CI runs them on the PR (the `validate` workflow, on Windows and Linux).
- No git. `design_propose` is the only way a change leaves your machine. It needs `gh` logged in, push access (O1) and uncommitted changes in that design folder. It also needs `git` and `gh` on the PATH that the Desktop-launched server sees. That is unverified: check it when you set up with Tristan.
- No baseline tool and no git in the chat. A design that needs a `baseline.json`, or an update to an open PR, must be finished in Setup A (or by Tristan). `design_propose` from Desktop always opens a new PR.
- It branches from the clone's current HEAD, so keep the clone on an up-to-date `main`.

## 4. Task: design work

Needs: setup A or B

Use this to make a design, change it, compare it and hand it over.

**Ask:**

> Make a new design from the tailsitter template.
>
> Set concept-a's battery mass to 290 g and check the gates.
>
> Try three values of `flight.cl_max` and show me the effect.
>
> Propose this change.

**Claude does:**

- Makes a design folder `designs/<id>/` with `plane.yaml` (written in PDL, see [pdl/README.md](pdl/README.md)) and a `CHANGELOG.yaml`. Tools: `design_new` (or `design_copy`).
- Changes one key at a time with `design_set` (CLI: `plane design set`). It always gives a reason, and the change goes into `CHANGELOG.yaml`.
- Re-checks with `design_validate` (tiers T0 to T9), then `claim_check` if the design has claims. Tries values with `design_sweep` (a scratch copy: your file is untouched). Compares with `design_diff`.
- Setup A only: if the design has known FAIL or SKIP rows, it records them with `plane baseline update`. A new design that is not fully accepted needs this, or CI fails. A full design takes about 3 minutes.
- On "Propose this change": uses `design_propose` (CLI: `plane design propose`). Do not commit first: propose commits for you. It needs uncommitted changes in that design folder. It makes the branch `design/<id>/<slug>` from your current HEAD, commits only that design folder, pushes and opens a PR. It does not merge. It needs `gh` logged in and push access (O1).

**Check the answer:**

- The reply shows the old and new value (`requirements.mtow_g: 900 -> 950`), the result of `design_validate` with failing and WARN rows named, and the PR link.
- A rejected value (wrong type or key) leaves the file untouched. Claude should say so and fix the value.
- Setup A only: after review feedback, do not open a second PR. Ask: "Update my open PR." Claude switches to the PR branch `design/<id>/<slug>`, makes the change, commits and pushes to the same branch.
- Red flags, stop and ask Tristan: Claude committed design edits on local `main`, edited a file by hand, used `save_design`, edited `designs/concept-a/plane.yaml` directly, touched `core/` in the same commit, or says a change is "merged" when only a PR is open.
- Not every key moves the numbers. `requirements.mtow_g` is a requirement, so sweeping it gives identical results. Use a key that drives the physics, such as `flight.cl_max`.
- Never update a baseline to hide a regression. Update it only when you fixed rows or created the design.

### Starting a new concept

- `concept-a` is the only active design (D9). Every other folder in `designs/` is a template, a reference or retired.
- A new concept needs a ledger task with your name on it (O4). Ask Tristan for it first; it names the concept and the mission it targets.
- The target mission is the VTOL demonstrator brief (D74): a 2 minute hover, 5 minutes of cruise (10 minutes is the goal), a 20 % reserve and a 0.25 kg growth allowance. It is in `knowledge/concepts/judging-mission-and-learning.md`. "DBF" in this repo means the DaVinci DBF capstone. UC Berkeley's separate DBF competition team and its rules are out of scope.
- A new design starts blank or from a template. Blank: `plane design new <new-id> --blank` makes `designs/<new-id>/plane.yaml` with one placeholder component `datum` and nothing else. Template: `plane design new <new-id> --template <template-id>` copies the template with its meshes and files (use it for a variant of an existing concept).
- Say it to Claude in plain words, for example: "Start a new design called X from a blank start: high wing, conventional tail, ~1.2 m span; use generators and library parts, validate, and propose a draft PR."
- Build a blank design with ops only. `plane generators list` and `plane generators show <name>` give each generator's parameters with units. `plane design add <path> components --value '{id: wing, type: wing, geometry: {generator: wing_panel, params: {airfoil_file: naca2412, span: 1200, root_chord: 200, tip_chord: 140, inboard_span: 100}}, position: [200, 0, 0], mass_g: 250, manufacturing: {method: foamboard}}' --why "main wing"` appends one component; the same op appends to `attachments` and `bom.items`. Then `plane design set <path> root --value <id> --why "..."` and `plane design set <path> "components[datum]" --kind remove --why "drop placeholder"`.
- Airfoils: `airfoil_file` takes a design-folder `.dat`, any NACA 4-digit name (`naca2412`, generated) or a name from `knowledge/airfoils/` (`s5010`). `wing_panel` takes `inboard_span` for a straight inboard section and a tapered outboard one. Real parts come from `plane parts list` (use them through the `library_part` generator and a BOM line).
- Many edits at once: `plane design apply <path> --edits <file.yaml> --why "..."` applies a YAML list in one step (one regeneration pass, one CHANGELOG entry; all or nothing). Each item has one verb key and, except `remove`, a `value` written as YAML data (not as a string): `- {set: "components[wing].mass_g", value: 250}` changes an existing scalar or an existing one-line list such as a position (`value: [212, 0, 0]`); `- {add: flight.air_density_kgm3, value: 1.2}` creates a new key (`add` only creates keys the schema allows and refuses keys that already exist; use `set` for those); `- {append: components, value: {id: probe, type: other, geometry: {point_mass: {}}, position: [10, 0, 0], mass_g: 2}}` adds one element to a list that already exists (a list that does not exist yet is created first with `add`; linkages need articulated joints plus horn, pushrod and pin parts, so follow the worked recipe in `docs/mechanisms.md`); `- {remove: "attachments[fc-mount]"}` deletes one element. Quote any key that contains `[`. An agent without a Write tool makes the file with a shell heredoc (`cat > edits.yaml <<'EOF' ... EOF`).
- A motor component needs a `propulsion` block or the schema refuses it: `propulsion: {max_thrust_n: 12, axis: [-1, 0, 0], role: cruise, max_current_a: 18, prop_diameter_mm: 254}`. `axis` is the direction of the thrust force on the aircraft (`[-1, 0, 0]` for a forward-thrusting tractor or pusher; `[0, 0, 1]` for hover lift); `role` is `lift`, `cruise` or `both`; `max_current_a` and `prop_diameter_mm` are optional but the thrust and T7 checks use them. Take the numbers from the motor datasheet and note the source; a number that is only an estimate stays labelled as an estimate.
- Component types: there is no `control_surface` type. Ailerons and flaps are `wing`, elevator and rudder are `tail_surface`, servos are `servo`, horns, rods and pins are `other`.
- Control surfaces that follow their wing: put the shared planform numbers in `parameters` (for example `span_mm`, `root_chord_mm`, `tip_chord_mm`, `sweep_deg`) and reference them as `"$span_mm"` in the wing and in every aileron, flap or elevon `wing_panel`; `plane design set <path> parameters.span_mm --value N --why ...` then regenerates all of them. Add `hinge_from: generator` to the hinge attachment of each such surface (`part: elevon`, side left or right) so its location, pivot and axis follow too (the typed values stay in the file as a placeholder). Limit: servo, arm, rod and horn parts and tail surfaces do not follow yet.
- Generating a whole concept from a prompt (G3 to G7, ledger T116 to T119) is still v1.1: today Claude builds the design with the steps above, one op per element, and validates with `plane design validate <path> --tier all`.

To look at a design, run `plane studio`: it serves the app on http://127.0.0.1:8765 (`--port` changes it, `--no-browser` keeps the browser closed), builds the designs it needs and caches them in `.studio/`, and lets you edit, validate and compare point and click on the same files. No `build-index` is needed for Studio.
`plane build-index --out viewer/data` is for the static copy of the viewer (the GitHub Pages build runs it): it exports every design under `designs/` (mesh, scorecard, mass) and writes `index.json`, and it took about 5 minutes for 11 designs on 2026-11-24. `viewer/data/` is a build output and is gitignored.
A new design shows up in Studio as soon as `designs/<id>/plane.yaml` exists. `plane design validate designs/<id> --tier all` prints the same scorecard without a browser.
For one design use `plane build-index --design <id> --out <folder>`; designs using the local CAD overlay must be built outside the repo or into a git-ignored folder (docs/cad-overlay.md); `plane design render <path> --out <file.png>` writes quick PNG views.

### Control surfaces and servos

A control surface only counts for tier 6 when a `mechanisms[]` entry joins its servo, arm, pushrod and horn. The recipe, the numbers T6 checks and the usual failures are in `docs/mechanisms.md`; its worked example is `tests/fixtures/mechanism-recipe/plane.yaml`. In short: servo just ahead of the hinge line; arm and horn from `plate`; pushrod from `strut`; the surface hinge and the servo arm are articulated attachments; the pushrod end at the arm is a `kinematic_link` attachment; the horn end is a small pin part joined to the horn; then one `mechanisms[]` entry with `link: {driver_end, follower_end}`. Add the parts with `plane design add`, read the real lever ratio from the `T6.ratio` message and write it as `expect`. A servo that no mechanism uses shows as `T6.servo_undriven.<id>` (WARN) on conventional fixed-wing designs.

## 5. Task: gate work

Needs: setup A

Use this to add or change a check that the validator runs. "Tests" for a design means these gates.

A finished gate has five parts:

1. The gate code. The checks live in `core/hangar/gates/*.py` and `core/hangar/checks.py`. The registry is `standards/gates.yaml`. `plane gate list` shows it.
2. Its threshold in `standards/*.yaml`, with a source or `pending`. A source must be a `knowledge/` entry that was opened.
3. A test that proves the gate catches a bad design (see `tests/test_gates.py` and `tests/test_discipline_gates.py`). The fixtures `mutate` and `example` in `tests/conftest.py` change a copy of the example design. The test must fail without the gate code.
4. The gate run on all designs. Every design that moves is named in the PR.
5. `baseline.json` updated for the designs whose known rows changed, in a separate commit that touches `designs/` only (O12).

**Ask:**

> Add a gate that checks every servo torque margin is at least 1.5x. Put the 1.5 in standards with a source or pending, add a test with a bad design, run it on all designs and tell me which designs change.

**Claude does:**

- Opens a branch `std/gate-<name>` from the latest `origin/main`.
- Adds the gate code, the threshold (with source or `pending`) and the test. New gates start report-only (`blocking: false` in `standards/gates.yaml`, like T7 and T8) until Tristan flips them.
- Runs the new test and checks that it fails without the gate. Runs `plane baseline check --all --format md`, which prints one block per design: known results, unchanged, regressions, improvements.
- Runs the local suite `python -m pytest -q -m "not slow" -n auto` before pushing (several minutes). Slow tests run in CI.
- Makes the `baseline.json` update as its own second commit. Pushes the branch and opens a PR. If a teammate does this work, Tristan runs a fresh reviewer agent on that PR before merging (D69); no plan unit is needed.

**Check the answer:**

- The PR names the threshold key and its source, the failing test name, and a table with one row per design.
- A gate that passes every design is suspect. Ask Claude to show the bad design it tested.
- A threshold with no source must say `pending`.
- The `designs/` commit must not contain `core/` files. If it does, ask Claude to split it.

## 6. Task: standards and connection types

Needs: setup A

Use this to look up, add or change a threshold or a connection type.

**Ask:**

> What is the source for the static margin limit?
>
> Show me every threshold that is still pending.
>
> Add the M4 heat-set insert as a connection type, with its source and a test.

**Claude does:**

- Reads with `plane standards show static_margin`, `plane standards list`, `plane standards pending` and `plane standards connections`. Thresholds live only in `standards/*.yaml` (`claims`, `connection-types`, `design-standards`, `gate-thresholds`, `gates`, `load-cases`, `manufacturing`, `operations`, `program`). Each has a `source:` or `source: pending`.
- Makes a branch `std/<topic>` that touches `standards/`, `knowledge/` and `tests/` only, with a test that fails without the change. The two checks `test_standards.py` and `test_standards_referenced.py` cover the files.
- Runs `plane baseline check --all --format md`, because a changed threshold can change gate results.
- Opens a PR that says which designs' baseline rows move.

**Check the answer:**

- A standards entry has `min` and `max`, or a `value`, then `rule`, `source` and `note`. Example (shortened) from `standards/design-standards.yaml`:

```text
static_margin:
  min: 0.05
  max: 0.15
  rule: Static margin ... for fixed-wing cruise.
  source: MIT 16.01 design rules; ... (knowledge/sources/std-mit-unified-desrules.md)
  note: ...
```

- A new key does nothing until a gate reads it, and gate code is core (see gate work, O12).
- Every new number has a source that points to an opened knowledge entry, or says `pending`.
- Claude fixed the design, not the threshold, when a design failed a gate.
- The PR lists which designs move.

## 7. Task: knowledge

Needs: setup A

Use this to add a source, a DIY project or an idea.

**Ask:**

> Add a source entry for this paper, and fill it in from the page.
>
> Save this idea: use a carbon spar on the tail boom.

**Claude does:**

- Creates the entry from a template with `plane research new source <slug>` ([TEMPLATE-source.md](../knowledge/TEMPLATE-source.md)) or `plane research new diy <slug>` ([TEMPLATE-diy-project.md](../knowledge/TEMPLATE-diy-project.md)).
- Fills in the fields (id, title, authors, year, url, type, retrieved, verified) and the sections (Summary, Usable rules / numbers, How we could use it).
- Runs `plane research check knowledge/sources/<slug>.md`. It prints nothing when the entry is complete.
- Saves an idea with `plane idea add`. It writes `knowledge/ideas/<date>-<slug>.md`.
- For code or data from another repo: adapts it, never copies it, and records it in [PROVENANCE.md](../PROVENANCE.md) with the repo, commit and path.

**Check the answer:**

- Claude cites only sources it opened. `verified: true` only if it read the relevant part.
- A missing field is listed by the check. Do not accept "done" while it lists any.
- An import has a `PROVENANCE.md` line.

## 8. Task: FEA and simulation

Needs: setup A (setup B can run read-only analyses and `sim_drop`)

Use this to check stress, drop loads and mass.

**Ask:**

> Run the stress check on the left spar plug (wng-004-l) of concept-a.
>
> Run the drop test on my-test and tell me which joint is closest to its limit.
>
> What is the mass and centre of gravity of concept-a?

**Claude does:**

- Shows the plan with `plane fea plan` (part, material, allowable, ultimate factor). Runs it with `plane fea run designs/<id> --part <part>`, or `--all`.
- Runs the drop test with `plane sim drop`. It prints the drop height, then one line per joint, such as `T2.sim_drop_loads PASS: wing-body: peak 82.6 N <= 125 N in drop test`.
- Reads mass, centre of gravity and inertia with `design_mass`. Exports a mesh with `design_export`.
- FEA needs OpenCAE, an outside tool (GPL-3.0). The repo does not contain it. Set it up once with `plane fea setup`: `--opencae-python` is the Python of the environment that has OpenCAE's libraries, and `--opencae-root` is the OpenCAE folder. After that, `plane tools doctor` shows `opencae ok`. Until it is installed, FEA results are SKIP with the fix, never a silent pass.
- Physics checks from OpenCAE's command line (mass, propulsion, structure, flight, whole-aircraft CFD) need a clone of OpenCAEModel main (GPL-3.0, an outside tool; the repo does not contain it) and Python 3.11+ with its libraries. Set it up once with `plane opencae setup --cli-python <python> --cli-root <clone folder>`, then run `plane opencae run <design> --analyses mass,propulsion`. Results are stored in `designs/<id>/opencae/results.json` and shown as `T2.opencae_*` rows. A missing clone, solver (CalculiX for structure; OpenFOAM or SU2 for CFD) or result is SKIP with the fix command, never a pass. `opencae setup su2 --yes` (about 40 MB download) is run by a person, never by an agent.

**Check the answer:**

- A result is PASS or FAIL with a number and a limit. SKIP means the tool is missing: install OpenCAE, do not accept it as a pass.
- Claude names the part, the material and the load case it used.
- If OpenCAE is missing, Claude says how to fix it and does not guess a number.

## 9. Agents

Read this to choose a role. The full standard is [agents.md](../standards/agents.md).

Ask Claude: "use the design-engineer to ..." or "use the recon to compare 3 approaches". The main session starts the role.

A session may launch only the roles in the agent table of the newest plan. Tristan maintains that table. The read-only built-in subagents `Explore`, `Plan` and `claude-code-guide` are allowed by exact name; Write, Edit and NotebookEdit are refused inside any agent with those names (D69). Every other built-in is refused, for example `general-purpose` and `claude`, because they are not in the table.

| Role | Model | What it does |
|---|---|---|
| `conductor` | Opus | Main-session role. Owns the plan, launches the others, declares a unit done. Tristan only (O5). |
| `advisor` | Opus | Read-only. Asks "works, but is it what we meant?". Called after a unit fails twice. |
| `tactician` | Sonnet | Turns one unit into builder-ready briefs, and checks a finished unit. Tristan's (O5). |
| `builder` | Haiku | One easy brief. Only with a builder-ready prompt. |
| `builder-plus` | Sonnet | One hard brief. Only with a builder-ready prompt. |
| `scout` | Haiku | Puts facts into the knowledge templates. |
| `recon` | Sonnet | Benchmarks 3 to 5 known approaches, returns a ranked recommendation. |
| `design-engineer` | Sonnet | Iterates a design with `plane` commands only, never edits code. |
| `reviewer` | Opus | Fresh for each wave. Scores against `standards/review-scorecard.md`. Tristan's (O5). |
| `auditor` | Haiku | Read-only hourly check for open prompts, broken rules, stale ledger items. |

For you (O5): `design-engineer`, `recon`, `scout`, and plain sessions. A builder only with a builder-ready prompt. The read-only built-ins `Explore`, `Plan` and `claude-code-guide` need no table row.

The agent gate refuses a launch when:

- The role is not in the roster. You see `Agent "helper" is not in the hangar roster. Use one of: ...`
- The role is not in the active plan's agent table. You see `Agent "<role>" is not in the active plan's agent table (plans/2026-11-20-standardization.md). Add it to the table first.` Ask Tristan.
- A `builder` or `builder-plus` prompt is not builder-ready: it lacks exact output, exact inputs, a mechanical pass check (a command and the expected result) or a stop rule. A brief file lives in `plans/<plan>/briefs/<unit>-<n>.md`.

Haiku builds, hard work goes one tier up, and a unit that fails review twice goes to `advisor`.

The plan is `plans/2026-11-20-standardization.md`. Finished units are archived in `plans/2026-11-20-standardization/archive.md`. [PROGRESS.md](../PROGRESS.md) is generated from both. Do not edit any of them. See also [ROADMAP.md](../ROADMAP.md) and [CLAUDE.md](../CLAUDE.md).

## 10. Branches, review and merge

Read this before your first branch. It is the core of the guide. In Setup A, "Open a branch for this, commit it, push it, open the PR" is a normal ask.

### What the repo does for you

- CI runs on every pull request, and on every push to `main` and to `std/**` only. It runs on Windows and Linux with Python 3.12.
- CI runs the whole test suite, the separation check, `plane progress --check` and `plane baseline check --all` against the base.
- The separation check is per commit, not per PR. No single commit may change both `designs/**` and `core/**`, unless its message has a line starting `migration:` or the PR has the `migration` label. A PR may hold a `designs/` commit and a `core/` commit if they are separate commits.
- `design_propose` makes branches named `design/<id>/<slug>`. Git cannot hold both `design/<id>` and `design/<id>/<slug>`. Never make a branch called just `design/<id>`.
- Each design has its own `baseline.json` and `CHANGELOG.yaml`. One design per branch means no overlap.
- These shared files conflict when two branches change them: `PROGRESS.md`, `ledger/items.yaml`, `updates/<week>/updates.yaml`, `docs/cli.md` and `plans/*.md`.
- The repo has no branch protection yet. The repo keeps only `main` (D47): delete your branch when it is merged or abandoned.

### The rules

1. Branch names: `std/<unit-or-topic>` (CI runs on every push) or `design/<id>/<slug>` (CI runs when the PR opens). With your name: `std/<person>-<topic>`.
2. One topic and one owner per branch. Branch from the latest `origin/main`. Never commit design edits on local `main`: branch first. The first push uses `-u`, so the branch tracks itself, not `origin/main`.
3. Stay in your folders:

| Branch type | May touch |
|---|---|
| `design/<id>/<slug>` | only `designs/<one id>/` |
| test branch | only `tests/` |
| standards branch | `standards/`, `knowledge/`, `tests/` |
| knowledge branch | `knowledge/` (and `PROVENANCE.md` for imports) |
| gate branch `std/gate-<name>` (O12) | `core/hangar/gates/`, `core/hangar/checks.py`, `standards/`, `knowledge/`, `tests/`; then a second commit with `designs/*/baseline.json` only |
| weekly-update branch `std/<person>-update-<week>` | only `updates/<week>/` |
| harness, core, schema | Tristan's, and James for harness install work. Never `designs/`. |

Nobody but Tristan edits `plans/`, `reviews/`, `ledger/`, `PROGRESS.md`, `.github/`, `.claude/`, `CLAUDE.md` or `ROADMAP.md`.

4. Sync by merging `origin/main` into your branch. Never force push. Never rebase a branch you have pushed. If `PROGRESS.md` or `docs/cli.md` conflicts, do not hand-merge. Regenerate them.
5. If you commit by hand instead of using `design_propose`, branch first (rule 2), then add and commit. Before you ask for review: validate the design (design branches), run the tests, run the separation check, push. CI must be green on both operating systems.
6. Review and merge: open a PR from your branch to `main`. Design PRs need Dillon's OK (R25). Tests, standards, gate and core PRs need Tristan's. Only Tristan merges (O3).
7. After the merge, delete the branch on GitHub and on your machine (D47).
8. Commits are small and have one topic. Message format: `<area>: <what> (<ledger id if any>)`. Every commit ends with Tristan's trailer `Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>`, plus any agent line (O8).
9. Work comes from ledger tasks (O4). Your branch and PR text name the ledger id. You do not edit the ledger. Tell Tristan, who closes the item with evidence. A text or docs fix of under about 20 lines that touches no code, hook, workflow, schema or threshold takes the light path (D66, [agents.md](../standards/agents.md)): one builder and one reviewer glance, with no brief and no tactician. A data-only design change (`plane design set`) needs CI green and Dillon's approval, with no reviewer agent, and touches no code, hook, workflow, schema or threshold. Full path (D69): anything touching gates, the bench, security or schema, or over about 20 lines, is built on your branch with your own tests and ends in a PR; Tristan runs a fresh reviewer agent on the PR before merging. You need no plan unit.

## 11. Ledger and weekly update

Needs: setup A

Read this to see project status and post your weekly update.

**Ask:**

> Show me what is overdue.
>
> Add my update for this week.

**Claude does:**

- Reads the ledger with `plane ledger report` (counts per kind and status, then the overdue list) and `plane ledger check`. A `dropped` item never counts as overdue.
- For the weekly update: creates your entry with `plane update add`. It adds or replaces your own entry, so it is safe to run again after a merge conflict. It does this on a branch `std/<person>-update-<week>` and opens a PR.
- Does not add or close ledger items. Only Tristan does (O4, O11): two branches that both add an item get the same next id and conflict.

**Check the answer:**

- The update has your name, a link to your PR and one line saying what changed.
- Claude did not touch `ledger/items.yaml`.

Your prompt log (`ledger/prompts.jsonl`) is separate. It is local and git-ignored. CI publishes merged weeks to GitHub Pages on every push to `main`.

## Appendix: what Claude runs, and what to do if something breaks

All commands are listed in [cli.md](cli.md). Placeholders like `<id>` are yours.

### A. Install and check (Setup A)

Clone and go in.

```
git clone https://github.com/davinciucberkeley-collab/dbf-hangar.git
cd dbf-hangar
```

Check Git LFS is installed.

```
git lfs version
```

Make and turn on the virtual environment. Git Bash:

```
python -m venv .venv
source .venv/Scripts/activate
```

PowerShell (only if you cannot use Git Bash; if it refuses to run the script, ask Tristan or James):

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install, then check the version.

```
python -m pip install -e ".[mcp,dev]"
plane --version
```

If `plane --version` is wrong, call `.venv/Scripts/plane` (Git Bash) or `.\.venv\Scripts\plane` (PowerShell) instead.

Tell git who you are.

```
git config user.name "<your name>"
git config user.email "<your email>"
```

Check tools and designs.

```
plane tools doctor
plane list
```

```text
opencae      missing  OpenCAE not found; run: plane fea setup --opencae-python <python of the environment with OpenCAE's libraries> --opencae-root <OpenCAE folder>
mujoco       ok       mujoco 4.0.1
aerosandbox  missing  aerosandbox not installed; run: python -m pip install aerosandbox
blender      planned  planned, not implemented in v1.0 (optional collision/transport check, will use Blender 4.5); nothing to run yet
sitl         planned  planned, not implemented in v1.0 (ArduPilot SITL flight-case plant, report-only)
davinci      missing  DaVinci API access not configured (D3 decided: skip until real calls after Dec 1); fix: configure access when that work starts
```

`plane list` prints one row per design: `id name status lift vtol_method`.

Tests. The quick check, one file without the parallel plugin (for debugging one test), and the local suite (several minutes; the pass count changes as tests are added). CI also runs the slow tests.

```
python -m pytest -q tests/test_cli_doc.py
python -m pytest -q -p no:xdist tests/test_cli_doc.py
python -m pytest -q -m "not slow" -n auto
```

MCP in Claude Code (optional). Run from the repo root with the venv active. It prints `Added stdio MCP server dbf-hangar with command: plane-mcp  to local config`.

```
claude mcp add dbf-hangar -- plane-mcp
claude mcp list
claude mcp remove dbf-hangar
```

### B. The command behind each task

Design work. Make, copy, validate:

```
plane design new my-test --template example-tailsitter-wing
plane design new <new-id> --template <template-id>
plane design copy designs/<src> <new-id>
plane design validate designs/<id>
```


Read, change, sweep and compare:

```
plane design get designs/my-test --key requirements
plane design set designs/my-test requirements.mtow_g --value 950 --why "try a lighter airframe"
plane design set designs/my-test authors --append Dillon --why "credit"
plane design set designs/my-test authors --remove "platform bootstrap" --why "tidy"
plane design set designs/my-test flight.cl_max --value 1.3 --also requirements.budget_usd=300 --why "two keys"
plane design sweep designs/my-test flight.cl_max --values 1.0 --values 1.2 --values 1.4
plane design diff designs/my-test designs/example-tailsitter-wing
```

```text
{"mtow_g": 900, "stall_speed_max_mps": 9, "cruise_speed_mps": 14, "budget_usd": 250}
requirements.mtow_g: 900 -> 950
authors: ['platform bootstrap'] -> ['platform bootstrap', 'Dillon']
authors: ['platform bootstrap', 'Dillon'] -> ['Dillon']
flight.cl_max: 1.0 -> 1.3
requirements.budget_usd: 250 -> 300
1.0: accepted=True mass_g=759.0 static_margin=0.1404 stall_speed_mps=7.79 hover_tw=2.418 failures=[]
1.2: accepted=True mass_g=759.0 static_margin=0.1404 stall_speed_mps=7.12 hover_tw=2.418 failures=[]
1.4: accepted=True mass_g=759.0 static_margin=0.1404 stall_speed_mps=6.59 hover_tw=2.418 failures=[]
requirements.mtow_g: 950 -> 900   (example; the real diff prints one line per differing key, several for a fresh copy)
```

A bad value or key exits 2 and leaves the file untouched:

```text
plane: requirements.mtow_g: 'abc' is not of type 'number' (data path requirements/mtow_g; schema path ...; allowed type number)
plane: no.such.key: no key 'no' (have: ['attachments', 'authors', 'components', ...])
```

`--why` is required. `--kind` is `add`, `subtract`, `modify` (default) or `remove`. Give `--values` once per value. `--append` and `--remove` work only on one-line `[list]` values.

Baselines. An accepted design needs none (`Accepted. No baseline needed.`). A design with known FAIL or SKIP rows needs one, or CI fails.

```
plane baseline check designs/<id>
plane baseline update designs/<id>
```

```text
**Missing baseline.json.** Run "plane baseline update designs/ca-x" and commit it.
```

Manual route only (the normal route is `propose`, which commits for you; do not commit first). Make the branch first (see Branches below), then commit. The commit touches nothing under `core/`:

```
git add designs/<id>
git commit -m "<message>"
```

Propose (no commit first). It was not run for this guide, because it pushes to the real remote. It needs `gh` logged in and push access. It creates `design/<id>/<slug>`, commits only that design folder, pushes, opens a PR and prints the URL.

```
plane design propose designs/<id> "<title>"
```

Gates and claims:

```
plane gate list
plane gate explain T3.endurance --design designs/<id>
plane claim list designs/concept-a
plane claim check designs/concept-a
plane claim explain designs/concept-a CL-A-CG
plane bom list designs/concept-a
plane bom cost designs/concept-a
plane baseline check --all --format md
```

```text
T0 T0.schema          blocking     schema/plane.schema.json
... (example rows; the real list is longer)
T7 T7.integration     report-only  gate-thresholds.yaml#wire_clearance_mm
T8 T8.sourcing        report-only  gate-thresholds.yaml#bom_verified_max_age_days
T9 T9.claims          blocking     claims.yaml#recompute_rel_tol
```

Standards:

```
plane standards show static_margin
plane standards list
plane standards pending
plane standards connections
```

Knowledge:

```
plane research new source <slug>
plane research new diy <slug>
plane research check knowledge/sources/<slug>.md
plane idea add "<title>" "<body>" <by>
```

On a fresh stub the check prints `missing: title, authors, year, url, type, retrieved, verified, section:Summary, ...` and exits 1.

FEA, simulation, mass, export, migration:

```
plane fea plan designs/concept-a wng-004-l
plane sim drop designs/<id>
plane design mass designs/<id>
plane design export designs/<id> --format glb --out <file>
plane design migrate designs/<id>
```

`plane fea setup --opencae-python <path> --opencae-root <path>` saves where OpenCAE is, once, in `opencae.local.json` (git-ignored). `plane fea run designs/<id> --part <part>` runs it. Both were checked with `--help` only. `design migrate` is a dry run: add `--write` to apply it.

Branches. Start, sync, check, push, clean up:

```
git fetch origin
git switch -c <branch> origin/main
git merge origin/main
python harness/ci/check_separation.py --base origin/main
git status
git push -u origin <branch>
```

After the merge:

```
git switch main
git pull
git branch -d <branch>
git push origin --delete <branch>
```

If `PROGRESS.md` conflicts, regenerate it (and check it is current):

```
plane progress --write
plane progress --check
```

Ledger and weekly update:

```
plane ledger report
plane ledger check
plane update new <week>
plane update add <week> <person> <link> "<changed>"
```

For example, `plane update add 2026-11-30 james https://example.com/pr/1 "Added drop test"` prints `{"count": 1}`. Only Tristan adds ledger items, for example:

```
plane ledger add task "Run drop test on my-test" --source "team guide check" --owner <person> --due 2026-12-01
```

### C. Common problems

| Problem | What to do |
|---|---|
| `plane --version` shows an old version | An older `plane` is first on PATH. Call `.venv/Scripts/plane` or `.\.venv\Scripts\plane`. |
| A `plane design set` is refused (exit 2) | The value or key is wrong. The message shows the allowed type. Your file is untouched. |
| `Missing baseline.json` (exit 1) | Run `plane baseline update designs/<id>` and commit the file. |
| CI separation check fails | Split the commit so `designs/` and `core/` are in separate commits. |
| `plane progress --check` fails | Run `plane progress --write` and commit. |
| `plane tools doctor` says OpenCAE is missing | Install OpenCAE (FEA person only). Everyone else can ignore it. |
| The Stop hook blocks the session | Answer or defer the open prompt. |
| The agent gate blocks a launch | Use a role from the plan's agent table, and give a builder a builder-ready brief. For `Agent "<role>" is not in the active plan's agent table (plans/2026-11-20-standardization.md). Add it to the table first.`, ask Tristan. The read-only built-ins `Explore`, `Plan` and `claude-code-guide` are allowed by exact name, and Write, Edit and NotebookEdit are refused inside them (D69); every other built-in, such as `general-purpose` or `claude`, is refused. |
| `git push` is denied | You are not a collaborator yet (O1). Ask Tristan. |
| Desktop shows no `dbf-hangar` tools | Fully quit and reopen Desktop. Check the config path and the doubled backslashes. Read the logs below. Tell Tristan which tools are missing. |

### D. Claude Desktop config and log locations

| What | Windows | macOS |
|---|---|---|
| Config file | `%APPDATA%\Claude\claude_desktop_config.json` | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Logs folder | `%APPDATA%\Claude\logs` | `~/Library/Logs/Claude` |
| Connection events | `mcp.log` | `mcp.log` |
| Server errors | `mcp-server-dbf-hangar.log` | `mcp-server-dbf-hangar.log` |
