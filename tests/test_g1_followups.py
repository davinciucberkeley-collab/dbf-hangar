"""U4.24 G1 follow-ups (T122): S2, S4, S5, S6, S7."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from hangar.checks import tier0_schema
from hangar.design import REPO_ROOT, load_design
from hangar.ops import call

GEN = Path(__file__).parent / "fixtures" / "pdl-gen"


def _copy(tmp_path, mutate=None) -> Path:
    d = tmp_path / "gen-rod"
    shutil.copytree(GEN, d)
    if mutate:
        raw = yaml.safe_load((d / "plane.yaml").read_text(encoding="utf-8"))
        mutate(raw)
        (d / "plane.yaml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return d


def _cut(raw):      # removes x in [-50, -38] of the rod: 12 % of its volume
    raw["components"][0]["cavities"] = [{"geometry": {"box": {"size": [16, 20, 20]}}, "position": [-46, 0, 0]}]


def _whole(raw):    # removes the whole rod
    raw["components"][0]["cavities"] = [{"geometry": {"box": {"size": [300, 300, 300]}}, "position": [0, 0, 0]}]


def _od6(raw):      # inner_d 8 >= outer_d 6: the rod fails to build
    raw["parameters"]["rod_od_mm"] = 6


def test_1_non_number_parameter_reference_is_not_resolved(tmp_path):
    d = _copy(tmp_path, lambda r: r["parameters"].__setitem__("rod_len_mm", "100"))
    rows = [(r.check_id, r.status, r.message) for r in tier0_schema(load_design(d)).results]
    fails = [m for c, s, m in rows if c == "T0.parameters" and s == "FAIL"]
    assert fails and any("rod_len_mm" in m and "not a number" in m for m in fails), rows
    assert not any(c == "T0.parameters" and s == "PASS" for c, s, m in rows)


def test_2_mass_model_uses_the_cut_volume(tmp_path):
    d = load_design(_copy(tmp_path, _cut))
    assert d.resolve_errors == {}
    assert d.data["components"][0]["mass_g"] == pytest.approx(4.5110 * 0.88, abs=2e-3)      # 3.9697 g
    from hangar.geom.resolve import generated_volumes
    assert sum(generated_volumes(d.data["components"][0], d.base_dir)) == pytest.approx(2481.04, rel=1e-3)


def test_3_cavity_that_removes_the_whole_part_is_a_resolve_error_not_a_crash(tmp_path):
    d = load_design(_copy(tmp_path, _whole))
    assert "rod" in d.resolve_errors and "cavity" in d.resolve_errors["rod"]


def test_4_one_volume_cache_and_the_repo_root():
    from hangar.geom import materials, resolve
    assert not hasattr(resolve, "_VOLUMES") and not hasattr(resolve, "_key")
    assert materials._FILE == REPO_ROOT / "standards" / "materials.yaml"


def test_5_unrelated_edit_is_allowed_while_a_part_already_fails(tmp_path):
    d = _copy(tmp_path, _od6)
    assert "rod" in load_design(d).resolve_errors
    r = call("design.set", path=str(d), key="components[ballast].mass_g", value="12", why="heavier ballast")
    assert r.ok, r.messages
    assert any("still failing" in m and "rod" in m for m in r.messages), r.messages
    assert not r.data.get("regenerated")
    assert "mass_g: 12" in (d / "plane.yaml").read_text(encoding="utf-8")
    e = yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))[0]
    assert "regenerated" not in e


def test_6_edit_that_keeps_a_failing_part_failing_is_allowed_but_one_that_newly_breaks_a_part_is_refused(tmp_path):
    d = _copy(tmp_path, _od6)
    r = call("design.set", path=str(d), key="parameters.rod_od_mm", value="7", why="still too thin")
    assert r.ok, r.messages                         # od 7 < id 8: still failing, was failing before
    d2 = _copy(tmp_path / "b")
    orig = (d2 / "plane.yaml").read_bytes()
    r2 = call("design.set", path=str(d2), key="parameters.rod_od_mm", value="6", why="breaks the rod")
    assert not r2.ok and "regeneration failed" in " ".join(r2.messages)
    assert (d2 / "plane.yaml").read_bytes() == orig and not (d2 / "CHANGELOG.yaml").exists()


def test_7_regenerated_key_is_absent_when_nothing_regenerated(tmp_path):
    d = _copy(tmp_path)
    r = call("design.set", path=str(d), key="components[ballast].mass_g", value="12", why="heavier ballast")
    assert r.ok and "regenerated" not in r.data


def test_8_a_mass_model_bug_is_not_hidden_by_the_aircraft_summary(tmp_path, monkeypatch):
    d = _copy(tmp_path)
    orig = (d / "plane.yaml").read_bytes()

    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr("hangar.mass.mass_properties", boom)
    r = call("design.set", path=str(d), key="parameters.rod_len_mm", value="200", why="longer")
    assert not r.ok and any("boom" in m for m in r.messages), r.messages
    assert (d / "plane.yaml").read_bytes() == orig
