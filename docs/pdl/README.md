# Plane Design Language (PDL)

## What a plane is

A plane is a folder `designs/<id>/` holding a `plane.yaml`. The language is
PDL; the file name stays `plane.yaml` (decision D1). Units are fixed: mm, g, N,
deg, s. Every field is listed in [reference.md](reference.md), which is
generated from `schema/plane.schema.json`; do not edit it by hand.

## A minimal file

The header names the design and its schema version:

<!-- excerpt: designs/concept-a/plane.yaml -->
```yaml
schema_version: "0.4"
id: concept-a
name: Concept A, scaled quad tailsitter flying wing (D-182)
authors: ["UC Berkeley DBF capstone team (source repo dbf-combined)", "imported for aircraft-platform by `plane import dbf`"]
status: designed
```

The requirements block holds the numbers the checks compare against:

<!-- excerpt: designs/concept-a/plane.yaml -->
```yaml
requirements:
  mtow_g: 1470              # params-A.json req.mass_gate_kg 1.47 kg (A-P1 weigh-in gate)
  cruise_speed_mps: 17        # params-A.json mission.cruise_ms
  stall_speed_max_mps: 13.08    # params-A.json mission.cruise_ms 17 / req.cruise_ratio 1.3 (A-P6: 1.3 Vs < cruise)
  budget_usd: 2           # params-A.json req.budget_usd
```

A component has an id, a type, geometry, a position and a mass:

<!-- excerpt: designs/concept-a/plane.yaml -->
```yaml
  - id: avn-001
    type: structure
    description: "Avionics plate"
    geometry: {mesh: {file: meshes/avn-001.stl}}
    position: [0, 0, 0]
    mass_g: 8
    material: "PETG (printed)"
    manufacturing: {method: 3d-print-fdm, machine: "jacobs-fdm"}
```

## The v1.0 blocks

All are optional; they need `schema_version: "1.0"`.

- `files`: CAD (`step`, `f3d`, `stl`, `glb`; source or derived), drawings and photos, by relative path.
- `bom`: bill of materials lines with part number, supplier, url, qty, cost and a `verified` stamp.
- `wiring`: harnesses between components, with route, gauge and an `exposed_ok` reason.
- `mechanisms`: pull-this-moves-that checks between attachments (driver, driven, expected ratios).
- `transport`: disassembly groups; `requirements.transport_box_mm` is the transport box size.
- `assembly`: ordered steps naming the components added, with tool and note.
- `components[].provenance`: where a mass or geometry number came from.

`CHANGELOG.yaml` is a separate file written by `design.set` (unit U1.4); it is not part of `plane.yaml`.

## Versions

| Version | Adds |
|---|---|
| 0.1 | The base: components, attachments, requirements, flight, materials. |
| 0.2 | Attachment articulation; `flight.hover_pose` and `flight.cruise_pose`. |
| 0.3 | `component.cavities`. |
| 0.4 | `point_mass` geometry, `attachment.kinematic_link`, `attachment.rating_basis`, `component.planform`. |
| 1.0 | The blocks above and `requirements.transport_box_mm`. |

## Move an old file to 1.0

`plane design migrate designs/<id>` shows what would change. Add `--write` to
change only the `schema_version` line; every other byte stays. Old versions
stay valid, so migrating is optional.

## Rules of thumb

- Dates are quoted strings, for example `"2026-11-20"`.
- File paths are relative to the design folder, with forward slashes.
- Every id is a lowercase slug (`^[a-z0-9][a-z0-9_-]*$`).
