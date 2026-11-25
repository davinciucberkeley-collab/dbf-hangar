"""standards.pending also lists the pending gate thresholds (U15.2, T19)."""
from __future__ import annotations

import yaml

from hangar.design import REPO_ROOT
from hangar.ops import call

GATE_THRESHOLDS = REPO_ROOT / "standards" / "gate-thresholds.yaml"


def _pending_items() -> dict[str, dict]:
    return {i["key"]: i for i in call("standards.pending").data["items"]}


def test_gate_thresholds_are_listed():
    keys = {i["key"] for i in call("standards.pending").data["items"]}
    assert "wire_clearance_mm" in keys
    assert "servo_must_drive_mechanism" in keys
    assert "wing_area_complete_min" in keys


def test_matches_the_file():
    data = yaml.safe_load(GATE_THRESHOLDS.read_text(encoding="utf-8"))
    data.pop("version", None)
    expected = {k for k, v in data.items() if isinstance(v, dict) and v.get("source") == "pending"}
    items = _pending_items()
    listed = {k for k in items if k in data}
    assert listed == expected
    assert all(items[k]["blocking"] is False for k in listed)


def test_sourced_gate_thresholds_are_not_listed():
    keys = set(_pending_items())
    assert "mechanism_ratio_tol" not in keys
    assert "transport_box_mm" not in keys
