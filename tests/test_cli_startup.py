"""U15.3 (T124): the geometry stack (trimesh, scipy, networkx) loads only when geometry is built."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV = {**os.environ, "PLANE_CAD_OVERLAY": "off"}
LIST_LINE = 'print(sorted(m for m in ("trimesh", "scipy", "networkx") if m in sys.modules))\n'


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=ENV, cwd=REPO_ROOT)


def test_help_loads_no_geometry_stack():
    code = ("import sys\nfrom hangar.cli import cli\ntry:\n    cli(['--help'], standalone_mode=False)\n"
            "except SystemExit:\n    pass\n" + LIST_LINE)
    r = _run(code)
    assert r.returncode == 0, r.stderr
    assert r.stdout.endswith("[]\n"), r.stdout[-300:]


def test_design_get_loads_no_geometry_stack():
    """design get --key id builds no meshes, even on parametric designs (mass_g and swept poses are filled lazily; D102)."""
    code = ("import sys\nfrom hangar.cli import cli\n"
            "cli(['design', 'get', 'designs/concept-a', '--key', 'id'], standalone_mode=False)\n"
            + LIST_LINE)
    r = _run(code)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert lines[-1] == "[]", r.stdout
    assert any("concept-a" in ln for ln in lines[:-1]), r.stdout


def test_lazy_proxy_behaves():
    from hangar._lazy import LazyModule

    m = LazyModule("json")
    assert m.__dict__["_mod"] is None
    assert m.dumps([1]) == "[1]"
    assert m.__dict__["_mod"] is not None
    with pytest.raises(ModuleNotFoundError):
        LazyModule("no_such_module_xyz").anything


def test_package_exports_still_resolve():
    import hangar

    for name in ("validate", "mass_properties", "load_design", "Design", "Scorecard", "list_designs"):
        assert callable(getattr(hangar, name)), name
    with pytest.raises(AttributeError):
        hangar.nope
    from hangar import validate  # noqa: F401


def test_geometry_still_loads_on_demand():
    code = ("import sys\nfrom hangar.design import load_design\nfrom hangar.geometry import component_parts, is_point_mass\n"
            "d = load_design('designs/concept-a-param')\n"
            "c = next(c for c in d.components if not is_point_mass(c))\n"
            "parts = component_parts(c, d.base_dir)\nassert parts\nprint('trimesh' in sys.modules)\n")
    r = _run(code)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == "True"
