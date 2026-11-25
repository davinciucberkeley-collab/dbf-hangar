"""U13.5-4: an STL written by the importer reloads watertight even when the mesh holds coincident vertex pairs."""
import numpy as np
import pytest
import trimesh
from scipy.spatial import cKDTree

from hangar.importers import dbf as D


def _two_cubes():
    a = trimesh.creation.box(extents=(1, 1, 1))
    a.apply_translation((0.5, 0.5, 0.5))
    b = trimesh.creation.box(extents=(1, 1, 1))
    b.apply_translation((1.5, 1.5, 0.5))
    m = trimesh.util.concatenate([a, b])
    return trimesh.Trimesh(m.vertices, m.faces, process=False)


def test_two_cubes_touching_on_an_edge_reload_watertight(tmp_path):
    m = _two_cubes()
    assert m.is_watertight and m.is_volume
    D._write_stl(m, tmp_path / "x.stl")
    r = trimesh.load(tmp_path / "x.stl", force="mesh")
    assert r.is_watertight and r.is_volume
    assert r.volume == pytest.approx(2.0, abs=1e-3)
    assert len(r.faces) == len(m.faces)


def test_no_vertex_pair_is_left_coincident():
    c = D._canonical(_two_cubes())
    assert len(cKDTree(c.vertices).query_pairs(1e-6)) == 0
    assert abs(c.volume - 2.0) < 1e-3


def test_mesh_without_pairs_is_unchanged(tmp_path):
    box = trimesh.creation.box(extents=(1, 1, 1))
    c = D._canonical(box)
    corners = np.array([[x, y, z] for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)])
    assert np.array_equal(c.vertices[np.lexsort(c.vertices.T[::-1])], corners[np.lexsort(corners.T[::-1])])
    D._write_stl(box, tmp_path / "b.stl")
    assert (tmp_path / "b.stl").stat().st_size == 84 + 50 * 12
