"""U17.1 2b (D91 b): a `team constraint` source counts as sourced only with a named owner and an ISO date."""
from __future__ import annotations

import datetime
import json
from types import SimpleNamespace

import yaml

import hangar.gates.fidelity as fid
from hangar.design import PASS, REPO_ROOT, CheckResult, TierReport
from hangar.gates.fidelity import compute_fidelity, is_sourced, resolve_threshold

STANDARDS = REPO_ROOT / "standards"
TEAM = "team constraint, test"


def _th(source, **kw):
    return {"source": source, **kw}


def test_team_constraint_needs_owner_and_date():
    assert not is_sourced(_th(TEAM))
    assert not is_sourced(_th(TEAM, owner="Tristan"))
    assert not is_sourced(_th(TEAM, date="2026-11-25"))
    assert not is_sourced(_th(TEAM, owner="TBD", date="2026-11-25"))
    assert not is_sourced(_th(TEAM, owner="", date="2026-11-25"))
    assert not is_sourced(_th(TEAM, owner="Tristan", date="soon"))
    assert is_sourced(_th(TEAM, owner="Tristan", date="2026-11-25"))
    assert is_sourced(_th(TEAM, owner="Dillon", date=datetime.date(2026, 11, 25)))
    assert is_sourced(_th("Team Constraint, x", owner="Dillon", date="2026-11-25"))


def test_non_team_sources_keep_the_old_rule():
    assert not is_sourced(_th("pending"))
    assert not is_sourced(_th("internal convention"))
    assert not is_sourced(_th(" Pending "))
    assert not is_sourced(None)
    assert is_sourced(_th("14 CFR 107.3"))


def test_resolve_threshold_returns_owner_and_date_as_json_safe_values():
    th = resolve_threshold("program.yaml#budget_usd")
    assert th["owner"] == "Tristan" and th["date"] == "2026-11-25"
    json.dumps(th)
    assert resolve_threshold("design-standards.yaml#static_margin")["owner"] is None
    m = resolve_threshold("manufacturing.yaml#jacobs-fdm")
    assert m["owner"] == "Tristan" and m["date"] == "2026-11-25"


def test_fidelity_counts_a_team_constraint_only_with_owner_and_date(tmp_path, monkeypatch):
    (tmp_path / "t.yaml").write_text(
        "good:\n  value: 1\n  rule: r\n  source: team constraint, x\n  owner: Tristan\n  date: '2026-11-25'\n"
        "bare:\n  value: 1\n  rule: r\n  source: team constraint, x\n", encoding="utf-8")
    monkeypatch.setattr(fid, "STANDARDS_DIR", tmp_path)
    rows = [CheckResult("T4.method", PASS, "a", "t.yaml#good"), CheckResult("T4.method", PASS, "b", "t.yaml#bare")]
    out = compute_fidelity(SimpleNamespace(components=[]), [TierReport(4, "manufacturing", rows)])
    assert out["blocking"] == 2 and out["sourced_blocking"] == 1


def _walk(node, where, out):
    if isinstance(node, dict):
        if isinstance(node.get("source"), str):
            out.append((where, node))
        for k, v in node.items():
            _walk(v, f"{where}#{k}", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, f"{where}[{(v.get('id') if isinstance(v, dict) else i)}]", out)


def _team_entries():
    out = []
    for p in sorted(STANDARDS.glob("*.yaml")):
        _walk(yaml.safe_load(p.read_text(encoding="utf-8")), p.name, out)
    return [(w, e) for w, e in out if e["source"].strip().lower().startswith("team constraint")]


def test_every_team_constraint_in_standards_has_owner_and_date():
    entries = _team_entries()
    assert entries
    for where, e in entries:
        assert is_sourced({"source": e["source"], "owner": e.get("owner"), "date": e.get("date")}), where
        assert e["owner"] in ("Tristan", "Dillon"), where


def test_the_default_owner_list_is_exact():   # defaults: Tristan, 2026-11-25; the conductor confirms them with Tristan
    expected = {
        "program.yaml#constraints#budget_usd", "program.yaml#constraints#deadline", "program.yaml#constraints#mass_cap_kg",
        "program.yaml#constraints#transport_pieces_max", "program.yaml#constraints#transport_box_mm",
        "program.yaml#constraints#physics_pass", "program.yaml#constraints#cad_real_parts",
        "program.yaml#constraints#exposed_wiring_minimised",
        "operations.yaml#hover_ctrl_factor", "operations.yaml#transition_thrust_fraction_max",
        "operations.yaml#mission_hover_min", "operations.yaml#mission_cruise_min", "operations.yaml#energy_reserve_fraction",
        "fixed-wing.yaml#cruise_to_stall_ratio_min", "gate-thresholds.yaml#transport_box_mm",
        "manufacturing.yaml#machine_optional_methods", "manufacturing.yaml#machines[jacobs-fdm]",
        "manufacturing.yaml#machines[jacobs-fdm-lulzbot]", "manufacturing.yaml#machines[jacobs-fdm-fortus]",
    }
    got = {w for w, _ in _team_entries()}
    assert got == expected, (sorted(got - expected), sorted(expected - got))
    for _, e in _team_entries():
        assert e["owner"] == "Tristan" and str(e["date"]) == "2026-11-25"
