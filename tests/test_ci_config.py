"""CI configuration pins (T115): the progress workflow keeps the pending-decision check, the playwright cache keys on the
installed version, every _HEAVY id still exists, and a renamed one warns."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
# load tests/conftest.py by path: `import conftest` resolves to tests/harness/conftest.py when that folder is collected too
_spec = importlib.util.spec_from_file_location("hangar_tests_root_conftest", ROOT / "tests/conftest.py")
_root_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_root_conftest)
_HEAVY = _root_conftest._HEAVY
missing_heavy = _root_conftest.missing_heavy
pytest_collection_modifyitems = _root_conftest.pytest_collection_modifyitems
PENDING = "tests/test_standards.py::test_no_blocking_threshold_is_pending_without_a_decision"


def test_progress_workflow_runs_the_pending_decision_check():
    text = (ROOT / ".github/workflows/progress.yml").read_text(encoding="utf-8")
    assert PENDING in text
    assert "def test_no_blocking_threshold_is_pending_without_a_decision" in (ROOT / "tests/test_standards.py").read_text(encoding="utf-8")


def test_playwright_cache_key_uses_the_installed_version():
    text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    key = [l for l in text.splitlines() if l.strip().startswith("key: pw-")]
    assert len(key) == 1, key
    assert "steps.pw.outputs.v" in key[0] and "hashFiles" not in key[0]
    assert "id: pw" in text


@pytest.mark.parametrize("nodeid", _HEAVY)
def test_every_heavy_id_still_exists(nodeid):
    path, _, rest = nodeid.partition("::")
    name = rest.split("[")[0]
    src = (ROOT / path).read_text(encoding="utf-8")
    assert re.search(rf"^def {re.escape(name)}\(", src, re.M), f"{nodeid}: renamed or removed; update _HEAVY in tests/conftest.py"


def test_missing_heavy_names_ids_of_collected_files_only():
    got = missing_heavy({"tests/test_a.py::test_x"}, heavy=("tests/test_a.py::test_y", "tests/test_b.py::test_z", "tests/test_a.py::test_x"))
    assert got == ["tests/test_a.py::test_y"]      # test_b.py was not collected at all (partial run): no warning for it


def _run_hook(spec, nodeids):
    items = [SimpleNamespace(nodeid=n) for n in nodeids]
    cfg = SimpleNamespace(getoption=lambda name: spec, hook=SimpleNamespace(pytest_deselected=lambda items: None))
    pytest_collection_modifyitems(cfg, items)
    return {i.nodeid for i in items}


def test_hook_warns_when_a_heavy_id_was_renamed():
    ids = [h for h in _HEAVY if not h.endswith("test_missing_tool_is_skip_with_fix")] + ["tests/test_other.py::test_a"]
    with pytest.warns(UserWarning, match="_HEAVY"):
        _run_hook("1/3", ids)


def test_heavy_ids_are_dealt_four_per_shard_and_the_subprocess_ones_split():
    rest = [f"tests/test_zz.py::test_{k}" for k in range(30)]
    subprocess_heavy = {h for h in _HEAVY if any(s in h for s in ("missing_tool", "plane_fea_group", "grader_passes", "grader_fails"))}
    assert len(subprocess_heavy) == 4
    union: set[str] = set()
    split = []
    for i in (1, 2, 3):
        mine = _run_hook(f"{i}/3", list(_HEAVY) + rest)
        assert len(mine & set(_HEAVY)) == 4
        split.append(len(mine & subprocess_heavy))
        union |= mine
    assert sorted(split) == [0, 2, 2]               # never three or four of the subprocess-heavy ids on one shard
    assert union == set(_HEAVY) | set(rest)
