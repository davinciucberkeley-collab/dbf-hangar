from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "team-guide.md"
CLI = ROOT / "core" / "hangar" / "cli.py"


def _guide() -> str:
    return GUIDE.read_text(encoding="utf-8")


def test_studio_howto_present():
    text = _guide()
    for needle in [
        "plane studio",
        "http://127.0.0.1:8765",
        ".studio/",
        "plane build-index --out viewer/data",
        "No `build-index` is needed for Studio",
    ]:
        assert needle in text, needle


def test_old_one_liner_gone():
    assert (
        "does the same edits point and click, on the same files. It opens an app and a browser."
        not in _guide()
    )


def test_port_matches_the_code():
    guide_port = re.search(r"127\.0\.0\.1:(\d+)", _guide()).group(1)
    code_port = re.search(r'@click.option\("--port", default=(\d+)', CLI.read_text(encoding="utf-8")).group(1)
    assert guide_port == code_port
