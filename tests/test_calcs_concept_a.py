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
    assert "read_value" not in CALCS
    assert set(CALCS) - {"sum_values"} == {r["function"] for r in GOLDEN} | {"scale_value"}


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
