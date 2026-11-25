"""U4.41-6: the design apply file format, the motor propulsion block and the component types are documented, and the documented forms really work."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml

from hangar.ops import call

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "docs" / "team-guide.md"
AGENT = REPO / ".claude" / "agents" / "design-engineer.md"
EXAMPLE = REPO / "designs" / "example-tailsitter-wing"


def test_guide_has_the_three_bullets():
    text = GUIDE.read_text(encoding="utf-8")
    for needle in (
        "plane design apply <path> --edits <file.yaml>",
        "{append: components",
        "{add: mechanisms",
        "propulsion: {max_thrust_n: 12, axis: [-1, 0, 0], role: cruise, max_current_a: 18, prop_diameter_mm: 254}",
        "there is no `control_surface` type",
    ):
        assert needle in text, needle
    lines = text.splitlines()
    airfoils = [i for i, l in enumerate(lines) if l.startswith("- Airfoils:")]
    gate = lines.index("## 5. Task: gate work")
    assert len(airfoils) == 1
    bullets = [i for i, l in enumerate(lines) if i > airfoils[0] and l.startswith("- ") and i < gate]
    assert bullets[:3] and bullets[0] == airfoils[0] + 1
    assert all(lines[i].startswith("- ") for i in range(airfoils[0] + 1, airfoils[0] + 4))
    assert airfoils[0] < gate
    assert any("plane design apply <path> --edits <file.yaml>" in lines[i] for i in range(airfoils[0] + 1, airfoils[0] + 4))
    assert any("{add: mechanisms" in lines[i] for i in range(airfoils[0] + 1, airfoils[0] + 4))
    assert any("there is no `control_surface` type" in lines[i] for i in range(airfoils[0] + 1, airfoils[0] + 4))


def test_agent_file_points_at_the_guide():
    text = AGENT.read_text(encoding="utf-8")
    assert "Starting a new concept" in text
    assert "no Write tool" in text
    try:
        head = subprocess.run(
            ["git", "-C", str(REPO), "show", "HEAD:.claude/agents/design-engineer.md"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        import pytest
        pytest.skip("git not available")
    assert text.splitlines()[:5] == head.splitlines()[:5]


def test_documented_apply_file_really_works(tmp_path):
    d = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE, d)
    edits = tmp_path / "edits.yaml"
    items = [
        {"set": "components[center_body].mass_g", "value": 125},
        {"set": "components[center_body].position", "value": [155, 0, 1]},
        {"add": "flight.air_density_kgm3", "value": 1.2},
        {"append": "components", "value": {"id": "probe", "type": "other", "geometry": {"point_mass": {}},
                                           "position": [10, 0, 0], "mass_g": 2}},
        {"remove": "attachments[fc-mount]"},
    ]
    edits.write_text(yaml.safe_dump(items), encoding="utf-8")
    r = call("design.apply", path=str(d), edits=edits, why="t")
    assert r.ok, r.messages
    data = yaml.safe_load((d / "plane.yaml").read_text(encoding="utf-8"))
    center = next(c for c in data["components"] if c["id"] == "center_body")
    assert center["mass_g"] == 125
    assert center["position"] == [155, 0, 1]
    assert data["flight"]["air_density_kgm3"] == 1.2
    assert any(c["id"] == "probe" for c in data["components"])
    assert all(a["id"] != "fc-mount" for a in data["attachments"])


def test_documented_propulsion_block_is_schema_valid(tmp_path):
    d = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE, d)
    motor = ("{id: m2, type: motor, geometry: {box: {size: [30, 30, 40]}}, position: [0, 0, 0], mass_g: 60, "
             "propulsion: {max_thrust_n: 12, axis: [-1, 0, 0], role: cruise, max_current_a: 18, prop_diameter_mm: 254}}")
    r = call("design.add", path=str(d), key="components", why="t", value=motor)
    assert r.ok, r.messages
    bare = "{id: m3, type: motor, geometry: {box: {size: [30, 30, 40]}}, position: [0, 0, 0], mass_g: 60}"
    r = call("design.add", path=str(d), key="components", why="t", value=bare)
    assert not r.ok
    assert any("propulsion" in m for m in r.messages), r.messages
