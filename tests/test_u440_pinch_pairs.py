"""U4.40-3: exactly coincident vertex pairs left by _separate_pinches must not be welded by _clean."""
import json
from pathlib import Path

import numpy as np
import pytest
import trimesh
from scipy.spatial import cKDTree

from hangar.importers import dbf_geometry as geo

REPO_ROOT = Path(__file__).resolve().parents[1]


def _comp():
    with open(REPO_ROOT / "tests/fixtures/dbf-xmount-comp.json") as fh:
        return json.load(fh)


def test_xmount_fixture_rebuilds_closed():
    mesh, info = geo.part_mesh(_comp())
    assert geo._closed(mesh)
    assert info["bodies"] == 7
    assert mesh.volume == pytest.approx(1657.559, rel=1e-4)


def test_union_has_no_coincident_vertices():
    comp = _comp()
    placed = [geo._place(geo.body_mesh(b), comp["matrix"]) for b in comp["bodies"]]
    u = geo._boolean("union", placed)
    assert cKDTree(u.vertices).query_pairs(1e-6) == set()


def test_separate_pinches_is_identity_without_pairs():
    cube = trimesh.creation.box((1, 1, 1))
    v, f = cube.vertices, cube.faces
    assert np.array_equal(geo._separate_pinches(v, f), v)


def test_separate_pinches_moves_one_vertex_per_coincident_pair():
    a = trimesh.creation.box((1, 1, 1))
    a.apply_translation((0.5, 0.5, 0.5))
    b = trimesh.creation.box((1, 1, 1))
    b.apply_translation((1.5, 1.5, 0.5))
    m = trimesh.util.concatenate([a, b])
    m = trimesh.Trimesh(m.vertices, m.faces, process=False)
    out = geo._separate_pinches(m.vertices, m.faces)
    assert cKDTree(out).query_pairs(1e-6) == set()
    assert np.linalg.norm(out - m.vertices, axis=1).max() <= 2 * geo.PINCH_MM + 1e-12
