"""Skill shape tests. Every test is parametrized over all skills/*/SKILL.md, so later units add skills without editing tests."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from hangar import ops

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
REQUIRED = ["design-concept", "review-design", "research", "make-skill", "design-iterate",
            "recon", "plan-scheme", "get-it-together", "weekly-update"]
# A required skill that is missing is a test failure (its file is read below), not a silent skip.
SKILLS = sorted(set(SKILLS_DIR.glob("*/SKILL.md")) | {SKILLS_DIR / n / "SKILL.md" for n in REQUIRED})
SECTIONS = ["Goal", "Agents", "Steps", "Pass check", "Stop rules"]
MAX_LINES = 120
HAND_WRITTEN = {"progress", "baseline check", "baseline update"}  # CLI commands that are not registry ops
NUMBER_ALLOWED = {"get-it-together": {"15"}, "make-skill": {"120"}}  # per skill folder name

FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`([^`\n]+)`")
CMD = re.compile(r"(?<![\w./-])plane ([a-z][a-z-]*)(?: ([a-z][a-z-]*))?")
LIST_PREFIX = re.compile(r"^\s*\d+[a-z]?[.)]\s+", re.M)
NUM = re.compile(r"(?<![\w.#§/-])\d+(?:\.\d+)?%?(?![\w/-]|\.\d)")


def _id(path: Path) -> str:
    return path.parent.name


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _commands(text: str) -> list[tuple[str, str | None]]:
    code = "\n".join(FENCE.findall(text) + INLINE.findall(FENCE.sub("", text)))
    return [(m.group(1), m.group(2)) for m in CMD.finditer(code)]


def _is_known(group: str, verb: str | None) -> bool:
    if verb is None:
        return group in HAND_WRITTEN
    return f"{group}.{verb}" in ops.registry() or f"{group} {verb}" in HAND_WRITTEN


@pytest.mark.parametrize("path", SKILLS, ids=_id)
def test_every_skill_has_six_sections(path):
    text = _read(path)
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path}: no frontmatter"
    fm = dict(re.findall(r"^([a-z]+): *(.+)$", m.group(1), re.M))
    assert fm.get("name") == path.parent.name, f"{path}: name must equal the folder name"
    assert fm.get("description", "").startswith("Use when"), f"{path}: description must start with 'Use when'"
    body = FENCE.sub("", text[m.end():])
    assert re.findall(r"^## (.+?)\s*$", body, re.M) == SECTIONS, f"{path}: the ## headings must be exactly {SECTIONS}"


@pytest.mark.parametrize("path", SKILLS, ids=_id)
def test_skill_commands_exist(path):
    assert _commands("`plane design set x`, `plane progress --write`") == [("design", "set"), ("progress", None)]
    bad = [f"plane {g} {v or ''}".strip() for g, v in _commands(_read(path)) if not _is_known(g, v)]
    assert not bad, f"{path}: commands not in the ops registry or the hand-written list: {bad}"


@pytest.mark.parametrize("path", SKILLS, ids=_id)
def test_no_numbers_in_skills(path):
    allowed = NUMBER_ALLOWED.get(path.parent.name, set())
    found = [(i, n) for i, line in enumerate(LIST_PREFIX.sub("", _read(path)).splitlines(), 1)
             for n in NUM.findall(line) if n not in allowed]
    assert not found, f"{path}: numbers in skill text (link standards/<file>.yaml#<key> instead): {found}"


@pytest.mark.parametrize("path", SKILLS, ids=_id)
def test_skill_under_120_lines(path):
    n = len(_read(path).splitlines())
    assert n <= MAX_LINES, f"{path}: {n} lines, limit {MAX_LINES}"


DISCIPLINE_SKILLS = [
    "review-structures", "review-aero", "review-controls",
    "review-propulsion", "review-manufacturing", "review-test-safety",
]
_D_REPO = Path(__file__).resolve().parents[1]
_D_EXTRACT = _D_REPO / "plans" / "2026-11-20-standardization" / "discipline-extract"
_D_ITEM = re.compile(r"^- \*\*([A-Za-z0-9-]+)\*\*: .+ \(discipline-extract/([A-J][0-9]+)\.md#([0-9]+)\)$")
_D_LANDS = re.compile(r"^SKILL:([a-z-]+)/([A-Za-z0-9-]+)")


def _d_expected_rows():
    """{skill: {(role_id, row_number): slug}} from the `lands as` cell of every extract row."""
    out = {name: {} for name in DISCIPLINE_SKILLS}
    for f in sorted(_D_EXTRACT.glob("[A-J][0-9].md")):
        for line in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\| ([0-9]+) \|", line)
            if not m:
                continue
            last = line.split("|")[-2].strip()
            lm = _D_LANDS.match(last)
            if lm and lm.group(1) in out:
                out[lm.group(1)][(f.stem, int(m.group(1)))] = lm.group(2)
    return out


def test_discipline_skills_size_and_sections():
    for name in DISCIPLINE_SKILLS:
        path = _D_REPO / "skills" / name / "SKILL.md"
        assert path.is_file(), name
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 120, (name, len(lines))
        heads = [ln[3:].strip() for ln in lines if ln.startswith("## ")]
        missing = [s for s in SECTIONS if s not in heads]
        assert not missing, (name, missing)


def test_discipline_skill_items_cite_extract_rows():
    expected = _d_expected_rows()
    assert sum(len(v) for v in expected.values()) == 97
    for name in DISCIPLINE_SKILLS:
        text = (_D_REPO / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        cited = []
        for ln in text.splitlines():
            if not ln.startswith("- **"):
                continue
            m = _D_ITEM.match(ln)
            assert m, (name, ln)
            key = (m.group(2), int(m.group(3)))
            assert key in expected[name], (name, key, "row is not tagged SKILL:" + name)
            assert expected[name][key] == m.group(1), (name, key, "slug mismatch")
            cited.append(key)
        assert len(cited) == len(set(cited)), (name, "a row is cited twice")
        assert set(cited) == set(expected[name]), (name, sorted(set(expected[name]) - set(cited)))
