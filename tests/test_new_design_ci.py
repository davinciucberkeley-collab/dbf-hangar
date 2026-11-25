"""A new design in designs/ must pass the design-enumerating tests without editing them (U13.7, demo blocker)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from hangar.checks import tier0_schema
from hangar.design import DESIGNS_DIR, REPO_ROOT, load_design

FIXTURES = Path(__file__).parent / "fixtures"


def test_every_design_loads_cleanly():
    folders = sorted(p.parent for p in DESIGNS_DIR.glob("*/plane.yaml"))
    assert folders
    for f in folders:
        d = load_design(f)
        assert d.resolve_errors == {}, f
        bad = [r for r in tier0_schema(d).results if r.status == "FAIL" and r.check_id in ("T0.generator", "T0.parameters")]
        assert not bad, (f, bad)


def test_ci_set_tests_ignore_a_new_design(tmp_path):
    sandbox = tmp_path / "designs"
    sandbox.mkdir()
    real = REPO_ROOT / "designs"
    shutil.copytree(real / "example-tailsitter-wing", sandbox / "example-tailsitter-wing")
    shutil.copytree(real / "tiltwing-cakir", sandbox / "tiltwing-cakir")
    shutil.copytree(FIXTURES / "mechanism-recipe", sandbox / "newgen")
    stand_in = (real / "example-tailsitter-wing" / "plane.yaml").read_bytes()
    names = json.loads((FIXTURES / "design-verdicts.json").read_text(encoding="utf-8"))
    for name in names:
        if name != "_recorded" and not (sandbox / name).exists():
            (sandbox / name).mkdir()
            (sandbox / name / "plane.yaml").write_bytes(stand_in)      # the verdict test is not run here; only the subset test is
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
         "tests/test_expressions.py::test_designs_without_expressions_resolve_unchanged",
         "tests/test_pdl12.py::test_old_designs_untouched",
         "tests/test_applicability.py::test_verdict_fixture_records_its_date"],
        cwd=REPO_ROOT, env={**os.environ, "PLANE_DESIGNS_DIR": str(sandbox), "PLANE_CAD_OVERLAY": "off"},
        capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:]
