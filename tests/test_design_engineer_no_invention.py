"""U13.6: the design-engineer never invents ratings, requirements or thresholds to clear a check."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ROLE_REL = ".claude/agents/design-engineer.md"
ROLE = ROOT / ROLE_REL


def _lines() -> list[str]:
    return ROLE.read_text(encoding="utf-8").splitlines()


def _section(heading: str) -> list[str]:
    lines = _lines()
    assert lines.count(heading) == 1, heading
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start + 1:end]


def test_never_section_has_the_rules():
    never = _section("## Never")
    invent = [line for line in never if line.startswith("- Invent a number to clear a check")]
    assert invent, "missing 'Invent a number to clear a check' line"
    assert "rating_basis: placeholder" in invent[0]
    assert any(line.startswith("- Raise a rating, shrink a load or widen a requirement") for line in never)


def test_output_section_asks_for_unsourced_values():
    lines = _lines()
    start = lines.index("## Output")
    end = lines.index("## Never")
    assert start < end
    assert "Unsourced values" in "\n".join(lines[start:end])


def test_existing_never_lines_kept():
    never = _section("## Never")
    older = [
        next(line for line in never if line.startswith("- Edit `core/`")),
        next(line for line in never if line.startswith("- Relax a threshold")),
        next(line for line in never if line.startswith("- Merge your own PR")),
    ]
    positions = [never.index(line) for line in older]
    assert positions == sorted(positions)
    new_lines = [i for i, line in enumerate(never) if line.startswith(("- Invent a number", "- Raise a rating"))]
    assert new_lines, "new Never lines missing"
    assert min(new_lines) > never.index(older[1])
    assert max(new_lines) < never.index(older[2])


def test_front_matter_unchanged():
    git = shutil.which("git")
    if git is None:
        pytest.skip("git not installed")
    result = subprocess.run(
        [git, "show", f"HEAD:{ROLE_REL}"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        pytest.skip("HEAD has no design-engineer.md")
    head_front = result.stdout.splitlines()[:5]
    assert _lines()[:5] == head_front
