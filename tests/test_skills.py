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
