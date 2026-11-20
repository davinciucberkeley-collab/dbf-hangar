import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

def test_package_is_hangar_and_cli_still_plane():
    import hangar
    assert hangar.__version__.startswith("1.0.0.dev")
    assert shutil.which("plane")

def test_no_aircraft_platform_package_left():
    assert not (REPO / "core" / "aircraft_platform").exists()
    assert (REPO / "core" / "hangar" / "cli.py").exists()

def test_provenance_lists_every_imported_top_level_path():
    prov = (REPO / "PROVENANCE.md").read_text(encoding="utf-8")
    for p in ["core/", "schema/", "standards/", "tests/", "designs/", "knowledge/", "skills/", "viewer/", "docs/", ".github/"]:
        assert p in prov
    assert "f462468" in prov

def test_meshes_are_lfs_tracked():
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    assert "*.stl filter=lfs" in attrs and "*.sh text eol=lf" in attrs
