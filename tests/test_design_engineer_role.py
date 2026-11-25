"""U13.4: the design-engineer role points at the mechanism recipe and the add/apply/new ops."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / ".claude" / "agents" / "design-engineer.md"


def _text() -> str:
    return ROLE.read_text(encoding="utf-8")


def _loop_section() -> list[str]:
    lines = _text().splitlines()
    start = lines.index("## Loop (one change per iteration)")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    return lines[start + 1:end]


def test_pointers_present():
    text = _text()
    for needle in [
        "docs/mechanisms.md",
        "plane design add designs/<id> components|attachments|mechanisms",
        "plane design apply designs/<id>",
        "plane design new <id> --blank",
        "T6.servo_undriven",
    ]:
        assert needle in text, needle


def test_loop_items_are_numbered_1_to_8():
    numbers = [int(re.match(r"^(\d+)\. ", line).group(1))
               for line in _loop_section() if re.match(r"^\d+\. ", line)]
    assert numbers == [1, 2, 3, 4, 5, 6, 7, 8]


def test_ops_exist():
    from hangar.ops import registry

    names = set(registry())
    assert "design.add" in names
    assert "design.apply" in names


def test_front_matter_unchanged():
    git = shutil.which("git")
    if git is None:
        import pytest
        pytest.skip("git not on PATH")
    head = subprocess.run(
        [git, "show", "HEAD:.claude/agents/design-engineer.md"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert _text().splitlines()[:5] == head.splitlines()[:5]
