"""U17.1 2b (D91 a): criteria that resolved to no threshold now resolve; the fidelity line counts them."""
from __future__ import annotations

from types import SimpleNamespace

import yaml

from hangar.design import PASS, FAIL, REPO_ROOT, CheckResult, TierReport
from hangar.gates.fidelity import compute_fidelity, resolve_threshold

MFG = REPO_ROOT / "standards" / "manufacturing.yaml"


def _caps() -> dict:
    return yaml.safe_load(MFG.read_text(encoding="utf-8"))


def test_every_machine_resolves_with_a_real_source():
    for m in _caps()["machines"]:
        th = resolve_threshold(f"manufacturing.yaml#{m['id']}")
        assert th is not None, m["id"]
        assert str(th["source"]).strip().lower() not in ("pending", "internal convention", ""), m["id"]


def test_machine_optional_methods_is_an_entry_with_a_source():
    th = resolve_threshold("manufacturing.yaml#machine_optional_methods")
    assert th is not None and "purchased" in th["value"] and str(th["source"]).strip().lower() != "pending"


def test_bare_manufacturing_file_stays_unresolved():   # T4.machine and T4.capabilities rows keep it
    assert resolve_threshold("manufacturing.yaml") is None


def test_definition_criteria_resolve_to_pending_keys():
    for crit, key in (("requirements.mtow_g", "mtow_declared_in_design"),
                      ("connection-types.yaml", "connection_named_in_library")):
        th = resolve_threshold(crit)
        assert th is not None and th["file"] == "gate-thresholds.yaml" and th["key"] == key, crit
        assert th["source"] == "pending", crit


def test_fidelity_counts_the_t4_rows_and_not_the_pending_definitions():
    rows = [CheckResult("T4.method", PASS, "a", "manufacturing.yaml#machine_optional_methods"),
            CheckResult("T4.method", PASS, "b", "manufacturing.yaml#jacobs-fdm"),
            CheckResult("T4.fits_machine", FAIL, "c", "manufacturing.yaml#jacobs-fdm-fortus"),
            CheckResult("T4.machine", FAIL, "d", "manufacturing.yaml"),
            CheckResult("T0.schema", PASS, "e", "schema/plane.schema.json")]
    fid = compute_fidelity(SimpleNamespace(components=[]), [TierReport(4, "manufacturing", rows[:4]), TierReport(0, "schema", rows[4:])])
    assert fid["blocking"] == 5 and fid["sourced_blocking"] == 3


def test_tier4_free_method_rows_cite_the_free_methods_key():
    from hangar.checks import tier4_manufacturing
    from hangar.design import load_design
    d = load_design(REPO_ROOT / "designs" / "example-tailsitter-wing")
    rows = tier4_manufacturing(d).results
    free = [r for r in rows if r.check_id == "T4.method" and r.criterion == "manufacturing.yaml#machine_optional_methods"]
    assert free, "example-tailsitter-wing has 7 free-method rows"
    assert not [r for r in rows if r.check_id == "T4.method" and r.criterion == "manufacturing.yaml"]


def test_schema_criterion_is_not_aliased_and_has_no_threshold():   # keeps T0.root's gate.explain threshold None
    from hangar.gates.fidelity import CRITERION_ALIASES
    assert "schema/plane.schema.json" not in CRITERION_ALIASES
    assert resolve_threshold("schema/plane.schema.json") is None
