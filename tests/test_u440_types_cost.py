import pytest

from hangar.calcs.concept_a import bom_cost
from hangar.gates.interfaces import load_connection_types
from hangar.importers.dbf import CONN_METHOD

NEW_IDS = ("CT-A-M3-CSK-MOTOR", "CT-A-M3-BOLT-MOUNT")


def test_new_types_in_library():
    lib = load_connection_types()
    for cid in NEW_IDS:
        assert cid in lib
        assert lib[cid]["rating_basis"] == "placeholder"
        assert lib[cid]["source"] == "pending"
    assert len(lib) == 46


def test_importer_maps_new_types():
    for cid in NEW_IDS:
        assert CONN_METHOD[cid] == ("bolted", "")


def test_bom_cost_rship():
    rows = [("R01", "x", "A", 1, 100.0, False), ("R03", "x", "A", 1, 40.0, False),
            ("W01", "x", "A", 1, 10.0, False), ("P01", "x", "A", 1, 20.0, False),
            ("M01", "x", "A", 1, 30.0, False)]
    r = bom_cost(rows, 0.1, 5.0, [["A", 7.0]], 0.3, [], 500.0, rship=[10.71, 15.0, 10.71])
    assert r["total_usd"] == pytest.approx(466.42, rel=1e-9)
    assert r["total_30_usd"] == pytest.approx(506.02, rel=1e-9)
    assert r["margin_usd"] == pytest.approx(33.58, rel=1e-9)
    assert r["margin_30_usd"] == pytest.approx(-6.02, rel=1e-9)
    assert r["reserve_usd"] == pytest.approx(234.42, rel=1e-9)
    assert r["shipping_usd"] == pytest.approx(7.0, rel=1e-9)


def test_bom_cost_without_rship_unchanged():
    rows = [("R01", "x", "A", 1, 100.0, False), ("R03", "x", "A", 1, 40.0, False),
            ("W01", "x", "A", 1, 10.0, False), ("P01", "x", "A", 1, 20.0, False),
            ("M01", "x", "A", 1, 30.0, False)]
    ship = [["A", 7.0], ["TMotor", 1.0], ["RMRC", 2.0], ["Amazon", 3.0]]
    r = bom_cost(rows, 0.1, 5.0, ship, 0.3, [], 500.0)
    assert r["total_usd"] == pytest.approx(436.0, rel=1e-9)
    assert r["reserve_usd"] == pytest.approx(204.0, rel=1e-9)
    assert r["shipping_usd"] == pytest.approx(7.0, rel=1e-9)
