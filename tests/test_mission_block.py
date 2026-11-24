"""U4.30-3: the design-level optional `mission` block (schema + T0.mission row)."""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

from hangar.checks import tier0_schema
from hangar.design import FAIL, PASS, Design

FIX = Path(__file__).parent / "fixtures"


def design(mission=None, version: str | None = None) -> Design:
    d = copy.deepcopy(yaml.safe_load((FIX / "gates-base.yaml").read_text(encoding="utf-8")))
    if version is not None:
        d["schema_version"] = version
    elif d.get("schema_version", "0.1") < "1.2":
        d["schema_version"] = "1.2"
    if mission is not None:
        d["mission"] = mission
    return Design(d, path=FIX / "gates-base.yaml")


def rows(dsg: Design, check_id: str):
    return [r for r in tier0_schema(dsg).results if r.check_id == check_id]


def test_mission_absent_emits_no_row():
    dsg = design()
    assert rows(dsg, "T0.mission") == []
    assert [r.status for r in rows(dsg, "T0.schema")] == [PASS]


def test_mission_present_passes():
    dsg = design({"name": "VTOL demonstrator", "profile": "vtol-demonstrator"})
    r = rows(dsg, "T0.mission")
    assert [x.status for x in r] == [PASS]
    assert r[0].message == "mission: VTOL demonstrator (profile vtol-demonstrator)"


def test_mission_bad_profile_fails_schema():
    dsg = design({"name": "x", "profile": "jet"})
    r = rows(dsg, "T0.schema")
    assert [x.status for x in r] == [FAIL]
    assert "mission/profile" in r[0].message


def test_mission_extra_key_fails_schema():
    dsg = design({"name": "x", "profile": "other", "speed": 3})
    assert [x.status for x in rows(dsg, "T0.schema")] == [FAIL]


def test_mission_in_old_version_fails():
    dsg = design({"name": "VTOL demonstrator", "profile": "vtol-demonstrator"}, version="0.4")
    fails = [x for x in rows(dsg, "T0.version") if x.status == FAIL and "mission" in x.message]
    assert fails, [x.message for x in rows(dsg, "T0.version")]
