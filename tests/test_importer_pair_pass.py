"""U13.7 (T148 C2): the coincident-pair pass is a parameter, not a module flag; part_mesh output is unchanged."""
import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import trimesh

from hangar.importers import dbf_geometry as geo

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixtures/dbf-xmount-comp.json"


def _split_cube():
    """A closed cube whose faces own their vertices (24 vertices, 8 coincident groups): reloads closed once welded."""
    c = trimesh.creation.box((1, 1, 1))
    tri = c.vertices[c.faces]
    return tri.reshape(-1, 3).astype(float), np.arange(len(c.faces) * 3).reshape(-1, 3)


def test_flag_is_gone():
    assert not hasattr(geo, "_PAIR_PASS")


def test_signatures():
    for fn in (geo._separate_pinches, geo._from_manifold, geo._boolean, geo._part_mesh):
        p = inspect.signature(fn).parameters.get("pair_pass")
        assert p is not None, fn.__name__
        assert p.default is True, fn.__name__


def test_pair_pass_false_skips_the_second_pass():
    v, f = _split_cube()
    off = geo._separate_pinches(v, f, pair_pass=False)
    on = geo._separate_pinches(v, f, pair_pass=True)
    assert off.shape == v.shape and on.shape == v.shape

    # two coincident vertices at the origin whose faces pull in opposite directions (zero move direction), so the
    # first pass leaves them coincident and only the second pass separates them
    pts = np.array([(0, 0, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0),
                    (0, 0, 0), (10, 0, 0), (0, 10, 0), (-10, 0, 0), (0, -10, 0)], dtype=float)
    fac = np.array([(0, 1, 2), (0, 3, 4), (5, 6, 7), (5, 8, 9)])
    off = geo._separate_pinches(pts, fac, pair_pass=False)
    on = geo._separate_pinches(pts, fac, pair_pass=True)
    assert len(np.unique(np.round(off / 1e-6), axis=0)) < len(off)
    assert len(np.unique(np.round(on / 1e-6), axis=0)) == len(on)
    assert not np.array_equal(off, on)


def test_part_mesh_byte_identical_to_main():
    comp = json.load(open(FIXTURE))
    mesh, _ = geo.part_mesh(comp)
    assert len(mesh.vertices) == 1253 and len(mesh.faces) == 2654
    digest = hashlib.sha256(mesh.vertices.tobytes() + mesh.faces.tobytes()).hexdigest()
    assert digest == "5a128d9ce354c02db9169612a0d3edd00b02f41230474d4dab58f40ea1049a05"
