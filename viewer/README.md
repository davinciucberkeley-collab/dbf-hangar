# Viewer

Static site that displays every design in `designs/` with no per-design HTML. It only reads generated data.

```
plane build-index --out viewer/data
python3 -m http.server -d viewer      # http://localhost:8000
```

`viewer/data/` is a build output (gitignored). Adding a design means adding `designs/<name>/plane.yaml` and re-running `build-index`; the viewer picks it up.

## Data contract (`data/`)
- `index.json` (v2): `{version: 2, generated_at, designs, scorecards, mechanisms, ledger, updates}`. Each design is `{id, name, status, morphology, accepted, mass_g, cg_mm, glb, scorecard, mass, mechanisms, fea, tiers:{"0":"PASS",...}, error}`; a non-null `error` is shown in place of the model. `scorecards` and `mechanisms` map design id to file; `ledger` holds only `id, kind, status, owner, summary, due, decided_in` in the Pages build (the repo is public); `updates` is `[{week, entries:[{person, link, changed}]}]`, newest first. Only the Studio index has `"studio": true`.
- `<id>.mechanisms.json`: per-mechanism sweep steps (`input_deg`, `followers`, `transforms` = component id to 16 numbers, row-major body frame, mm) for Physics mode. Designs with articulations but no `mechanisms` block get one `sweep-<joint>` pseudo-mechanism per joint.
- `<id>.fea.json`: per printed part stress-check result (`status`, `up_to_date`, `worst`) for Stress mode.
- `<id>.glb`: metres, y-up, one named node per component (node name = component id).
- `<id>.scorecard.json`: `{design_id, accepted, tiers:[{tier, name, status, results:[{check_id, status, message, criterion, data}]}]}`. A result whose `data.pair` is two component ids highlights both on click.
- `<id>.mass.json`: `{mass_g, cg_mm, inertia_gmm2, per_component:[{id, mass_g, cg_mm}]}`.

## Features
One app, Plane Studio, with six modes (tabs): Designs (3D view with click-to-highlight, CG marker, scorecard with FAIL rows first), Compare (two viewports plus table of mass, CG, tiers and key numbers), Physics (replays a mechanism sweep on the real parts), Stress (per-part stress-check results; replaces the OpenCAE dashboard), Updates (weekly updates) and Ledger (filterable). Sidebar with text and VTOL-method filters. Deep links: `#m=<mode>&d=<id>` or `#m=compare&a=<id>&b=<id>` (`#d=<id>` and `#a=<id>&b=<id>` still work). Each mode is `modes/<id>.js`; shared helpers are in `lib.js`.

`plane studio` serves this same page from your computer; `index.json` then has `"studio": true`, which loads `modes/edit.js` (new, copy, edit, import, check, stress run, download) through a local API. The GitHub Pages copy is the same app without it: no element with `data-edit` exists there.

three.js 0.160.0 loads from cdn.jsdelivr.net, so the page needs network access. Deployed by `.github/workflows/pages.yml`.
