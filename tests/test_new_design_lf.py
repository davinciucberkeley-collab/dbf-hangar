import shutil
from pathlib import Path

import pytest

import hangar.cli as cli


@pytest.fixture
def tmp_designs(tmp_path, monkeypatch):
    d = tmp_path / "designs"
    shutil.copytree(Path(__file__).parent / "fixtures" / "derived-planform", d / "tpl")
    monkeypatch.setattr(cli, "DESIGNS_DIR", d)
    return d


def test_template_copy_is_lf(tmp_designs):
    p = cli.new_design("lf-copy", "tpl")
    b = p.read_bytes()
    assert b"\r" not in b
    assert b.count(b"\n") > 10


def test_blank_is_lf(tmp_designs):
    p = cli.new_blank_design("lf-blank")
    assert b"\r" not in p.read_bytes()


def test_template_copy_text_is_unchanged(tmp_designs):
    p = cli.new_design("lf-copy", "tpl")
    text = p.read_bytes().decode("utf-8")
    assert text.startswith("# Copied from designs/tpl by")
    assert "id: lf-copy" in text
