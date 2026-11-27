"""U19.2 brief 1: the plain-text registry and renderer (hangar.gates.describe). Nothing here changes scorecard output."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from hangar.design import REPO_ROOT, CheckResult, Design, Scorecard, TierReport
from hangar.gates import describe
from hangar.gates.describe import describe_card, describe_row, family_of, fold, load_registry, part_label, standard_limit

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "describe_examples.json").read_text(encoding="utf-8"))
CASES = FIXTURE["cases"]


def _design() -> Design:
    return Design(data=FIXTURE["design"])


def _row(case: dict) -> CheckResult:
    r = case["row"]
    return CheckResult(r["check_id"], r["status"], r["message"], r["criterion"], r["data"])


def _case(name: str) -> dict:
    return next(c for c in CASES if c["name"] == name)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_golden_examples(case):
    t = describe_row(_row(case), _design())
    exp = case["expect"]
    assert t.title == exp["title"]
    assert [p.label for p in t.parts] == exp["labels"]
    assert t.sentence != "" and t.sentence != t.details, f"fell back to the raw message: {t.sentence}"
    for s in exp["contains"]:
        assert s in t.sentence, f"{s!r} not in {t.sentence!r}"
    assert exp["hint_contains"] in t.hint
    assert not t.details.startswith("report-only")
    if "report_only" in exp:
        assert t.report_only is exp["report_only"]
    if "would_be" in exp:
        assert t.would_be == exp["would_be"]


def _emitted_families() -> set[str]:
    fams: set[str] = set()
    files = [REPO_ROOT / "core" / "hangar" / "checks.py", *sorted((REPO_ROOT / "core" / "hangar" / "gates").glob("*.py"))]
    for f in files:
        src = f.read_text(encoding="utf-8")
        for m in re.finditer(r'CheckResult\(\s*f?"(T\d\.[a-z_0-9]+)', src):
            fams.add(m.group(1))
        for m in re.finditer(r'f"(T\d\.[a-z_]+)', src):
            fams.add(m.group(1))
    gates = yaml.safe_load((REPO_ROOT / "standards" / "gates.yaml").read_text(encoding="utf-8"))
    for row in gates.get("discipline_checks", []):
        fams.add(row["id"])
    return fams


def test_every_emitted_family_has_an_entry():
    reg = load_registry()
    missing = sorted(f for f in _emitted_families() if f not in reg)
    assert not missing, f"families without a describe.yaml entry: {missing}"


def test_registry_entries_are_valid():
    reg = load_registry()
    assert reg
    for fam, e in reg.items():
        assert e.get("title"), fam
        assert e.get("group") in {"part", "problem", "design"}, fam
        assert set(e.get("what", {})) <= {"FAIL", "WARN", "SKIP", "PASS"}, fam
        if "extract" in e:
            re.compile(e["extract"])
        if e.get("fold"):
            assert e.get("fold_what"), fam


def test_standard_limit_lookup():
    m = standard_limit("design-standards.yaml#static_margin")
    assert m["min"] == 0.05 and m["max"] == 0.15
    assert standard_limit("stability.yaml#tail_volume_h_min")["value"] == 0.30
    assert standard_limit("load-cases.yaml#joint_rf_min")["value"] == 1.0
    assert standard_limit("nope.yaml#x") == {}


def test_part_label_rules():
    d = Design(data={"components": [
        {"id": "a", "name": "Named part", "description": "Something else (x)"},
        {"id": "b", "description": "Alpha (beta)"},
        {"id": "c", "description": "Alpha, beta"},
        {"id": "d", "description": "Alpha; beta"},
        {"id": "e", "description": "Alpha - beta"},
        {"id": "f", "description": "one two three four five six seven eight nine ten eleven twelve"},
        {"id": "tail-elevator-rod"},
    ]})
    assert part_label(d, "a") == "Named part"
    assert part_label(d, "b") == "Alpha"
    assert part_label(d, "c") == "Alpha"
    assert part_label(d, "d") == "Alpha"
    assert part_label(d, "e") == "Alpha"
    f = part_label(d, "f")
    assert len(f) <= 40 and f and "one two three four five six seven eight nine ten eleven twelve".startswith(f)
    assert f.split(" ")[-1] in {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"}
    assert part_label(d, "tail-elevator-rod") == "tail elevator rod"
    assert part_label(d, "zzz") == "zzz"


def test_design_none_and_missing_data_fall_back():
    case = _case("fea")
    row = CheckResult("T2.fea_strength", "FAIL", case["row"]["message"], case["row"]["criterion"], {})
    t = describe_row(row, None)
    assert t.sentence == t.details
    assert t.title == "Printed part is too weak"
    z = describe_row(CheckResult("T9.zzz", "WARN", "msg"), None)
    assert z.title == "Zzz"
    assert z.sentence == "msg"


def test_report_only_prefix_stripped_and_status_kept():
    t = describe_row(_row(_case("wiring")), _design())
    assert t.status == "WARN" and t.report_only is True
    assert not t.details.startswith("report-only")


def test_fold():
    base = _case("load")["row"]

    def rows(n):
        return [describe_row(CheckResult(base["check_id"], "SKIP", f"{c}: carries 2.1 N", base["criterion"],
                                         {"joint": c, "load_n": 2.1}), None) for c in "abcde"[:n]]
    e = fold(rows(5))
    assert len(e) == 1 and e[0]["count"] == 5
    assert e[0]["title"] == "Joint strength not checked: 5 joints"
    assert "Each of these 5 joints" in e[0]["sentence"]
    assert len(fold(rows(2))) == 2
    other = [describe_row(CheckResult("T3.static_margin", "FAIL", "x"), None) for _ in range(4)]
    assert len(fold(other)) == 4


def test_describe_card_keeps_shape():
    def r(i):
        return CheckResult(f"T9.zzz.{i}", "PASS", "ok")
    card = Scorecard("x", [TierReport(0, "a", [r(1), r(2), r(3)]), TierReport(1, "b", [r(4), r(5)])])
    out = describe_card(card, None)
    assert [len(t) for t in out] == [3, 2]
    assert [x.check_id for t in out for x in t] == [f"T9.zzz.{i}" for i in range(1, 6)]


def test_source_cut_never_leaves_open_paren():
    t = describe_row(_row(_case("fea")), _design())
    assert t.source.count("(") == t.source.count(")")
    assert describe._cut_words("aaaa bbbb (cccc dddd) eeee", 14).count("(") == 0


def test_stored_tie_rounds_up_like_the_raw_message():
    row = CheckResult("T2.joint_load", "SKIP", "fuselage-wing: carries 1.0 N; rating is a placeholder, not checked",
                      "design-standards.yaml#landing_load_factor", {"load_n": 0.95, "joint": "fuselage-wing"})
    assert "carries 1.0 N" in describe_row(row, _design()).sentence


def test_title_mapping_picks_the_row_status_and_string_form_still_works(monkeypatch):
    # string form: one title for every status (T7.wiring); mapping form: per-status titles (T2.fea_strength)
    fea = {"title": {"FAIL": "Printed part is too weak", "SKIP": "Printed part strength not checked",
                     "PASS": "Printed part is strong enough"}, "group": "part"}
    wiring = {"title": "Wire runs outside the airframe", "group": "part"}
    reg = dict(load_registry(), **{"T2.fea_strength": fea, "T7.wiring": wiring})
    monkeypatch.setattr(describe, "_REGISTRY", reg)
    assert describe_row(CheckResult("T2.fea_strength", "SKIP", "x"), None).title == "Printed part strength not checked"
    assert describe_row(CheckResult("T2.fea_strength", "PASS", "x"), None).title == "Printed part is strong enough"
    assert describe_row(CheckResult("T2.fea_strength", "FAIL", "x"), None).title == "Printed part is too weak"
    # a status the mapping does not name keeps the FAIL title
    assert describe_row(CheckResult("T2.fea_strength", "WARN", "x"), None).title == "Printed part is too weak"
    for status in ("FAIL", "WARN", "SKIP", "PASS"):
        assert describe_row(CheckResult("T7.wiring.h", status, "x"), None).title == "Wire runs outside the airframe"
