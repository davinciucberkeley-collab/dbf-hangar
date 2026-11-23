import numpy as np
import pytest

from hangar.importers import dbf, dbf_geometry as geo


def _cube(side_m):
    s = side_m / 2
    v = [(-s,-s,-s),(s,-s,-s),(s,s,-s),(-s,s,-s),(-s,-s,s),(s,-s,s),(s,s,s),(-s,s,s)]
    t = [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return {"kind": "mesh", "name": "cube", "verts": [list(p) for p in v], "tris": [list(x) for x in t]}

def test_mesh_kind_volume_in_mm3():
    m = geo.body_mesh(_cube(0.01))                      # a 10 mm cube given in metres
    assert m.is_watertight and m.volume == pytest.approx(1000.0, rel=1e-6)
    assert np.allclose(m.bounds, [[-5, -5, -5], [5, 5, 5]], atol=1e-6)

def test_mesh_kind_without_triangles_is_a_geometry_error():
    with pytest.raises(geo.GeometryError):
        geo.body_mesh({"kind": "mesh", "verts": [[0, 0, 0]], "tris": []})

def test_retention_n_ignores_non_numeric():
    assert dbf._retention_n({"retention": {"load_n": 38.8}}) == 38.8
    assert dbf._retention_n({"retention": {"load_n": "none (pneumatic)"}}) is None
    assert dbf._retention_n({"retention": {"load_n": 0}}) is None
    assert dbf._retention_n({}) is None

def test_conn_method_knows_pitot_tubing():
    assert dbf.CONN_METHOD["CT-PITOT-TUBING"][0] == "press-fit"
