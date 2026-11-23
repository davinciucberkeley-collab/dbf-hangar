import json
import os
from pathlib import Path

import pytest

from hangar.calcs import CALCS
from hangar.claims.calc import resolve_calc
from hangar.design import REPO_ROOT

GOLDEN = json.loads((REPO_ROOT / "tests/fixtures/concept-a-calcs/golden.json").read_text(encoding="utf-8"))
DBF_PROOFS = Path(os.environ.get("DBF_COMBINED", "C:/Users/trist/DBF-Combined")) / "redesign/qp/A/proofs"


def _close(got, want):
    if isinstance(want, list):
        return len(got) == len(want) and all(_close(g, w) for g, w in zip(got, want))
    if isinstance(want, dict):
        return set(got) == set(want) and all(_close(got[k], want[k]) for k in want)
    if isinstance(want, (int, float)) and not isinstance(want, bool):
        return got == pytest.approx(want, rel=1e-9, abs=1e-12)
    return got == want


def test_golden_has_36_nodes_and_28_functions():
    assert len(GOLDEN) == 36
    assert len({r["function"] for r in GOLDEN}) == 28


def test_registered_set_is_exactly_the_28_names():
    assert {r["function"] for r in GOLDEN} <= set(CALCS)
    assert set(CALCS) - {"sum_values"} == {r["function"] for r in GOLDEN} | {"scale_value", "read_value"}


def test_read_value_echoes_its_input():  # T28
    from hangar.calcs import read_value
    assert CALCS["read_value"] is read_value
    assert read_value(21.5) == {"v": 21.5}
    assert read_value(v="x") == {"v": "x"}


@pytest.mark.parametrize("row", GOLDEN, ids=[r["id"] for r in GOLDEN])
def test_golden_outputs_match(row):
    fn = resolve_calc(row["function"])
    res = fn(**row["input_values"])
    if not isinstance(res, dict):
        res = {next(iter(row["outputs"])): res}
    for k, want in row["outputs"].items():
        assert _close(res[k], want), (row["id"], k, want, res.get(k))


def test_registry_resolves_every_function():
    for name in {r["function"] for r in GOLDEN}:
        assert resolve_calc(name) is not None, name


def test_concept_a_module_does_no_io_and_imports_nothing_foreign():
    text = (REPO_ROOT / "core/hangar/calcs/concept_a.py").read_text(encoding="utf-8")
    for bad in ("open(", "proofkit", "sys.path", "importlib", "DBF-Combined", "read_text"):
        assert bad not in text, bad


def test_no_py_files_under_designs():
    assert list((REPO_ROOT / "designs").rglob("*.py")) == []


def test_scale_value():
    from hangar.calcs.concept_a import scale_value

    assert scale_value(1470, 0.001) == {"value": pytest.approx(1.47)}
    assert scale_value(v=2, k=3) == {"value": 6}


@pytest.mark.skipif(not DBF_PROOFS.exists(), reason="DBF-Combined clone not present")
def test_golden_matches_the_source_files():
    import glob

    rows = []
    for f in sorted(glob.glob(str(DBF_PROOFS) + "/claims.*.json")):
        for n in json.loads(Path(f).read_text(encoding="utf-8"))["nodes"]:
            if n["type"] == "calculation" and n["function"] != "read_value":
                rows.append({"id": n["id"], "function": n["function"], "input_values": n["input_values"], "outputs": n["outputs"]})
    rows.sort(key=lambda r: r["id"])
    assert rows == GOLDEN


def test_concept_a_t9_has_no_skipped_claim_and_no_fail():  # T28: the 40 read_value claims now recompute (from live PDL values)
    from hangar.design import REPO_ROOT, load_design
    from hangar.gates import run_gates
    card = run_gates(load_design(REPO_ROOT / "designs" / "concept-a"), only_tiers={9})
    rows = [r for t in card.tiers if t.tier == 9 for r in t.results]
    assert len(rows) == 93
    assert [r.check_id for r in rows if r.status in ("SKIP", "FAIL")] == []
