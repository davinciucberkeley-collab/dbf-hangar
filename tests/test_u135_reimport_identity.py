"""U13.5: pinch separation applies only to meshes that fail the watertight round trip (re-import identity)."""
import numpy as np
import trimesh

from hangar.importers import dbf, dbf_geometry as geo


def _split_cube():
    """A closed cube whose faces own their vertices (24 vertices, 8 coincident groups): reloads closed once welded."""
    c = trimesh.creation.box((1, 1, 1))
    tri = c.vertices[c.faces]
    return tri.reshape(-1, 3).astype(float), np.arange(len(c.faces) * 3).reshape(-1, 3)


def test_part_mesh_tries_without_pair_pass_first(monkeypatch):
    seen = []
    real = geo._part_mesh

    def spy(comp, pair_pass=True):
        seen.append(pair_pass)
        return real(comp, pair_pass)

    monkeypatch.setattr(geo, "_part_mesh", spy)
    import json
    from pathlib import Path
    comp = json.load(open(Path(__file__).resolve().parents[1] / "tests/fixtures/dbf-xmount-comp.json"))
    geo.part_mesh(comp)
    assert seen == [False, True]


def test_fixture_needs_and_gets_the_pair_pass():
    import json
    from pathlib import Path
    comp = json.load(open(Path(__file__).resolve().parents[1] / "tests/fixtures/dbf-xmount-comp.json"))
    mesh, _ = geo.part_mesh(comp)  # first attempt (no pair pass) fails, the retry succeeds
    assert geo._closed(mesh)


def test_canonical_leaves_clean_roundtrip_untouched():
    v, f = _split_cube()
    m = dbf._canonical(trimesh.Trimesh(v, f, process=False))
    assert len(np.unique(m.vertices, axis=0)) == 8  # still coincident groups, not separated


def test_canonical_still_separates_failing_roundtrip():
    a = trimesh.creation.box((1, 1, 1)); a.apply_translation((0.5, 0.5, 0.5))
    b = trimesh.creation.box((1, 1, 1)); b.apply_translation((1.5, 1.5, 0.5))
    m = trimesh.util.concatenate([a, b])
    m = dbf._canonical(trimesh.Trimesh(m.vertices, m.faces, process=False))
    assert len(np.unique(m.vertices, axis=0)) == len(m.vertices)
