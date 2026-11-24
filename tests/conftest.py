"""Shared fixtures for validator tests. Mutations start from the example design."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Callable
import warnings

import pytest

import hangar.checks as _checks
from hangar.checks import validate
from hangar.design import DESIGNS_DIR, Design, Scorecard, load_design

from testutil import EXAMPLE_PATH, statuses  # noqa: F401  (re-exported; helpers live in testutil)


@pytest.fixture
def example() -> Path:
    return EXAMPLE_PATH


@pytest.fixture
def mutate(example: Path) -> Callable[[Callable[[dict], None]], Scorecard]:
    def _mutate(fn: Callable[[dict], None]) -> Scorecard:
        base = load_design(example)
        data = copy.deepcopy(base.data)
        fn(data)
        design = Design(data=data, path=example)
        return validate(design)

    return _mutate


_T1_MEMO: dict[str, object] = {}


@pytest.fixture(scope="session", autouse=True)
def _share_concept_a_geometry():
    """Tier-1 geometry of the committed concept-a costs 28 to 54 s and nine tests ask for it: compute it once per
    worker. Only the committed folder is shared (same data, same standards), and each caller gets its own copy."""
    real = _checks.tier1_geometry

    def memo(design, std):
        # tests that change geometry use tmp_path copies or mutated design.data (different key), so they never hit another test's entry
        if design.base_dir != DESIGNS_DIR / "concept-a":
            return real(design, std)
        key = hashlib.sha256(json.dumps([design.data, std], sort_keys=True, default=str).encode()).hexdigest()
        if key not in _T1_MEMO:
            _T1_MEMO[key] = real(design, std)
        return copy.deepcopy(_T1_MEMO[key])

    mp = pytest.MonkeyPatch()
    mp.setattr(_checks, "tier1_geometry", memo)
    yield
    mp.undo()


_HEAVY = (  # slowest tests, most expensive first (W20-T measurement); dealt one per shard in turn so no shard gets them all (reordered for the windows shard times, T115)
    "tests/test_baseline.py::test_every_fail_or_skip_names_its_subject_or_is_design_level",
    "tests/test_adapters.py::test_missing_tool_is_skip_with_fix",
    "tests/test_bench.py::test_grader_passes_on_known_good_solution[fix-static-margin]",
    "tests/test_pdl.py::test_every_committed_design_migrates_to_1_1_with_same_verdict[concept-a]",
    "tests/test_adapters.py::test_plane_fea_group_and_legacy_alias",
    "tests/test_bench.py::test_grader_fails_on_start_design[fix-static-margin]",
    "tests/test_gates.py::test_tiers_0_5_unchanged_for_committed_designs[concept-a]",
    "tests/test_adapters.py::test_fea_plan_op_matches_engine",
    "tests/test_fea.py::test_hub_is_held_by_bridge_and_struts_not_by_wiring",
    "tests/test_discipline_gates.py::test_existing_gate_rows_fire_concept_a",
    "tests/test_gates.py::test_program_constraints_apply_to_every_active_design[concept-a]",
    "tests/test_bench.py::test_grade_replay_passes_when_only_plane_changed_the_design",
)


def missing_heavy(nodeids, heavy=_HEAVY) -> list[str]:
    """_HEAVY ids whose test file was collected but whose id was not (renamed or removed): they would silently fall back to round-robin."""
    ids = set(nodeids)
    files = {n.split("::", 1)[0] for n in ids}
    return [h for h in heavy if h.split("::", 1)[0] in files and h not in ids]


def pytest_addoption(parser):
    parser.addoption("--shard", default=None, help="run one slice of the collected tests, as I/N (1-based); CI splits the unit tests across N jobs")


def pytest_collection_modifyitems(config, items):
    spec = config.getoption("--shard")
    if not spec:
        return
    index, count = (int(x) for x in spec.split("/"))
    assert 1 <= index <= count, f"--shard {spec}: need 1 <= I <= N"
    gone = missing_heavy([it.nodeid for it in items])
    if gone:
        warnings.warn(f"--shard: _HEAVY ids not collected (renamed?): {gone}", stacklevel=1)
    heavy = {nid: h for h, nid in enumerate(_HEAVY)}
    mine = {it.nodeid for it in items if it.nodeid in heavy and heavy[it.nodeid] % count == index - 1}
    rest = sorted(it.nodeid for it in items if it.nodeid not in heavy)
    mine |= {nid for k, nid in enumerate(rest) if k % count == index - 1}
    dropped = [it for it in items if it.nodeid not in mine]
    config.hook.pytest_deselected(items=dropped)
    items[:] = [it for it in items if it.nodeid in mine]
