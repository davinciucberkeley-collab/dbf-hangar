"""Knowledge import of DBF-Combined config-study (U2.2 step 3a): entries follow TEMPLATE-concept.md."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest
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
DBF = Path(os.environ.get("DBF_COMBINED", "C:/Users/trist/DBF-Combined"))   # local clone; absent in CI
COPY_RUN = 10          # words in a row shared with a cited file that count as copied (T68)


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


def shared_run(entry: str, cited: str, n: int = COPY_RUN):
    """First run of n or more consecutive words (lower-cased, punctuation ignored) that both texts contain, else None."""
    we, wc = re.findall(r"\w+", entry.lower()), re.findall(r"\w+", cited.lower())
    grams = {tuple(we[i:i + n]) for i in range(len(we) - n + 1)}
    for i in range(len(wc) - n + 1):
        if tuple(wc[i:i + n]) in grams:
            return " ".join(wc[i:i + n])
    return None


def test_shared_run_finds_ten_shared_words_and_ignores_nine():
    cited = "The quick brown fox jumps over the lazy dog, again and again."
    assert shared_run("intro: quick brown fox jumps over the lazy dog again and more", cited) == "quick brown fox jumps over the lazy dog again and"
    assert shared_run("quick brown fox jumps over the lazy dog again", cited) is None      # 9 words
    assert shared_run("Quick, BROWN fox -- jumps over the lazy dog; again and", cited) == "quick brown fox jumps over the lazy dog again and"
    assert shared_run("", cited) is None and shared_run(cited, "") is None


@pytest.mark.skipif(not (DBF / "redesign" / "config-study").is_dir(), reason="DBF-Combined clone not present")
def test_no_entry_copies_ten_words_from_a_file_it_cites():
    for p in _entries():
        fm, body = _split(p)
        for f in fm["source_files"]:
            src = DBF / f
            if src.is_file():
                run = shared_run(body, src.read_text(encoding="utf-8", errors="replace"))
                assert run is None, f"{p.name} copies from {f}: {run!r}"


# ---- T110 (U4.27): the 23 docs/research entries get the same structure and copy checks as the config-study entries ----
RESEARCH = REPO_ROOT / "knowledge" / "research"
RESEARCH_STEMS = ["aerodynamics", "airframe-materials", "avionics-autopilot", "benchmarks", "bom-savings", "budget-airframe",
                  "budget-avionics", "budget-energy-test", "budget-lift", "configurations", "electrical-architecture", "firmware",
                  "hardware-schedule", "hardware-spec", "lift-propulsion", "nautical-wings-props", "propulsion-margin-data",
                  "pusher-battery-servo", "review-formats", "stall-margin", "team-crosscheck", "thermal", "tolerance-analysis"]
RESEARCH_SOURCE_COMMIT = "a93f14da"      # DBF-Combined commit the entries were written from (docs/research/ is not checked out there)


def _research_entries():
    return sorted(RESEARCH.glob("*.md"))


def test_research_import_has_exactly_the_23_entries():
    assert [p.stem for p in _research_entries()] == sorted(f"docs-research-{s}" for s in RESEARCH_STEMS)


def test_every_research_entry_has_its_template_fields_and_sections():
    for p in _research_entries():
        fm, body = _split(p)
        stem = p.stem.removeprefix("docs-research-")
        assert list(fm) == KEYS, p.name
        assert fm["id"] == p.stem and fm["kind"] == "research", p.name
        assert fm["source_repo"] == "DBF-Combined @ a93f14d" and fm["verified"] is False, p.name
        assert fm["source_files"] == [f"docs/research/{stem}.md"], p.name
        assert isinstance(fm["title"], str) and fm["title"].strip() and not fm["title"].startswith("<"), p.name
        found = _sections(body)
        for s in SECTIONS:
            assert found.get(s) and not found[s].startswith("<"), f"{p.name}: section {s} empty or placeholder"
        assert "<svg" not in body and "```" not in body, f"{p.name}: copied block"


def test_every_research_morph_cell_exists_in_the_chart():
    cells = _cells()
    for p in _research_entries():
        fm, _ = _split(p)
        assert isinstance(fm["morph_cells"], list), p.name          # [] is allowed: purchasing, fit and review files fit no cell
        assert set(fm["morph_cells"]) <= cells, f"{p.name}: unknown cell in {fm['morph_cells']}"


def test_every_research_source_file_is_listed_in_provenance():
    prov = (REPO_ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
    for p in _research_entries():
        fm, _ = _split(p)
        assert f"| knowledge/research/{p.name} | DBF-Combined @ a93f14d : {fm['source_files'][0]} |" in prov, p.name


def _dbf_git(*args):
    return subprocess.run(["git", "-C", str(DBF), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


@pytest.mark.skipif(not (DBF / ".git").exists() or _dbf_git("cat-file", "-e", RESEARCH_SOURCE_COMMIT).returncode != 0,
                    reason="DBF-Combined clone with commit a93f14d not present")
def test_no_research_entry_copies_ten_words_from_its_source():
    for p in _research_entries():
        fm, body = _split(p)
        for f in fm["source_files"]:
            r = _dbf_git("show", f"{RESEARCH_SOURCE_COMMIT}:{f}")
            assert r.returncode == 0, f"{p.name}: git show {f} failed: {r.stderr}"
            run = shared_run(body, r.stdout)
            assert run is None, f"{p.name} copies from {f}: {run!r}"
