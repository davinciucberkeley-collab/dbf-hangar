# Local CAD overlay for licensed part models

## 1. What it is and the licence rule

Some library parts have real CAD models on GrabCAD. Their licence (GrabCAD Terms of Use, section 6.2) allows
non-commercial, internal use only. They stay on team PCs: never commit, upload or publish the files, and never
publish anything built from them. The overlay swaps the geometry of a library part for the licensed model on this
machine only. Mass, BOM and `part.yaml` always come from the committed part. CI never has an overlay and behaves
exactly as before.

## 2. Where

The overlay folder is `C:/Users/trist/parts-cad` by default (`Path.home() / "parts-cad"`). Change it with the
environment variable `PLANE_CAD_OVERLAY=<folder>` or the git-ignored file `cad-overlay.local.json` in the repository
root: `{"path": "<folder>"}`. The value `off` (or an empty variable) disables the overlay. The variable beats the file.

## 3. Manifest

One folder per library part id, with an `overlay.yaml` next to the model: `<overlay>/<part id>/overlay.yaml`.

```
file: stl/model.stl     # required, relative to the part folder; .stl .obj .ply .off (.step/.stp only with cascadio)
licence: "..."          # required, non-empty text
units: mm               # mm (default) | m | in
matrix: [12 numbers]    # optional, 3x4 row-major, applied after units and before recentre
recentre: bbox          # bbox (default, bounding-box centre to the origin) | none
note: "..."             # optional
```

Rules: the mesh is merged and split into bodies, then united into one watertight solid; the overlay extents divided
by the committed `dimensions_mm` (the fit) must lie between 1/3 and 3 on every axis, otherwise the overlay is
`unusable` (check units and matrix).

## 4. The two manifests for the files that exist

The manifests live in the overlay folder, not in the repository. Tristan creates them.

`parts-cad/sunnysky-x2814-v3-900kv/overlay.yaml`

```
file: stl/EN-sunnysky-x2814-1.STL
licence: "GrabCAD Terms of Use 6.2, non-commercial internal use; https://grabcad.com/library/sunnysky-x2814-1000kv-1 (Mehmet Berkay), checked 2026-11-24"
units: mm
matrix: [0, 0, -1, 0, 1, 0, 0, 0, 0, -1, 0, 0]
recentre: bbox
note: "1000 kV geometry for the 900 kV part; shaft toward -x"
```

The STL axis z becomes the part x axis with the shaft toward -x (the body-frame nose side). Expected fit in
`parts show`: about `[1.5, 1.25, 1.25]` (the 54 mm includes the shaft; the committed envelope is 36 x 28 x 28).

`parts-cad/emax-es08maii-metal/overlay.yaml`

```
file: "EMAX ES08MA (Poluyan).STEP"      # or servo.stl, see section 5
licence: "GrabCAD Terms of Use 6.2, non-commercial internal use; https://grabcad.com/library/servo-emax-es08ma-1 (Alexander Poluyan), checked 2026-11-24"
units: mm
matrix: [0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0]
note: "ES08MA geometry (MAII proxy)"
```

The matrix is a first guess (extents 27.0 x 32.2 x 12.5 become 32.2 x 12.5 x 27.0 against the envelope
23 x 11.5 x 24). Adjust it until `plane parts show emax-es08maii-metal` shows a fit near 1 on all three axes and the
model looks right in Studio.

## 5. STEP files

STEP needs the optional `cascadio` package (`pip install cascadio`, extra `step` in pyproject; installed on this
machine since 2026-11-24). Without it a STEP file is `unusable` until it is installed or the servo is exported as STL (for example FreeCAD: select the body, File > Export > STL) to
`parts-cad/emax-es08maii-metal/servo.stl` and the manifest `file:` is changed to `servo.stl`. STEP models are
converted to millimetres automatically, so keep `units: mm`.

## 6. Check

`plane parts show <id>` prints `overlay: present | absent | unusable`, with file, licence and fit when present and
the reason when unusable.

## 7. Outputs stay local

Exports of a design that uses an overlay part (GLB, STL, MJCF, Studio data) refuse any path inside the repository
unless git ignores it (`viewer/data/`, `.studio/`); git itself is asked, and a tracked path is always refused.
Allowed outputs get a `LOCAL-ONLY-cad-overlay.txt` marker, and the index entry carries `local_only` (the part ids).
`plane build-index --out` for such a design must use a folder outside the repository or an ignored one.

## Baselines and FEA

Shared numbers never depend on one machine's licensed files. `plane baseline update`, `plane baseline check`, FEA runs and FEA hashes force the overlay off, so they give exactly the numbers CI gets. When an overlay is configured, the baseline commands print one line to stderr: `note: CAD overlay ignored here (baselines and FEA results never use licensed files)`.
