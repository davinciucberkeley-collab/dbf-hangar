"""U4.41-4: every meshed library part is one watertight body centred on its envelope."""
from __future__ import annotations

from pathlib import Path

import trimesh
import yaml

from hangar.geom import registry

PARTS = Path(__file__).resolve().parents[1] / "knowledge" / "parts"


def meshed():
    for yml in sorted(PARTS.glob("*/part.yaml")):
        part = yaml.safe_load(yml.read_text(encoding="utf-8"))
        if (part.get("geometry") or {}).get("generator") == "mesh_file":
            file = part["geometry"]["params"]["file"]
            yield part["id"], part, yml.parent / file


def _tattu():
    for pid, part, path in meshed():
        if pid == "tattu-2300mah-4s-75c":
            return part, path
    raise AssertionError("tattu-2300mah-4s-75c not found")


def test_every_meshed_part_is_one_body_centred_on_its_envelope():
    failures = []
    for pid, part, path in meshed():
        m = trimesh.load(path, force="mesh")
        m.merge_vertices()
        bodies = m.split(only_watertight=False)
        if len(bodies) != 1:
            failures.append(f"{pid}: {len(bodies)} bodies")
        if not (m.is_watertight and m.is_volume):
            failures.append(f"{pid}: not a watertight volume")
        centre = (m.bounds[0] + m.bounds[1]) / 2.0
        if any(abs(c) > 0.05 for c in centre):
            failures.append(f"{pid}: centre {centre.round(3).tolist()} is off origin")
        for axis, (got, want) in enumerate(zip(m.extents, part["dimensions_mm"])):
            if abs(got - want) > 0.1:
                failures.append(f"{pid}: extent axis {axis} {got:.2f} != {want}")
    assert failures == []


def test_tattu_numbers():
    part, path = _tattu()
    m = trimesh.load(path, force="mesh")
    m.merge_vertices()
    assert abs(m.extents[0] - 37.0) <= 0.1
    assert abs(m.extents[1] - 106.7) <= 0.1
    assert abs(m.extents[2] - 36.2) <= 0.1
    assert abs(m.volume - 106353) <= 106353 * 1e-3
    assert part["mass_g"] == 270.0
    assert part["dimensions_mm"] == [37.0, 106.7, 36.2]


def test_cad_source_records_the_change():
    part, _ = _tattu()
    assert "lead stub removed" in part["cad_source"]


def test_library_loader_still_builds_it(tmp_path):
    comp = registry.build_component(
        {"id": "b", "geometry": {"generator": "library_part", "params": {"part": "tattu-2300mah-4s-75c"}}},
        tmp_path,
    )
    parts = comp if isinstance(comp, list) else [comp]
    assert len(parts) == 1
    mesh = parts[0]
    assert mesh.is_watertight
    assert abs(mesh.volume - 106353) <= 106353 * 1e-3
