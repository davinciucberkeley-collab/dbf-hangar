"""U13.2-8: a fixed-wing design built from a blank start with the CLI ops alone."""
from __future__ import annotations

import time

import pytest
import yaml

import hangar.cli
from hangar import design as design_mod
from hangar.ops import call

FUSE = "{id: fuselage, type: fuselage, geometry: {generator: fuselage_loft, params: {stations: [[0, 60, 60], [150, 120, 130], [450, 100, 110], [800, 30, 30]], nose_length: 60, tail_length: 100}}, position: [0, 0, 0], mass_g: 300, manufacturing: {method: laser-cut, machine: jacobs-laser}}"
WING = "{id: wing, type: wing, geometry: {generator: wing_panel, params: {airfoil_file: naca2412, span: 1200, root_chord: 200, tip_chord: 140, inboard_span: 100, z_offset: 40}}, position: [200, 0, 0], mass_g: 250, manufacturing: {method: foamboard}}"
TAIL = "{id: tail, type: tail_surface, geometry: {generator: tail_surfaces, params: {airfoil_file: naca0012, stab_span: 400, stab_root_chord: 120, stab_tip_chord: 90, fin_thickness: 4, fin_height: 140, fin_root_chord: 130, fin_tip_chord: 80}}, position: [750, 0, 0], mass_g: 60, manufacturing: {method: foamboard}}"


@pytest.fixture
def designs(tmp_path, monkeypatch):
    d = tmp_path / "designs"
    d.mkdir()
    monkeypatch.setenv("PLANE_DESIGNS_DIR", str(d))
    monkeypatch.setattr(design_mod, "DESIGNS_DIR", d)
    monkeypatch.setattr(hangar.cli, "DESIGNS_DIR", d)
    return d


def test_blank_to_validated_fixed_wing(designs):
    t0 = time.monotonic()
    r = call("design.new", new_id="fw-e2e", blank=True)
    assert r.ok, r.messages
    d = designs / "fw-e2e"

    r = call("design.add", path=str(d), key="components", why="e2e", value=FUSE)
    assert r.ok, r.messages
    r = call("design.add", path=str(d), key="components", why="e2e", value=WING)
    assert r.ok, r.messages
    r = call("design.add", path=str(d), key="components", why="e2e", value=TAIL)
    assert r.ok, r.messages

    r = call("design.set", path=str(d), key="root", value="fuselage", why="e2e")
    assert r.ok, r.messages
    r = call("design.set", path=str(d), key="components[datum]", kind="remove", why="e2e")
    assert r.ok, r.messages

    r = call(
        "design.add",
        path=str(d),
        key="attachments",
        why="e2e",
        value="{id: wing-fuse, parent: fuselage, child: wing, method: glued, location: [250, 0, 40], embed_ok: true, rated_load_n: 100}",
    )
    assert r.ok, r.messages
    r = call(
        "design.add",
        path=str(d),
        key="attachments",
        why="e2e",
        value="{id: tail-fuse, parent: fuselage, child: tail, method: glued, location: [750, 0, 0], embed_ok: true, rated_load_n: 30}",
    )
    assert r.ok, r.messages

    r = call("design.validate", path=str(d), tier="1")
    assert r.ok is True, r.messages
    assert "FAIL" not in " ".join(r.messages)

    data = yaml.safe_load((d / "plane.yaml").read_text(encoding="utf-8"))
    assert [c["id"] for c in data["components"]] == ["fuselage", "wing", "tail"]
    assert data["root"] == "fuselage"
    assert [a["id"] for a in data["attachments"]] == ["wing-fuse", "tail-fuse"]
    assert sorted(p.name for p in d.iterdir()) == ["CHANGELOG.yaml", "plane.yaml"]

    log = yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert len(log) == 7

    r = call("design.mass", path=str(d))
    assert r.ok, r.messages
    assert r.data["mass_g"] == pytest.approx(610.0, abs=1e-6)
    print(f"\nE2E_WALL_SECONDS={time.monotonic() - t0:.1f}")
