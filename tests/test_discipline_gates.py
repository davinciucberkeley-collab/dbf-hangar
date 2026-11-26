"""U3.6: five report-only discipline gates (joint RF, control authority, transition margin, endurance, electrical rating)."""
from __future__ import annotations

import copy
import datetime
import difflib
import math
import shutil
from pathlib import Path

import pytest
import yaml

import hangar.gates
import hangar.gates.discipline
from hangar.design import DESIGNS_DIR, FAIL, PASS, REPO_ROOT, SKIP, WARN, Design, Scorecard, load_design
from hangar.gates import DISCIPLINE, discipline_check, load_discipline_table, load_gate_table, run_gates
from hangar.gates.fidelity import resolve_threshold
from hangar.ops import call

FIX = Path(__file__).parent / "fixtures"
TODAY = datetime.date(2026, 11, 20)
IDS = ("T2.joint_rf", "T3.control_authority", "T3.transition_margin", "T3.endurance", "T7.electrical_rating")
CONCEPT_A = DESIGNS_DIR / "concept-a"
CONCEPT_A_FROZEN = REPO_ROOT / "tests" / "fixtures" / "concept-a-frozen"

CONCEPT_A_D21 = {
    "schema_version": "1.0",
    "battery": {"pwr-001": {"capacity_mah": 2300, "cells_s": 4, "max_discharge_c": 75}},
    "motors": ["prp-001-ll", "prp-001-lr", "prp-001-ul", "prp-001-ur"],
    "motor_fields": {"max_current_a": 25, "prop_diameter_mm": 228.6},
    "flight": {"cruise_ld": 6.5, "cruise_ld_source": "test value",
               "transition_speed_mps": 15.8, "transition_speed_source": "test value"},
    "connection": {"E-WNG-01": "CT-M3-SHCS-INSERT"},
    "wiring": {"harnesses": [{"id": "hrn-bat", "from": "pwr-001", "to": "prp-003", "gauge_awg": 14}]},
}


def vtol(thrust: float = 20.0, cap: float = 5000, cant_deg: float = 30.0, z: float = 200.0, max_current: float = 20,
         discharge_c: float = 25) -> Design:
    """gates-base turned into a tailsitter with four lift motors (canted alternately for yaw) and a battery block."""
    d = copy.deepcopy(yaml.safe_load((FIX / "gates-base.yaml").read_text(encoding="utf-8")))
    for item in d["bom"]["items"]:
        item["verified"]["date"] = "2026-11-15"
    d["morphology"] = {"lift": "flying-wing", "vtol_method": "tailsitter"}
    d["flight"] = {"cl_max": 1.0, "cruise_ld": 8, "cruise_ld_source": "test fixture",
                   "transition_speed_mps": 15, "transition_speed_source": "test fixture"}
    d["requirements"]["cruise_speed_mps"] = 15
    d["components"] = [c for c in d["components"] if c["id"] != "motor_l"]
    d["attachments"] = [a for a in d["attachments"] if a["id"] != "motor-wing"]
    c = math.radians(cant_deg)
    for i, (y, zz) in enumerate([(-200, -z), (200, -z), (-200, z), (200, z)]):
        s = c if i % 2 == 0 else -c
        mid = f"motor_{i + 1}"
        d["components"].append({
            "id": mid, "type": "motor", "geometry": {"box": {"size": [30, 30, 30]}}, "position": [90, y, zz],
            "mass_g": 40, "manufacturing": {"method": "purchased"},
            "propulsion": {"max_thrust_n": thrust, "axis": [-math.cos(s), math.sin(s), 0], "role": "lift",
                           "max_current_a": max_current, "prop_diameter_mm": 230}})
        d["attachments"].append({"id": f"motor-{i + 1}-wing", "parent": "wing", "child": mid, "method": "bolted",
                                 "location": [90, y, zz], "rated_load_n": 50})
    for comp in d["components"]:
        if comp["id"] == "battery":
            comp["battery"] = {"capacity_mah": cap, "cells_s": 4, "max_discharge_c": discharge_c}
    d["bom"]["items"] = [b for b in d["bom"]["items"] if b["id"] != "motor"]
    d["wiring"]["harnesses"] = []
    d["assembly"]["sequence"][2]["add"] = ["far_pod"]
    return Design(d, path=FIX / "gates-base.yaml")


def base() -> Design:
    d = copy.deepcopy(yaml.safe_load((FIX / "gates-base.yaml").read_text(encoding="utf-8")))
    for item in d["bom"]["items"]:
        item["verified"]["date"] = "2026-11-15"
    return Design(d, path=FIX / "gates-base.yaml")


def run(design, tiers=(2, 3, 7), strict=True) -> Scorecard:
    return run_gates(design, only_tiers=set(tiers), strict=strict, today=TODAY)


def rows(card: Scorecard, check_id: str):
    return [r for t in card.tiers for r in t.results if r.check_id == check_id]


def statuses(card, check_id):
    return [r.status for r in rows(card, check_id)]


def connect(design: Design, ct: str = "CT-M3-SHCS-INSERT") -> Design:
    for a in design.data["attachments"]:
        a["connection"] = ct
        a["rating_basis"] = "placeholder"  # the joint's own rated_load_n is not a capacity, so T2.joint_rf reads the library (D50)
    return design


# ---- registry ----
def test_registry_matches_gates_yaml_discipline():
    hangar.gates._import_gates()
    table = load_discipline_table()
    assert {r["id"] for r in table} == set(DISCIPLINE)
    for r in table:
        assert DISCIPLINE[r["id"]].tier == r["tier"] and r["blocking"] is False


def test_duplicate_discipline_id_rejected():
    hangar.gates._import_gates()
    with pytest.raises(ValueError, match="duplicate discipline check id"):
        discipline_check("T2.joint_rf", 2)(lambda ctx, rep: [])


# ---- T2.joint_rf ----
def test_joint_rf_pass():
    rs = rows(run(connect(vtol()), tiers={2}), "T2.joint_rf")
    assert rs and {r.status for r in rs} == {PASS}


def test_joint_rf_fail():
    d = connect(vtol())
    d.component("far_pod")["mass_g"] = 30000
    rs = rows(run(d, tiers={2}), "T2.joint_rf")
    assert any(r.status == FAIL and "RF" in r.message for r in rs)


def test_joint_rf_skip_cases():
    rs = rows(run(vtol(), tiers={2}), "T2.joint_rf")
    assert [r.status for r in rs] == [SKIP] and "attachments[].connection" in rs[0].message
    rs = rows(run(connect(vtol(), "CT-PLUG-IN"), tiers={2}), "T2.joint_rf")
    assert rs and all(r.status == SKIP and "CT-PLUG-IN has no rated_load_n" in r.message for r in rs)


def _rf_rows(basis, rated, ct="CT-M3-SHCS-INSERT"):
    d = connect(vtol(), ct)
    for a in d.data["attachments"]:
        a["rated_load_n"] = rated
        if basis is None:
            a.pop("rating_basis")
        else:
            a["rating_basis"] = basis
    return rows(run(d, tiers={2}), "T2.joint_rf")


def test_joint_rf_uses_the_joints_own_rating():  # D50; the library rating of CT-M3-SHCS-INSERT is 1167 N
    rs = _rf_rows("sourced", 0.01)
    assert len(rs) == 8 and all(r.status == FAIL and r.data["rating_source"] == "joint" and "joint value" in r.message for r in rs)
    rs = _rf_rows("sourced", 100000)
    assert len(rs) == 8 and all(r.status == PASS and r.data["rating_source"] == "joint" for r in rs)
    rs = _rf_rows(None, 0.01)  # no rating_basis stated: the number is still the joint's own
    assert len(rs) == 8 and all(r.status == FAIL and r.data["rating_source"] == "joint" for r in rs)


def test_joint_rf_placeholder_rating_falls_back_to_the_library():
    rs = _rf_rows("placeholder", 0.01)
    assert len(rs) == 8 and all(r.status == PASS and r.data["rating_source"] == "library" for r in rs)
    rs = _rf_rows("placeholder", 0.01, "CT-PLUG-IN")  # the library has no rating either
    assert len(rs) == 8 and all(r.status == SKIP and "pending" in r.message for r in rs)


def test_joint_rf_derived_rating_is_reported_as_pending():
    for rated, would_be in ((0.01, FAIL), (100000, PASS)):
        rs = _rf_rows("derived", rated)
        assert len(rs) == 8
        for r in rs:
            assert r.status == SKIP and "pending" in r.message and "derived" in r.message
            assert r.data["would_be"] == would_be and r.data["rating_source"] == "joint"


def test_joint_own_rating_helper():
    from hangar.checks import joint_own_rating
    assert joint_own_rating({"rated_load_n": 5, "rating_basis": "placeholder"}) == (None, "placeholder")
    assert joint_own_rating({"rated_load_n": 5, "rating_basis": "derived"}) == (5, "derived")
    assert joint_own_rating({"rated_load_n": 5}) == (5, None)
    assert joint_own_rating({}) == (None, None)


# ---- T3.control_authority ----
def test_control_authority_pass():
    rs = rows(run(vtol(), tiers={3}), "T3.control_authority")
    assert sorted(r.data["axis"] for r in rs) == ["pitch", "roll", "yaw"]
    assert {r.status for r in rs} == {PASS}


def test_control_authority_fail():
    rs = rows(run(vtol(thrust=3.0), tiers={3}), "T3.control_authority")
    assert FAIL in {r.status for r in rs}


def test_control_authority_skips_non_vtol():
    rs = rows(run(base(), tiers={3}), "T3.control_authority")
    assert [r.status for r in rs] == [SKIP] and "not applicable" in rs[0].message


def _moment(r) -> float:
    return r.data["moment_nm"]      # T99: a data key, so the tests do not depend on the message wording


def _axis_row(design, axis):
    return next(r for r in rows(run(design, tiers={3}), "T3.control_authority") if r.data["axis"] == axis)


def _pinwheel(d: Design, cant_deg: float = 30.0) -> Design:
    """Cant follows the sign of each motor's z, so every motor's cant torque about the up axis has the same sign (a pinwheel)."""
    c = math.radians(cant_deg)
    for comp in d.data["components"]:
        if comp["type"] == "motor":
            s = c if comp["position"][2] > 0 else -c
            comp["propulsion"]["axis"] = [-math.cos(s), math.sin(s), 0]
    return d


def test_control_authority_pinwheel_cant_yaw_is_not_judged_and_never_passes():  # T37 (D58)
    row = _axis_row(_pinwheel(vtol()), "yaw")
    assert row.status == SKIP and row.data["would_be"] == FAIL and row.status != PASS
    assert "prop reaction torque is not modelled" in row.message and "conservative" in row.message
    assert abs(row.data["trim_yaw_nm"]) > 0.5       # equal thrust leaves an untrimmed yaw moment
    assert _moment(row) < 0.2 * abs(row.data["trim_yaw_nm"])     # the old sum of magnitudes gave a large number here
    assert {_axis_row(_pinwheel(vtol()), a).status for a in ("pitch", "roll")} <= {PASS, FAIL}


def test_control_authority_data_moment_matches_the_message():  # T99
    import re
    for axis in ("pitch", "roll", "yaw"):
        row = _axis_row(_pinwheel(vtol()), axis)
        assert row.data["moment_nm"] == float(re.search(r"control moment (-?[0-9.]+) N\*m", row.message).group(1)), axis


def test_control_authority_yaw_skip_says_when_hover_ctrl_factor_is_pending(monkeypatch):  # T99
    row = _axis_row(_pinwheel(vtol()), "yaw")
    assert row.status == SKIP and "is pending" not in row.message      # sourced criterion: the text is unchanged
    real = hangar.gates.discipline._crit
    monkeypatch.setattr(hangar.gates.discipline, "_crit",
                        lambda f, k: (real(f, k)[0], True) if k == "hover_ctrl_factor" else real(f, k))
    row = _axis_row(_pinwheel(vtol()), "yaw")
    assert row.status == SKIP and row.data["would_be"] == FAIL
    assert "operations.yaml#hover_ctrl_factor is pending" in row.message and "prop reaction torque is not modelled" in row.message


def test_control_authority_equal_pitch_lever_gives_zero_pitch_moment():  # T37 (D58)
    d = vtol(cant_deg=0.0)
    d.data["components"] = [c for c in d.data["components"] if c["id"] not in ("motor_3", "motor_4")]   # both left at the same height
    d.data["attachments"] = [a for a in d.data["attachments"] if a["id"] not in ("motor-3-wing", "motor-4-wing")]
    assert _moment(_axis_row(d, "pitch")) == 0.0


def test_control_authority_alternating_cant_still_passes_yaw():  # T37 (D58): the vtol fixture alternates its cant
    row = _axis_row(vtol(), "yaw")
    assert row.status == PASS and abs(row.data["trim_yaw_nm"]) < 1e-6


@pytest.mark.slow
def test_control_authority_concept_a_yaw_trim():  # T37 (D58): the drawn cant is a uniform pinwheel
    row = _axis_row(load_design(CONCEPT_A), "yaw")
    assert row.status == SKIP and row.data["would_be"] == FAIL
    assert row.data["trim_yaw_nm"] == pytest.approx(-1.06, abs=0.02)
    assert _moment(row) == pytest.approx(0.014, abs=0.005)


def _spin(d: Design, spins=("cw", "ccw", "cw", "ccw"), kq: float = 0.02) -> Design:
    """T95: the PDL 1.1 reaction-torque fields on the four lift motors motor_1..motor_4."""
    d.data["schema_version"] = "1.1"
    for i, s in enumerate(spins):
        d.component(f"motor_{i + 1}")["propulsion"].update(spin=s, torque_per_thrust_m=kq, torque_per_thrust_m_source="test fixture")
    return d


def test_yaw_with_reaction_torque_is_judged_not_skipped():  # T95
    tiny = _axis_row(_spin(_pinwheel(vtol()), kq=0.0001), "yaw")
    assert tiny.status == FAIL and "would_be" not in tiny.data
    assert "cant geometry and prop reaction torque" in tiny.message and "not modelled" not in tiny.message
    big = _axis_row(_spin(_pinwheel(vtol()), kq=0.2), "yaw")
    assert big.status == PASS and "would_be" not in big.data
    assert _moment(big) > 1.4 and _moment(tiny) < 0.05
    assert big.data["trim_yaw_nm"] == pytest.approx(0.838, abs=0.01)      # alternating spins add no net torque at equal thrust


def test_yaw_moment_from_reaction_torque_alone_scales_with_kq():  # T95: cant 0, so the cant-only yaw moment is 0
    assert _moment(_axis_row(vtol(cant_deg=0.0), "yaw")) == 0.0
    m1 = _moment(_axis_row(_spin(vtol(cant_deg=0.0), kq=0.02), "yaw"))
    m2 = _moment(_axis_row(_spin(vtol(cant_deg=0.0), kq=0.04), "yaw"))
    assert m1 == pytest.approx(0.145, abs=0.005) and m2 == pytest.approx(2 * m1, rel=0.01)


def test_yaw_reaction_trim_sign_follows_the_spin_direction():  # T95: cw adds +axis, ccw -axis, all one way gives no differential
    cw = _axis_row(_spin(vtol(cant_deg=0.0), spins=("cw",) * 4), "yaw")
    ccw = _axis_row(_spin(vtol(cant_deg=0.0), spins=("ccw",) * 4), "yaw")
    assert cw.data["trim_yaw_nm"] == pytest.approx(0.145, abs=0.005) and ccw.data["trim_yaw_nm"] == pytest.approx(-cw.data["trim_yaw_nm"])
    assert _moment(cw) == 0.0 and _moment(ccw) == 0.0
    assert abs(_axis_row(_spin(vtol(cant_deg=0.0)), "yaw").data["trim_yaw_nm"]) < 1e-6


def test_pitch_and_roll_ignore_the_reaction_fields():  # T95: only the yaw row uses them
    for axis in ("pitch", "roll"):
        assert _moment(_axis_row(_spin(_pinwheel(vtol())), axis)) == _moment(_axis_row(_pinwheel(vtol()), axis))


@pytest.mark.parametrize("missing", ["spin", "torque_per_thrust_m", "torque_per_thrust_m_source"])
def test_yaw_stays_not_judged_when_any_motor_lacks_a_reaction_field(missing):  # T95: the D58 SKIP is kept
    d = _spin(_pinwheel(vtol()))
    del d.component("motor_2")["propulsion"][missing]
    row = _axis_row(d, "yaw")
    assert row.status == SKIP and row.data["would_be"] == FAIL
    assert f"motor motor_2: propulsion.{missing} missing" in row.message and "prop reaction torque is not modelled" in row.message


# ---- T3.transition_margin ----
def _stall(design) -> float:
    return rows(run(design, tiers={3}), "T3.stall")[0].data["stall_mps"]


def _speed_row(design):
    return next(r for r in rows(run(design, tiers={3}), "T3.transition_margin") if r.message.startswith("speed margin"))


def _thrust_row(design):
    return next(r for r in rows(run(design, tiers={3}), "T3.transition_margin")
                if r.message.startswith("entry thrust fraction"))


def test_transition_pass():
    speed = _speed_row(vtol())
    assert speed.status == SKIP and speed.data["would_be"] == PASS  # criterion is pending, so never PASS
    assert _thrust_row(vtol()).status == PASS


def test_transition_fail():
    d = vtol()
    d.data["flight"]["transition_speed_mps"] = round(1.19 * _stall(d), 2)  # just under 1.2 x stall
    speed = _speed_row(d)
    assert speed.status == SKIP and speed.data["would_be"] == FAIL
    assert _thrust_row(vtol(thrust=2.6)).status == FAIL


def test_transition_not_applicable_skips():
    rs = rows(run(base(), tiers={3}), "T3.transition_margin")
    assert [r.status for r in rs] == [SKIP] and "not applicable" in rs[0].message


def test_transition_missing_source_skips():
    d = vtol()
    del d.data["flight"]["transition_speed_source"]
    speed = _speed_row(d)
    assert speed.status == SKIP and "flight.transition_speed_source" in speed.message


# ---- T3.endurance ----
def test_endurance_pass():
    assert statuses(run(vtol(cap=5000), tiers={3}), "T3.endurance") == [PASS]


def test_endurance_fail():
    rs = rows(run(vtol(cap=200), tiers={3}), "T3.endurance")
    assert [r.status for r in rs] == [FAIL] and "Wh" in rs[0].message


def test_endurance_skip_without_battery_block():
    d = vtol()
    del d.component("battery")["battery"]
    rs = rows(run(d, tiers={3}), "T3.endurance")
    assert [r.status for r in rs] == [SKIP] and "components[].battery" in rs[0].message


def test_endurance_skip_without_prop_diameter():
    d = vtol()
    del d.component("motor_1")["propulsion"]["prop_diameter_mm"]
    rs = rows(run(d, tiers={3}), "T3.endurance")
    assert [r.status for r in rs] == [SKIP] and "motor_1" in rs[0].message and "prop_diameter_mm" in rs[0].message


def test_endurance_skip_without_cruise_ld_source():
    d = vtol()
    del d.data["flight"]["cruise_ld_source"]
    rs = rows(run(d, tiers={3}), "T3.endurance")
    assert [r.status for r in rs] == [SKIP] and "flight.cruise_ld_source" in rs[0].message


# ---- T7.electrical_rating ----
def test_electrical_rating_pass():
    rs = rows(run(vtol(), tiers={7}), "T7.electrical_rating")  # 5 Ah x 25 C = 125 A >= 4 x 20 A
    assert [r.status for r in rs] == [PASS] and rs[0].data["parts"] == ["battery"]


def test_electrical_rating_fail():
    rs = rows(run(vtol(max_current=40), tiers={7}), "T7.electrical_rating")  # 160 A > 125 A
    assert [r.status for r in rs] == [FAIL]


def _harness(d: Design, gauge) -> Design:
    d.data["wiring"]["harnesses"] = [{"id": "hrn-bat", "from": "battery", "to": "esc", "gauge_awg": gauge}]
    return d


def _wire_rows(d):
    return [r for r in rows(run(d, tiers={7}), "T7.electrical_rating") if "hrn-bat" in r.message]


def _disconnect_rows(d):
    for a in d.data["attachments"]:
        if a["id"] == "battery-bay":
            a["connection"] = "CT-XT60"
    return [r for r in rows(run(d, tiers={7}), "T7.electrical_rating") if r.message.startswith("disconnect")]


def test_electrical_rating_skips():
    d = vtol()
    del d.component("motor_3")["propulsion"]["max_current_a"]
    rs = rows(run(d, tiers={7}), "T7.electrical_rating")
    assert [r.status for r in rs] == [SKIP] and "motor_3" in rs[0].message and "max_current_a" in rs[0].message
    rs = _wire_rows(_harness(vtol(), 13))
    assert [r.status for r in rs] == [SKIP] and "13 AWG" in rs[0].message
    assert [r.status for r in _wire_rows(_harness(vtol(max_current=5), 12))] == [PASS]   # 20 A <= 55 x 0.8 A
    assert [r.status for r in _wire_rows(_harness(vtol(max_current=15), 14))] == [FAIL]  # 60 A > 45 x 0.8 A
    assert [r.status for r in _disconnect_rows(vtol(max_current=5))] == [PASS]           # 20 A <= 30 A
    assert [r.status for r in _disconnect_rows(vtol(max_current=10))] == [FAIL]          # 40 A > 30 A


# ---- report-only, pending, no data ----
def test_discipline_rows_are_report_only():
    d = vtol(thrust=3.0)
    soft = rows(run(d, tiers={3}, strict=False), "T3.control_authority")
    assert soft and all(r.status == WARN and r.data["report_only"] is True for r in soft)
    assert any(r.data["raw_status"] == "FAIL" for r in soft)
    assert all(r.message.startswith("report-only until 2026-12-08: ") for r in soft)
    assert FAIL in statuses(run(d, tiers={3}, strict=True), "T3.control_authority")


def test_pending_criterion_skips_never_passes(monkeypatch):
    real = hangar.gates.discipline.resolve_threshold

    def fake(crit):
        th = real(crit)
        return {**th, "source": "pending"} if crit == "operations.yaml#hover_ctrl_factor" else th

    monkeypatch.setattr(hangar.gates.discipline, "resolve_threshold", fake)
    rs = rows(run(vtol(), tiers={3}), "T3.control_authority")
    assert rs and all(r.status == SKIP and "would_be" in r.data for r in rs)
    assert all("not judged: operations.yaml#hover_ctrl_factor pending" in r.message for r in rs)


def test_no_gate_passes_without_data():
    card = run(base())
    for cid in IDS:
        assert PASS not in statuses(card, cid), cid


def test_fidelity_ignores_report_only_discipline_rows(monkeypatch):
    d = vtol()
    strict = run(d, tiers={3}, strict=True).fidelity["blocking"]
    assert run(d, tiers={3}, strict=False).fidelity["blocking"] == strict
    monkeypatch.setattr(hangar.gates, "DISCIPLINE", {})
    assert run(d, tiers={3}, strict=True).fidelity["blocking"] == strict


def test_explain_discipline_id():
    r = call("gate.explain", check_id="T3.control_authority")
    assert r.ok and r.data["blocking"] is False and r.data["criterion"] == "operations.yaml#hover_ctrl_factor"


def test_gate_list_has_15_rows():
    assert call("gate.list").data["count"] == 21


# ---- concept-a (D21 values in memory; on disk once the design PR lands) ----
def _concept_a_d21(data: dict) -> dict:
    s = CONCEPT_A_D21
    data["schema_version"] = s["schema_version"]
    for c in data["components"]:
        if c["id"] in s["battery"]:
            c["battery"] = dict(s["battery"][c["id"]])
        if c["id"] in s["motors"]:
            c["propulsion"].update(s["motor_fields"])
    data["flight"].update(s["flight"])
    for a in data["attachments"]:
        if a.get("id") in s["connection"]:
            a["connection"] = s["connection"][a["id"]]
    data["wiring"] = copy.deepcopy(s["wiring"])
    return data


def _check_concept_a(design: Design):
    card = run(design, tiers={2, 3, 7})
    for cid in IDS:
        rs = rows(card, cid)
        assert any(r.status in (PASS, FAIL) for r in rs), (cid, [(r.status, r.message) for r in rs])
        for r in rs:
            if r.status == SKIP:
                assert "pending" in r.message, (cid, r.message)
    wire = [r for r in rows(card, "T7.electrical_rating") if "hrn-bat" in r.message]
    assert wire and wire[0].status in (PASS, FAIL)


@pytest.mark.slow
def test_concept_a_d21_in_memory():
    d = load_design(CONCEPT_A)
    _check_concept_a(Design(_concept_a_d21(copy.deepcopy(d.data)), path=d.path))


def _on_disk_has_battery() -> bool:
    data = yaml.safe_load((CONCEPT_A / "plane.yaml").read_text(encoding="utf-8"))
    return any(c["id"] == "pwr-001" and "battery" in c for c in data["components"])


D21_LEAVES = ("capacity_mah", "cells_s", "max_discharge_c", "max_current_a", "prop_diameter_mm", "cruise_ld",
              "cruise_ld_source", "transition_speed_mps", "transition_speed_source", "gauge_awg", "connection", "battery")


def _d21_leaves_set(data: dict) -> set:
    """Names of the D21 fields that the design file sets (components[].battery and its keys, propulsion, flight, harnesses, attachments)."""
    out = set()
    for c in data["components"]:
        if "battery" in c:
            out |= {"battery"} | set(c["battery"])
        out |= set(c.get("propulsion", {}))
    out |= set(data.get("flight", {}))
    harnesses = data.get("wiring", {}).get("harnesses", [])
    if harnesses:  # a harness field counts as set only when every harness sets it: a SKIP may name it for the one that does not
        out |= set.intersection(*(set(h) for h in harnesses))
    for a in data.get("attachments", []):
        out |= set(a)
    return out & set(D21_LEAVES)


def _names(field: str, message: str) -> bool:
    """True when `message` names `field` as a word. A file name such as connection-types.yaml does not name `connection`."""
    import re
    return re.search(rf"(?<![\w-]){field}(?![\w-])", message) is not None


def test_d39_detector_names_fields_not_file_names():
    assert not _names("connection", "E-WNG-02: CT-EPOXY has no rated_load_n in standards/connection-types.yaml")
    assert _names("connection", "x: connection CT-FOO not in standards/connection-types.yaml")
    assert _names("gauge_awg", "e-hrn-01: wiring.harnesses[].gauge_awg missing")


def test_d39_harness_field_counts_as_set_only_when_every_harness_sets_it():
    data = {"components": [], "attachments": [], "flight": {}, "wiring": {"harnesses": [{"id": "a", "gauge_awg": 14}, {"id": "b"}]}}
    assert "gauge_awg" not in _d21_leaves_set(data)
    data["wiring"]["harnesses"][1]["gauge_awg"] = 12
    assert "gauge_awg" in _d21_leaves_set(data)


def _check_d21_fields_read(design: Design) -> set:
    """D39: every discipline gate gave a row, and no SKIP row names a D21 field the design sets. No verdict is asserted."""
    leaves = _d21_leaves_set(design.data)
    card = run(design, tiers={2, 3, 7})
    for cid in IDS:
        rs = rows(card, cid)
        assert rs, f"{cid}: the gate gave no row"
        for r in rs:
            if r.status == SKIP:
                named = sorted(k for k in leaves if _names(k, r.message))
                assert not named, f"{cid}: SKIP names a field that is set {named}: {r.message}"
    return leaves


@pytest.mark.slow
@pytest.mark.skipif(not _on_disk_has_battery(), reason="concept-a pwr-001 has no battery block yet (design PR)")
def test_concept_a_d21_on_disk():
    _check_d21_fields_read(load_design(CONCEPT_A))


# ---- criteria and existing rows ----
def test_existing_gate_rows_criteria_resolve():
    for row in [*load_gate_table(), *load_discipline_table()]:
        crit = row["criterion"]
        if "#" in crit:
            assert resolve_threshold(crit) is not None, crit
        else:
            assert (REPO_ROOT / crit).exists() or (REPO_ROOT / "standards" / crit).exists(), crit


def _ids(card):
    return [r.check_id for t in card.tiers for r in t.results]


def test_existing_gate_rows_fire():
    ids = _ids(run(base(), tiers={3, 7, 8, 9}))
    for cid in ("T3.mass", "T7.assembly.once"):
        assert cid in ids
    for prefix in ("T7.wiring.", "T7.transport.", "T8."):
        assert any(i.startswith(prefix) for i in ids), prefix


@pytest.mark.slow
def test_existing_gate_rows_fire_concept_a():
    ids = _ids(run(load_design(CONCEPT_A), tiers={1, 3, 9}))
    for cid in ("T1.interference", "T3.static_margin", "T3.hover_tw"):
        assert cid in ids, cid


# ---- design set on the new battery fields (moved from U3.6-2 test 8) ----
def test_add_battery_pair_is_inserts_only(tmp_path):
    dst = tmp_path / "concept-a"
    shutil.copytree(CONCEPT_A_FROZEN, dst, ignore=shutil.ignore_patterns("fea"))
    plane = dst / "plane.yaml"
    old = plane.read_text(encoding="utf-8").splitlines()
    r = call("design.set", path=str(dst), key="components[pwr-001].battery.capacity_mah", value="2300",
             why="d21", kind="add", also=["components[pwr-001].battery.cells_s=4"])
    assert r.ok, r.messages
    new = plane.read_text(encoding="utf-8").splitlines()
    tags = {t for t, *_ in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes()}
    assert tags <= {"equal", "insert"} and "insert" in tags
