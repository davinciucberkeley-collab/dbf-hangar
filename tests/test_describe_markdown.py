"""U19.2 brief 2: the markdown scorecard renders from the describe registry; the old table stays as the appendix."""
from __future__ import annotations

import json
from pathlib import Path

from hangar.checks import validate
from hangar.design import CheckResult, Design, Scorecard, TierReport, load_design
from hangar.ops import call

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "describe_examples.json").read_text(encoding="utf-8"))
FOUR_BAR = Path(__file__).parent / "fixtures" / "four-bar"
# the 8 before/after examples of spec section 4 (the fixture also has three extra static/joint variants)
EXAMPLE_NAMES = ["fea", "static", "drop", "wiring", "tail", "rf", "kin", "load"]


def _card(max_tier: int = 9, clean: bool = False) -> tuple[Design, Scorecard]:
    design = Design(data=dict(FIXTURE["design"]))
    design.data["id"] = "stub"
    by_tier: dict[int, list[CheckResult]] = {}
    cases = {c["name"]: c for c in FIXTURE["cases"]}
    rows = []
    for name in EXAMPLE_NAMES:
        r = cases[name]["row"]
        rows.append(CheckResult(r["check_id"], r["status"], r["message"], r["criterion"], r["data"]))
    rows.append(CheckResult("T3.mass", "PASS", "1273 g vs MTOW 1470 g"))
    rows.append(CheckResult("T3.hover_tw", "SKIP", "not applicable: x", "", {"not_applicable": True}))
    for row in rows:
        by_tier.setdefault(int(row.check_id[1]), []).append(row)
    tiers = [TierReport(t, f"tier {t}", res) for t, res in sorted(by_tier.items())]
    return design, Scorecard("stub", tiers, max_tier=max_tier)


def _lines_after_full_table(md: str) -> list[str]:
    lines = md.splitlines()
    i = lines.index("## Full table")
    out = []
    for line in lines[i + 2:]:
        if line == "":
            break
        out.append(line)
    return out


def test_sections_and_counts():
    design, card = _card()
    md = card.to_markdown(design)
    assert "**Summary:** 3 FAIL, 3 WARN, 2 not checked, 1 not applicable, 1 PASS." in md
    heads = ["## Needs fixing", "## Warnings", "## Not checked", "## Not applicable (1)", "## Passing (1 checks)", "## Full table"]
    pos = [md.index(h) for h in heads]
    assert pos == sorted(pos)


def test_example_lines():
    design, card = _card()
    md = card.to_markdown(design)
    assert "- **FAIL** **Printed part is too weak**: Hub (cge-001)" in md
    assert ("  Fix: Make the part thicker where the load enters it, or change material, then run `plane fea stub --all`."
            in md)
    assert ("- **WARN** **Wire runs outside the airframe**: Pack Tattu 2300 mAh 4S 75C (pwr-001), "
            "XT60 female + 14 AWG tail to the ESC (hrn-002) _[report-only until 2026-12-08, would be FAIL today]_" in md)
    assert "  Check: `T2.fea_strength`" in md


def test_full_table_is_the_old_table():
    design, card = _card()
    expected = ["| Tier | Status | Check | Result | Criterion |", "|---|---|---|---|---|"]
    for t in card.tiers:
        for r in t.results:
            expected.append(f"| {t.tier} {t.name} | {r.status} | {r.check_id} | {r.status}: {r.message} | {r.criterion} |")
    assert _lines_after_full_table(card.to_markdown(design)) == expected


def test_design_none():
    _, card = _card()
    md = card.to_markdown()
    assert "## Full table" in md


def test_partial_and_accepted_wording_kept():
    _, partial = _card(max_tier=1)
    md = partial.to_markdown()
    assert "**Partial run (tiers 0–1):**" in md
    assert "Accepted" not in md
    clean = Scorecard("stub", [TierReport(3, "tier 3", [CheckResult("T3.mass", "PASS", "ok")])])
    assert "**Accepted:** yes" in clean.to_markdown()


def test_ops_markdown_key_uses_registry():
    r = call("design.validate", path=str(FOUR_BAR), tier="1")
    assert "## Full table" in r.data["markdown"]
    expected = validate(load_design(FOUR_BAR), max_tier=1).to_dict()["tiers"]
    assert r.data["tiers"] == expected
