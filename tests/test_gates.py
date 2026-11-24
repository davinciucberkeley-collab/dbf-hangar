"""Gate registry, T6 mechanisms, T7 integration, T8 sourcing, the fidelity line and the unknown-type SKIP (U2.1)."""
from __future__ import annotations

import copy
import datetime
import re
from pathlib import Path

import pytest
import yaml

import hangar.gates.sourcing
from hangar.baseline import compare, read_baseline, snapshot
from hangar.checks import validate
from hangar.design import DESIGNS_DIR, FAIL, PASS, REPO_ROOT, SKIP, WARN, Design, Scorecard, load_design, load_standards
from hangar.gates import GATES, load_gate_table, load_gate_thresholds, run_gates

FIX = Path(__file__).parent / "fixtures"
TODAY = datetime.date(2026, 11, 20)
EXAMPLE = DESIGNS_DIR / "example-tailsitter-wing"


def result(card: Scorecard, check_id: str):
    for t in card.tiers:
        for r in t.results:
            if r.check_id == check_id:
                return r
    raise KeyError(check_id)


def run(d, **kw) -> Scorecard:
    design = d if isinstance(d, Design) else load_design(d)
    kw.setdefault("today", TODAY)
    return run_gates(design, **kw)


def status(d, check_id, *, tiers, strict=True) -> str:
    return result(run(d, only_tiers=set(tiers), strict=strict), check_id).status


def base() -> Design:
    data = copy.deepcopy(yaml.safe_load((FIX / "gates-base.yaml").read_text(encoding="utf-8")))
    for item in data["bom"]["items"]:
        item["verified"]["date"] = "2026-11-15"
    return Design(data, path=FIX / "gates-base.yaml")


def test_linked_flap_follows_servo():
    assert status(FIX / "mech-good.yaml", "T6.mechanism.flap_l", tiers={6}) == PASS


def test_jammed_linkage_fails_with_step():
    r = result(run(FIX / "mech-jammed.yaml", only_tiers={6}), "T6.mechanism.flap_l")
    assert r.status == FAIL and "deg" in r.message and "input" in r.message


def test_undriven_joint_warns():
    p = FIX / "mech-unlinked.yaml"
    for j in ("tilt", "flap_hinge", "servo_arm"):
        assert status(p, f"T6.undriven.{j}", tiers={6}) == WARN


def test_exposed_wire_fails_unless_reasoned():
    wire_outside = base()
    wire_outside.data["wiring"]["harnesses"][0]["route"] = ["far_pod"]
    assert status(wire_outside, "T7.wiring.esc_to_motor_l", tiers={7}) == FAIL
    wire_outside_ok = base()
    h = wire_outside_ok.data["wiring"]["harnesses"][0]
    h["route"] = ["far_pod"]
    h["exposed_ok"] = {"reason": "inspection hatch"}
    assert status(wire_outside_ok, "T7.wiring.esc_to_motor_l", tiers={7}) == PASS
    assert status(base(), "T7.wiring.esc_to_motor_l", tiers={7}) == PASS


def _as_point_masses(d, *ids):
    for c in d.data["components"]:
        if c["id"] in ids:
            c["geometry"] = {"point_mass": {}}
    return d


def test_harness_between_point_masses_is_skip_not_pass():  # T15
    d = _as_point_masses(base(), "esc", "far_pod")
    d.data["wiring"]["harnesses"].append({"id": "pm_pm", "from": "esc", "to": "far_pod"})
    r = result(run(d, only_tiers={7}, strict=True), "T7.wiring.pm_pm")
    assert r.status == SKIP
    assert "point mass" in r.message
    assert status(d, "T7.wiring.esc_to_motor_l", tiers={7}) == PASS


def test_harness_from_a_point_mass_to_a_mesh_is_still_checked():  # T15
    d = _as_point_masses(base(), "esc")
    d.data["wiring"]["harnesses"].append({"id": "pm_body", "from": "esc", "to": "body"})
    assert status(d, "T7.wiring.pm_body", tiers={7}) == PASS


def test_harness_with_a_point_mass_segment_and_a_checked_segment_passes_and_says_so():  # T86 (W6-R: mixed harness)
    d = _as_point_masses(base(), "esc", "battery")
    d.data["wiring"]["harnesses"].append({"id": "mixed", "from": "esc", "route": ["battery"], "to": "body"})   # esc-battery: point mass to point mass; battery-body: checked
    r = result(run(d, only_tiers={7}, strict=True), "T7.wiring.mixed")
    assert r.status == PASS
    assert "all 1 checked segments" in r.message and "1 segment(s) between point masses not checked" in r.message


def test_harness_with_a_point_mass_segment_still_fails_on_its_checked_segment():  # T86 (W6-R: a point-mass segment must not hide a bad one)
    d = _as_point_masses(base(), "esc", "battery")
    d.data["wiring"]["harnesses"].append({"id": "mixed_far", "from": "esc", "route": ["battery"], "to": "far_pod"})   # battery-far_pod leaves every envelope
    r = result(run(d, only_tiers={7}, strict=True), "T7.wiring.mixed_far")
    assert r.status == FAIL
    assert "segment battery to far_pod" in r.message


def test_transport_group_of_only_point_masses_is_skip():  # T15
    d = _as_point_masses(base(), "esc")
    d.data["transport"]["disassembly"].append({"group": "pm_only", "component_ids": ["esc"]})
    r = result(run(d, only_tiers={7}, strict=True), "T7.transport.pm_only")
    assert r.status == SKIP
    assert "point mass" in r.message


def test_transport_group_too_big_fails():
    wing_too_long = base()
    wing_too_long.data["components"][1]["geometry"]["lifting_surface"]["span"] = 1400
    assert status(wing_too_long, "T7.transport.wing", tiers={7}) == FAIL
    assert status(base(), "T7.transport.wing", tiers={7}) == PASS


def test_stale_bom_line_fails():
    bom_stale = base()
    bom_stale.data["bom"]["items"][1]["verified"]["date"] = "2026-01-01"
    r = result(run(bom_stale, only_tiers={8}, strict=True), "T8.bom.verified.motor")
    assert r.status == FAIL and "days ago" in r.message
    assert status(base(), "T8.bom.verified.motor", tiers={8}) == PASS


_COMMITTED = sorted(p.parent for p in DESIGNS_DIR.glob("*/baseline.json"))


def _tier_of(check_id):
    m = re.match(r"T(\d+)", check_id)
    return int(m.group(1)) if m else 0


def _baseline_up_to_tier_5(baseline):
    """The baseline restricted to tiers 0-5, since this test runs the gates only to tier 5."""
    if baseline is None:
        return None
    m = dict(baseline)
    m["known"] = [e for e in baseline.get("known", []) if _tier_of(e["check_id"]) <= 5]
    if "tiers_run" in baseline:
        m["tiers_run"] = [n for n in baseline["tiers_run"] if n <= 5]
    return m


@pytest.mark.parametrize("d", _COMMITTED, ids=[p.name for p in _COMMITTED])
def test_tiers_0_5_unchanged_for_committed_designs(d):
    card = run_gates(load_design(d), 5)
    assert compare(snapshot(card), _baseline_up_to_tier_5(read_baseline(d)))["regressions"] == []


def test_scorecard_reports_fidelity():
    card = run_gates(load_design(EXAMPLE), only_tiers={0})
    f = card.fidelity
    assert {"sourced_blocking", "blocking", "measured_mass_parts"} <= f.keys()
    assert all(isinstance(v, int) for v in f.values())
    assert f["sourced_blocking"] <= f["blocking"]
    assert "Fidelity: " in card.to_markdown()
    assert "fidelity" in card.to_dict()


def test_registry_matches_gates_yaml():
    run_gates(load_design(EXAMPLE), only_tiers={0})
    table = load_gate_table()
    assert {g["id"] for g in table} == set(GATES)
    assert sorted(g["tier"] for g in table) == list(range(10))
    from hangar.checks import TIER_CRITERION
    for g in table:
        assert GATES[g["id"]].tier == g["tier"]
        assert isinstance(g["needs"], list)
        if 1 <= g["tier"] <= 5:
            assert g["criterion"] == TIER_CRITERION[g["tier"]]
    blocking = {g["tier"]: g["blocking"] for g in table}
    assert blocking[7] is False and blocking[8] is False and blocking[6] is True and blocking[9] is True


def test_report_only_gates_warn_by_default():
    wire_outside = base()
    wire_outside.data["wiring"]["harnesses"][0]["route"] = ["far_pod"]
    card = run(wire_outside, only_tiers={7})
    r = result(card, "T7.wiring.esc_to_motor_l")
    assert r.status == WARN and r.data["raw_status"] == FAIL and r.message.startswith("report-only")
    assert next(t for t in card.tiers if t.tier == 7).status == WARN


def test_thresholds_have_source():
    th = load_gate_thresholds()
    for k, v in th.items():
        assert v["value"] not in (None, "", []) and v["rule"] and v["source"], k
    assert th["wire_clearance_mm"]["source"] == "pending"
    std = load_standards()
    flat = {k for grp in std.values() if isinstance(grp, dict) for k in grp} | set(std)
    assert not set(th) & flat


def test_unknown_type_is_skip_naming_the_type():
    d = base()
    d.data["components"][0]["type"] = "wingletz"
    card = run(d, max_tier=1, only_tiers={0})
    t0 = card.tiers[0]
    assert t0.status == SKIP
    row = next(r for r in t0.results if r.check_id == "T0.component_type")
    assert "wingletz" in row.message and "body" in row.message
    assert not any(r.status == FAIL for r in t0.results if r.check_id == "T0.schema")
    card3 = run(d, max_tier=3)
    assert len(card3.tiers) > 1 and not card3.accepted
    bad = base()
    bad.data["requirements"]["mtow_g"] = -5
    assert any(r.check_id == "T0.schema" and r.status == FAIL for r in run(bad, max_tier=0).tiers[0].results)


def test_no_blocks_no_t6_and_only_discipline_t7():
    card = run(load_design(EXAMPLE), only_tiers={6, 7})
    assert not [t for t in card.tiers if t.tier == 6]
    t7 = [r for t in card.tiers if t.tier == 7 for r in t.results]
    assert all(r.check_id == "T7.electrical_rating" and r.status == WARN for r in t7)
    t8 = next(t for t in run(load_design(EXAMPLE), only_tiers={8}).tiers if t.tier == 8)
    assert [r.check_id for r in t8.results] == ["T8.program.budget"] and t8.results[0].status == WARN


def test_t9_registered_and_runs_through_registry():
    card = run(load_design(FIX / "claims-mini"), only_tiers={9})
    t9 = next(t for t in card.tiers if t.tier == 9)
    assert next(r for r in t9.results if r.check_id == "T9.claim.CL-MASS-GATE").status == FAIL


def test_gate_ops():
    from hangar.ops import call, registry
    assert {"gate.list", "gate.explain", "sim.mechanism"} <= set(registry())
    r = call("gate.list")
    assert r.ok and r.data["count"] == 17
    r = call("gate.explain", check_id="T7.wiring.x")
    assert r.ok and r.data["blocking"] is False and r.data["threshold"]["source"] == "pending"
    assert call("gate.explain", check_id="Q1.x").exit_code == 2


def test_gate_explain_exact_check_id_with_design():  # T26
    from hangar.ops import call
    assert call("gate.explain", check_id="T1.attachment").data["threshold"]["key"] == "interference_max_mm3"   # tier-level answer, unchanged
    r = call("gate.explain", check_id="T1.attachment", design=str(EXAMPLE))
    assert r.ok and r.data["exact"] is True and r.data["check_id"] == "T1.attachment"
    assert r.data["criterion"] == "design-standards.yaml#attach_tolerance_mm"
    assert r.data["threshold"]["key"] == "attach_tolerance_mm"
    bad = call("gate.explain", check_id="T1.nope", design=str(EXAMPLE))
    assert bad.exit_code == 2 and "T1.attachment" in " ".join(bad.messages)
    assert call("gate.explain", check_id="T3.control_authority", design=str(EXAMPLE)).data["criterion"] == "operations.yaml#hover_ctrl_factor"


def test_gate_explain_explains_a_fail_only_check_id_on_a_passing_design():  # T83
    from hangar.ops import call
    from hangar.ops.gates import FAIL_ONLY_CRITERIA
    r = call("gate.explain", check_id="T1.attachment_contact", design=str(EXAMPLE))
    assert r.ok and r.data["exact"] is True and r.data["check_id"] == "T1.attachment_contact"
    assert r.data["criterion"] == "design-standards.yaml#attach_tolerance_mm"
    assert r.data["threshold"]["key"] == "attach_tolerance_mm"
    for cid, criteria in FAIL_ONLY_CRITERIA.items():   # every id a run emits only on FAIL, on a design that passes
        r = call("gate.explain", check_id=cid, design=str(EXAMPLE))
        assert r.ok and r.data["exact"] is True and r.data["check_id"] == cid, (cid, r.messages)
        assert [c["criterion"] for c in r.data["checks"]] == list(criteria), cid
        assert r.data["criterion"] == criteria[0], cid
    r = call("gate.explain", check_id="T0.root", design=str(EXAMPLE))
    assert r.data["threshold"] is None   # a schema rule has no number behind it
    assert call("gate.explain", check_id="T1.attachment_overlap", design=str(EXAMPLE)).data["checks"][1]["threshold"]["key"] == "glued_overlap_max_fraction"
    assert call("gate.explain", check_id="T1.nope", design=str(EXAMPLE)).exit_code == 2   # unknown ids are still refused


def test_fail_only_criteria_table_matches_checks_py_and_the_gates_package():  # T83 guard (T100: gates/*.py too): the table cannot drift
    from hangar import checks
    from hangar.ops.gates import FAIL_ONLY_CRITERIA
    files = [Path(checks.__file__), *sorted((Path(checks.__file__).parent / "gates").glob("*.py"))]
    assert Path(checks.__file__).parent / "gates" / "claims.py" in files
    src = "\n".join(f.read_text(encoding="utf-8") for f in files)
    statuses = {}
    for m in re.finditer(r'CheckResult\(\s*"(T\d+\.[A-Za-z_0-9.]+)",\s*([^,]+?),', src):
        statuses.setdefault(m.group(1), set()).add(m.group(2).strip())
    assert {cid for cid, s in statuses.items() if s == {"FAIL"}} == set(FAIL_ONLY_CRITERIA)   # no FAIL-only id left out, none listed that can pass
    for criteria in FAIL_ONLY_CRITERIA.values():
        for criterion in criteria:
            assert (f'STD + "{criterion.split("#")[1]}"' if criterion.startswith("design-standards.yaml#") else f'"{criterion}"') in src, criterion


def test_gate_explain_explains_t9_claims_load_on_a_passing_design():  # T100
    from hangar.ops import call
    r = call("gate.explain", check_id="T9.claims.load", design=str(EXAMPLE))
    assert r.ok and r.data["exact"] is True and r.data["criterion"] == "claims.yaml#recompute_rel_tol"


def test_scorecard_lists_the_bare_manufacturing_file_as_a_criterion_form():  # T100: T4.machine cites manufacturing.yaml with no #<machine id>
    text = (REPO_ROOT / "standards" / "review-scorecard.md").read_text(encoding="utf-8")
    assert "`manufacturing.yaml` (the whole file, when a check is about the list of machines itself" in text


def test_design_engineer_doc_explains_with_the_design():  # T83
    text = (REPO_ROOT / ".claude" / "agents" / "design-engineer.md").read_text(encoding="utf-8")
    assert "plane gate explain <check_id> --design designs/<id>" in text


def test_sim_mechanism_op_returns_steps():
    from hangar.ops import call
    r = call("sim.mechanism", path=str(FIX / "mech-good.yaml"), mechanism_id="flap_l")
    assert r.ok
    steps = r.data["steps"]
    assert len(steps) == 21 and steps[-1]["input_deg"] == 20
    assert abs(steps[-1]["followers"]["flap_hinge"] - 20) < 1.5
    assert call("sim.mechanism", path=str(FIX / "mech-good.yaml"), mechanism_id="nope").exit_code == 2


def test_validate_wrapper_unchanged_for_legacy_tiers():
    c0 = validate(load_design(EXAMPLE), max_tier=0)
    assert len(c0.tiers) == 1 and c0.max_tier == 0 and c0.partial is True
    assert validate(load_design(EXAMPLE)).max_tier == 9


def test_program_budget_row_when_file_exists(monkeypatch, tmp_path):
    assert result(run(base(), only_tiers={8}, strict=True), "T8.program.budget").status == PASS
    tmp = tmp_path / "program.yaml"
    tmp.write_text(yaml.safe_dump({"constraints": {"budget_usd": {"value": 10, "rule": "t", "source": "test fixture"}}}),
                   encoding="utf-8")
    monkeypatch.setattr(hangar.gates.sourcing, "PROGRAM_PATH", tmp)
    assert result(run(base(), only_tiers={8}, strict=True), "T8.program.budget").status == FAIL
    monkeypatch.undo()
    nobom = base()
    del nobom.data["bom"]
    r = result(run(nobom, only_tiers={8}, strict=True), "T8.program.budget")
    assert r.status == SKIP and r.message == "no BOM: budget not checked"
    r = result(run(nobom, only_tiers={8}), "T8.program.budget")
    assert r.status == WARN and r.data["raw_status"] == SKIP


def test_program_budget_row_absent_without_file(monkeypatch, tmp_path):
    monkeypatch.setattr(hangar.gates.sourcing, "PROGRAM_PATH", tmp_path / "missing.yaml")
    with pytest.raises(KeyError):
        result(run(base(), only_tiers={8}), "T8.program.budget")
    nobom = base()
    del nobom.data["bom"]
    assert not [t for t in run(nobom, only_tiers={8}).tiers if t.tier == 8]


def test_program_yaml_every_constraint_has_source_or_pending():
    prog = yaml.safe_load((REPO_ROOT / "standards" / "program.yaml").read_text(encoding="utf-8"))
    assert prog["schema"] == "program/1"
    keys = {"budget_usd", "deadline", "mass_cap_kg", "transport_pieces_max", "transport_box_mm",
            "physics_pass", "cad_real_parts", "exposed_wiring_minimised"}
    c = prog["constraints"]
    assert set(c) == keys
    for k, v in c.items():
        assert v.get("value") not in (None, "") and v.get("rule") and v.get("source"), k
        assert "team constraint" in v["source"] or v["source"] == "pending", k
    assert c["budget_usd"]["value"] == 2000 and c["mass_cap_kg"]["value"] == 25
    assert c["transport_box_mm"]["value"] == [1250, 550, 450]


def _active_designs():
    out = []
    for p in sorted(DESIGNS_DIR.glob("*/plane.yaml")):
        if yaml.safe_load(p.read_text(encoding="utf-8")).get("status") != "retired":
            out.append(p.parent)
    return out


@pytest.mark.slow
@pytest.mark.parametrize("d", _active_designs(), ids=[p.name for p in _active_designs()])
def test_program_constraints_apply_to_every_active_design(d):
    card = validate(load_design(d), max_tier=8)
    assert "T8.program.budget" in {r.check_id for t in card.tiers for r in t.results}
