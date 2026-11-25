"""U13.6 (3b): design.render writes headless PNG views."""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

from hangar import design as design_mod  # noqa: E402
from hangar.ops import call, registry  # noqa: E402
from hangar.ops._png import decode  # noqa: E402

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
SIG = b"\x89PNG\r\n\x1a\n"


def _render(out, **kw):
    r = call("design.render", path=str(EXAMPLE_DIR), out=out, **kw)
    assert r.ok, r.errors
    return r


def test_iso_png_has_signature_and_size(tmp_path):
    out = tmp_path / "a.png"
    _render(out)
    assert out.read_bytes().startswith(SIG)
    w, h, _ = decode(out)
    assert (w, h) == (900, 900)


def test_model_is_drawn(tmp_path):
    out = tmp_path / "a.png"
    _render(out)
    _, _, rows = decode(out)
    px = [v for row in rows for v in row]
    frac = sum(1 for v in px if v < 250) / len(px)
    assert 0.02 < frac < 0.60


def test_top_view_aspect_matches_the_bounds(tmp_path):
    out = tmp_path / "t.png"
    _render(out, view="top", size=900)
    sx, sy, _ = call("design.bounds", path=str(EXAMPLE_DIR)).data["overall"]["size"]
    w, h, rows = decode(out)
    rows = rows[: int(h * 0.94)]
    xs = [x for row in rows for x, v in enumerate(row) if v < 250]
    ys = [y for y, row in enumerate(rows) if any(v < 250 for v in row)]
    ratio = (max(xs) - min(xs) + 1) / (max(ys) - min(ys) + 1)
    assert ratio == pytest.approx(sy / sx, rel=0.1)


def test_views_differ_and_all_writes_four(tmp_path):
    _render(tmp_path / "t.png", view="top")
    _render(tmp_path / "s.png", view="side")
    assert (tmp_path / "t.png").read_bytes() != (tmp_path / "s.png").read_bytes()
    r = _render(tmp_path / "m.png", view="all")
    for v in ("top", "side", "front", "iso"):
        assert (tmp_path / f"m-{v}.png").exists()
    assert len(r.data["files"]) == 4


def test_deterministic(tmp_path):
    _render(tmp_path / "a.png", view="side")
    _render(tmp_path / "b.png", view="side")
    assert (tmp_path / "a.png").read_bytes() == (tmp_path / "b.png").read_bytes()


def test_bad_arguments(tmp_path):
    r = call("design.render", path=str(EXAMPLE_DIR), out=tmp_path / "x.png", size=50)
    assert not r.ok and r.exit_code == 2
    r = call("design.render", path=str(EXAMPLE_DIR), out=tmp_path / "x.png", view="bottom")
    assert not r.ok


def test_overlay_guard_is_called(tmp_path, monkeypatch):
    seen = []

    def recorder(out, design):
        seen.append(Path(out))
        return []
    monkeypatch.setattr("hangar.geom.overlay.guard_output", recorder)
    _render(tmp_path / "a.png")
    assert seen == [tmp_path / "a.png"]


def test_face_budget(tmp_path):
    from hangar.render import render_png
    d = design_mod.load_design(EXAMPLE_DIR)
    out = tmp_path / "f.png"
    render_png(d, out, max_faces=50)
    _, _, rows = decode(out)
    px = [v for row in rows for v in row]
    assert sum(1 for v in px if v < 250) / len(px) > 0.005


def test_op_registered():
    assert "design.render" in registry()
    import tomllib
    ex = tomllib.loads((design_mod.REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["optional-dependencies"]
    assert "matplotlib" in ex["render"] and "matplotlib" in ex["dev"]
