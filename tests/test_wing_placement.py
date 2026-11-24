from __future__ import annotations

import json
from pathlib import Path

import pytest

from hangar.geom import registry
from hangar.geom.registry import get, validate_params

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
DAT = "airfoils/diamond.dat"
SCHEMA = Path(__file__).parent.parent / "schema" / "plane.schema.json"


def build(name, params, base=FIXTURE_DIR):
    return registry.build_component({"id": "t", "geometry": {"generator": name, "params": params}}, base)


def wing(**kw):
    p = {"airfoil_file": DAT, "span": 400, "root_chord": 100, "tip_chord": 100, "part": "full"}
    p.update(kw)
    return p


def vol(m):
    return abs(float(m.volume))


def test_none_is_unchanged():
    plain = build("wing_panel", wing())
    none = build("wing_panel", wing(placement="none"))
    assert len(plain) == len(none) == 1
    assert none[0].bounds.tolist() == plain[0].bounds.tolist()
    assert vol(none[0]) == pytest.approx(vol(plain[0]), rel=1e-6)
    assert vol(none[0]) == pytest.approx(200000, rel=1e-6)


def test_high_mid_low_shift():
    base = dict(fuselage_height=80, fuselage_center_z=10)
    expected = {"high": (45, 55), "mid": (5, 15), "low": (-35, -25)}
    ref = vol(build("wing_panel", wing())[0])
    for placement, (lo, hi) in expected.items():
        m = build("wing_panel", wing(placement=placement, **base))[0]
        assert m.bounds[0][2] == pytest.approx(lo, abs=1e-6), placement
        assert m.bounds[1][2] == pytest.approx(hi, abs=1e-6), placement
        assert vol(m) == pytest.approx(ref, rel=1e-6), placement


def test_placement_adds_to_z_offset():
    # datum = 0 + fuselage_height/2 (40) + z_offset (3) = 43; z extent +-5 about datum
    m = build("wing_panel", wing(placement="high", fuselage_height=80, z_offset=3))[0]
    assert m.bounds[0][2] == pytest.approx(38, abs=1e-6)
    assert m.bounds[1][2] == pytest.approx(48, abs=1e-6)


def test_placement_validation():
    errs = validate_params(get("wing_panel"), wing(placement="low"))
    assert any("fuselage_height" in e for e in errs), errs


def test_all_new_generators_in_schema_text():
    desc = _find_generator_description(json.loads(SCHEMA.read_text(encoding="utf-8")))
    assert desc is not None, "no geometry.generator description in schema"
    missing = [n for n in registry.names() if n not in desc]
    assert not missing, f"geometry.generator description lacks: {missing}"


def _find_generator_description(node):
    if isinstance(node, dict):
        if "generator" in node and isinstance(node["generator"], dict) and "description" in node["generator"]:
            return node["generator"]["description"]
        for v in node.values():
            found = _find_generator_description(v)
            if found is not None:
                return found
    elif isinstance(node, list):
        for v in node:
            found = _find_generator_description(v)
            if found is not None:
                return found
    return None
