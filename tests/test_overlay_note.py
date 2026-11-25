"""U13.7 (T148 C1): the CAD overlay note prints only when the configured folder holds a manifest."""
import inspect

import hangar.cli
from hangar.geom import overlay

NOTE = "note: CAD overlay ignored here"


def _manifest(root, part):
    (root / part).mkdir(parents=True)
    (root / part / "overlay.yaml").write_text("file: model.stl\n", encoding="utf-8")


def test_no_manifest_no_note(tmp_path, monkeypatch):
    root = tmp_path / "parts-cad"
    root.mkdir()
    monkeypatch.setenv(overlay.CONFIG_ENV, str(root))
    assert overlay.manifest_count() == 0
    assert overlay.ignored_note() is None
    assert overlay.overlay_configured() is True

    (root / "x").mkdir()
    assert overlay.manifest_count() == 0
    assert overlay.ignored_note() is None

    monkeypatch.setenv(overlay.CONFIG_ENV, "off")
    assert overlay.manifest_count() == 0
    assert overlay.ignored_note() is None


def test_note_when_a_manifest_exists(tmp_path, monkeypatch):
    root = tmp_path / "parts-cad"
    _manifest(root, "test-servo")
    monkeypatch.setenv(overlay.CONFIG_ENV, str(root))
    assert overlay.manifest_count() == 1
    assert overlay.ignored_note().startswith(NOTE)

    _manifest(root, "test-motor")
    assert overlay.manifest_count() == 2


def test_cli_uses_the_helper():
    # the baseline commands are click.Command objects; their Python body is the callback
    for cmd in (hangar.cli.baseline_update_cmd, hangar.cli.baseline_check_cmd):
        src = inspect.getsource(cmd.callback)
        assert "ignored_note()" in src
        assert "overlay_configured" not in src


def test_forced_off_still_works(tmp_path, monkeypatch):
    root = tmp_path / "parts-cad"
    _manifest(root, "test-servo")
    monkeypatch.setenv(overlay.CONFIG_ENV, str(root))
    with overlay.forced_off():
        assert overlay.manifest_count() == 1
        assert overlay.overlay_configured() is True
