"""U12.2-1: real-parts library loader, library_part generator, T8 library rows, parts ops."""
from __future__ import annotations

import copy
import datetime
import math
from pathlib import Path

import pytest
import yaml

from hangar.checks import validate  # noqa: F401
from hangar.design import FAIL, PASS, Design
from hangar.gates import run_gates
from hangar.geom import library, registry
from hangar.geom.registry import get, validate_params
from hangar.ops import OpInputError, call
from hangar.ops import parts as parts_op

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "parts"
BASE = Path(__file__).parent / "fixtures" / "gates-base.yaml"
OK = yaml.safe_load((FIXTURE_DIR / "test-servo" / "part.yaml").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def lib(monkeypatch):
    monkeypatch.setattr(library, "PARTS_DIR", FIXTURE_DIR)


def test_list_and_load():
    assert library.list_parts() == ["test-servo"]
    assert library.load_part("test-servo")["mass_g"] == 9.0


def test_unknown_part_message():
    with pytest.raises(KeyError) as e:
        library.load_part("nope")
    assert "known: test-servo" in str(e.value)


def test_part_errors():
    assert library.part_errors(OK, "test-servo") == []
    assert any("mass_g" in m for m in library.part_errors({**OK, "mass_g": 0}, "test-servo"))
    assert any("id" in m for m in library.part_errors({**OK, "id": "other"}, "test-servo"))
    assert any("cad_status" in m for m in library.part_errors({**OK, "cad_status": "real"}, "test-servo"))
    errs = " ".join(library.part_errors({}, "test-servo"))
    assert all(k in errs for k in library.REQUIRED) and len(library.REQUIRED) == 12


def test_library_part_generator_volume(tmp_path):
    parts = registry.build_component(
        {"id": "s", "geometry": {"generator": "library_part", "params": {"part": "test-servo"}}}, tmp_path)
    assert len(parts) == 1
    assert abs(float(parts[0].volume)) == pytest.approx(math.pi * 5 ** 2 * 20, rel=0.01)
    assert parts[0].extents[0] == pytest.approx(20.0)


def test_generator_unknown_part_validation():
    errs = validate_params(get("library_part"), {"part": "nope"})
    assert errs and any("known:" in e for e in errs)


def _card(lib_part):
    import yaml as y
    data = copy.deepcopy(y.safe_load(BASE.read_text(encoding="utf-8")))
    data["schema_version"] = "1.2"
    for it in data["bom"]["items"]:
        it["verified"]["date"] = "2026-11-15"
    esc = next(c for c in data["components"] if c["id"] == "esc")
    del esc["geometry"]["box"]
    esc["geometry"] = {"generator": "library_part", "params": {"part": "test-servo"}}
    data["bom"]["items"].append({"id": "esc", "component_ids": ["esc"], "qty": 1, "unit_cost_usd": 5,
                                 "library_part": lib_part,
                                 "verified": {"by": "team", "date": "2026-11-15", "method": "datasheet",
                                              "evidence": "datasheet"}})
    return run_gates(Design(data, path=BASE), only_tiers={8}, strict=True, today=datetime.date(2026, 11, 20))


def _row(card, cid):
    return next(r for t in card.tiers for r in t.results if r.check_id == cid)


def test_t8_library_rows():
    card = _card("test-servo")
    assert _row(card, "T8.bom.library.esc").status == PASS
    assert _row(card, "T8.bom.library_match.esc").status == PASS
    card = _card("other-part")
    assert _row(card, "T8.bom.library_match.esc").status == FAIL
    assert _row(card, "T8.bom.library.esc").status == FAIL


def test_parts_ops():
    assert call("parts.list").data["count"] == 1
    assert call("parts.show", id="test-servo").data["vendor"] == OK["vendor"]
    # call() turns OpInputError into ok=False (hangar.ops._call_spec); the op function itself raises it
    r = call("parts.show", id="nope")
    assert not r.ok and "known: test-servo" in " ".join(r.messages + [str(r.data)])
    with pytest.raises(OpInputError):
        parts_op.show("nope")
