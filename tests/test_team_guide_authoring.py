from pathlib import Path
import re

from hangar.ops import registry

GUIDE = Path(__file__).resolve().parent.parent / "docs" / "team-guide.md"


def _text() -> str:
    return GUIDE.read_text(encoding="utf-8")


def _starting_section() -> str:
    lines = _text().splitlines()
    start = next(i for i, line in enumerate(lines) if line == "### Starting a new concept")
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def test_stale_sentence_is_gone():
    assert "Claude cannot yet generate a concept from a blank page" not in _text()


def test_new_text_present():
    text = _text()
    for needle in [
        "plane design new <new-id> --blank",
        "plane generators show <name>",
        "plane design add <path> components",
        "naca2412",
        "inboard_span",
    ]:
        assert needle in text, needle


def test_every_plane_command_in_the_section_exists():
    ops = registry()
    misses = []
    for g, v in re.findall(r"plane (\w+) ([a-z-]+)", _starting_section()):
        if f"{g}.{v}" not in ops:
            misses.append(f"{g}.{v}")
    assert misses == []
