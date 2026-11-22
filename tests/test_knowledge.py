"""Knowledge import of DBF-Combined config-study (U2.2 step 3a): entries follow TEMPLATE-concept.md."""
from __future__ import annotations

import re

import yaml

from hangar.design import REPO_ROOT

CONCEPTS = REPO_ROOT / "knowledge" / "concepts"
EXEMPT = {"tailsitter-evidence"}          # older entry, own frontmatter; not part of this import
KEYS = ["id", "title", "kind", "morph_cells", "source_repo", "source_files", "created", "verified"]
SECTIONS = ["Summary", "Key facts", "Status in the study", "Open questions"]
CONCEPT_IDS = ([f"k{n:02d}" for n in range(1, 26)] + [f"b{n:02d}" for n in range(1, 10)]
               + [f"u{n:02d}" for n in range(1, 10)])
RESEARCH_IDS = ["research-components-cost", "research-existing-vtol", "research-flight-control", "research-student-builds"]
JUDGING_IDS = ["judging-build-and-transport", "judging-flight-risk", "judging-mission-and-learning"]
SOURCE_ROOT = "redesign/config-study/"


def _entries():
    return sorted(p for p in CONCEPTS.glob("*.md") if p.stem not in EXEMPT)


def _split(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    assert m, f"{path.name}: no frontmatter"
    return yaml.safe_load(m.group(1)), m.group(2)


def _sections(body):
    found, cur = {}, None
    for line in body.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            found[cur] = []
        elif cur:
            found[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in found.items()}


def _cells():
    chart = yaml.safe_load((REPO_ROOT / "knowledge" / "morphological-chart.yaml").read_text(encoding="utf-8"))
    return {f"{d['id']}:{o['id']}" for d in chart["dimensions"] for o in d["options"]}


def test_concept_template_has_the_fields_and_sections():
    text = (REPO_ROOT / "knowledge" / "TEMPLATE-concept.md").read_text(encoding="utf-8")
    fm = yaml.safe_load(re.match(r"---\n(.*?)\n---\n", text, re.S).group(1))
    assert list(fm) == KEYS
    for s in SECTIONS:
        assert f"## {s}" in text


def test_import_has_exactly_the_expected_entries():
    assert [p.stem for p in _entries()] == sorted(CONCEPT_IDS + RESEARCH_IDS + JUDGING_IDS)   # 43 + 4 + 3 = 50


def test_every_entry_has_its_template_fields_and_sections():
    for p in _entries():
        fm, body = _split(p)
        assert list(fm) == KEYS, p.name
        assert fm["id"] == p.stem, p.name
        assert fm["kind"] == ("concept" if p.stem in CONCEPT_IDS else "research" if p.stem in RESEARCH_IDS else "judging"), p.name
        assert fm["source_repo"] == "DBF-Combined @ a93f14d", p.name
        assert fm["verified"] is False, p.name
        assert isinstance(fm["title"], str) and fm["title"].strip() and not fm["title"].startswith("<"), p.name
        found = _sections(body)
        for s in SECTIONS:
            assert found.get(s) and not found[s].startswith("<"), f"{p.name}: section {s} empty or placeholder"
        assert "<svg" not in body and "```" not in body, f"{p.name}: copied block"


def test_every_morph_cell_exists_in_the_chart():
    cells = _cells()
    for p in _entries():
        fm, _ = _split(p)
        assert isinstance(fm["morph_cells"], list) and fm["morph_cells"], f"{p.name}: no morph cell"
        assert set(fm["morph_cells"]) <= cells, f"{p.name}: unknown cell in {fm['morph_cells']}"
        if fm["kind"] == "concept":
            assert any(c.startswith("vtol_method:") for c in fm["morph_cells"]), f"{p.name}: no vtol_method cell"


def test_every_source_file_is_listed_in_provenance():
    prov = (REPO_ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
    for p in _entries():
        fm, _ = _split(p)
        assert isinstance(fm["source_files"], list) and fm["source_files"], p.name
        for f in fm["source_files"]:
            assert f.startswith(SOURCE_ROOT), f"{p.name}: {f}"
            assert f in prov, f"{p.name}: {f} not in PROVENANCE.md"
            assert "DBF-Combined @ a93f14d" in prov
    assert "redesign/config-study/tiebreak/" in prov and "not imported" in prov


def test_concepts_with_a_card_cite_it():
    for cid in ("k01", "k06", "k09", "k19", "b08", "b09", "u01"):
        fm, _ = _split(CONCEPTS / f"{cid}.md")
        assert f"{SOURCE_ROOT}cards/{cid.upper()}/CARD.md" in fm["source_files"], cid
        assert any(f.endswith("judging/flight-risk.md") for f in fm["source_files"]), cid
