from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "team-guide.md"
HEADING = "### Control surfaces and servos"
GATE = "## 5. Task: gate work"


def _text() -> str:
    return GUIDE.read_text(encoding="utf-8")


def _section() -> str:
    text = _text()
    start = text.index(HEADING)
    rest = text[start + len(HEADING):]
    nxt = rest.find("\n## ")
    return text[start: start + len(HEADING) + (nxt if nxt >= 0 else len(rest))]


def test_section_present_and_before_gate_work():
    text = _text()
    assert HEADING in text
    assert text.index(HEADING) < text.index(GATE)


def test_section_names_the_doc_and_fixture():
    section = _section()
    for needle in (
        "docs/mechanisms.md",
        "tests/fixtures/mechanism-recipe/plane.yaml",
        "kinematic_link",
        "T6.ratio",
        "T6.servo_undriven",
    ):
        assert needle in section, needle


def test_pointed_files_exist():
    assert (ROOT / "docs" / "mechanisms.md").is_file()
    assert (ROOT / "tests" / "fixtures" / "mechanism-recipe" / "plane.yaml").is_file()
