"""U15.3 step 4 (D102): `design get` on parametric designs does not build meshes; generated mass_g is filled on first read."""
from __future__ import annotations

import copy
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from hangar import yamlfast
from hangar.design import load_design
from hangar.geom import resolve as resolve_mod
from hangar.geom.resolve import is_generated, regeneration_report, resolve_design_data

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV = {**os.environ, "PLANE_CAD_OVERLAY": "off"}
IDS = ["concept-a-param", "c172-rc"]
TRIMESH_LINE = 'print("trimesh" in sys.modules)\n'


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=ENV, cwd=REPO_ROOT)


def _get(args: list[str]) -> list[str]:
    code = f"import sys\nfrom hangar.cli import cli\ncli({['design', 'get', *args]!r}, standalone_mode=False)\n" + TRIMESH_LINE
    r = _run(code)
    assert r.returncode == 0, r.stderr
    return r.stdout.splitlines()


@pytest.mark.parametrize("design_id", IDS)
def test_get_key_loads_no_trimesh(design_id):
    lines = _get([f"designs/{design_id}", "--key", "id"])
    assert lines[-1] == "False", lines
    assert f'"{design_id}"' in lines, lines


def test_get_parameter_value():
    lines = _get(["designs/concept-a-param", "--key", "parameters.span_mm"])
    assert lines[-1] == "False", lines
    assert "900" in lines, lines


@pytest.mark.parametrize("design_id", IDS)
def test_get_without_key_loads_no_trimesh(design_id):
    lines = _get([f"designs/{design_id}"])
    assert lines[-1] == "False", lines[-3:]
    assert "schema_version" in "\n".join(lines)


def test_get_components_key_still_has_mass():
    code = ("import sys\nfrom pathlib import Path\nfrom hangar.cli import cli\nfrom hangar import yamlfast\n"
            "from hangar.geom.resolve import resolve_design_data\n"
            "cli(['design', 'get', 'designs/c172-rc', '--key', 'components[0].mass_g'], standalone_mode=False)\n"
            "p = Path('designs/c172-rc')\n"
            "raw = yamlfast.safe_load((p / 'plane.yaml').read_text())\n"
            "print(resolve_design_data(raw, p.resolve())[0]['components'][0]['mass_g'])\n" + TRIMESH_LINE)
    r = _run(code)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert lines[-1] == "True", lines
    assert float(lines[-3]) == float(lines[-2]), lines


@pytest.mark.parametrize("design_id", IDS)
def test_lazy_data_equals_eager(design_id):
    path = REPO_ROOT / "designs" / design_id / "plane.yaml"
    raw = yamlfast.safe_load(path.read_text())
    eager, eerr = resolve_design_data(copy.deepcopy(raw), path.parent)
    d = load_design(path)
    assert d.data == eager
    assert d.resolve_errors == eerr


def test_mass_filled_once_on_first_read(monkeypatch):
    count = {"n": 0}
    real = resolve_mod.generated_volumes

    def counting(c, base_dir):
        count["n"] += 1
        return real(c, base_dir)

    monkeypatch.setattr(resolve_mod, "generated_volumes", counting)
    d = load_design(REPO_ROOT / "designs" / "c172-rc")
    assert count["n"] == 0
    d.data_without_mass()
    assert count["n"] == 0
    comps = d.components
    first = count["n"]
    expected = sum(1 for c in comps if is_generated(c) and isinstance(c.get("mass_model"), dict))
    assert first > 0 and first == expected
    d.components
    assert count["n"] == first
    assert d.data_without_mass() is d.data


def _tiny(material="xps-foam", thickness=1.5, did="t") -> dict:
    return {"schema_version": "1.2", "id": did, "root": "a", "attachments": [],
            "components": [{"id": "a", "type": "plate", "position": [0, 0, 0],
                            "geometry": {"generator": "plate", "params": {"plane": "xy", "size": [4, 14], "thickness": thickness}},
                            "mass_model": {"material": material}}]}


def test_resolve_errors_surface_on_first_read(tmp_path):
    raw = _tiny("no-such-material")
    raw.pop("root")
    raw.pop("attachments")
    (tmp_path / "plane.yaml").write_text(yaml.safe_dump(raw))
    d = load_design(tmp_path)
    errs = d.resolve_errors
    assert "a" in errs
    assert errs == resolve_design_data(raw, tmp_path)[1]


def test_regeneration_report_skips_aircraft_when_nothing_regenerates(tmp_path, monkeypatch):
    plane = tmp_path / "plane.yaml"
    count = {"n": 0}
    real = resolve_mod._aircraft

    def counting(*a, **k):
        count["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(resolve_mod, "_aircraft", counting)
    old_text = yaml.safe_dump(_tiny())
    res = regeneration_report(old_text, yaml.safe_dump(_tiny(did="t2")), plane)
    assert res["components"] == {}
    assert res["mass_g"] == [None, None]
    assert count["n"] == 0
    res = regeneration_report(old_text, yaml.safe_dump(_tiny(thickness=2.0)), plane)
    assert "a" in res["components"]
    assert count["n"] == 2
    m0, m1 = res["mass_g"]
    assert isinstance(m0, float) and isinstance(m1, float) and m0 != m1
