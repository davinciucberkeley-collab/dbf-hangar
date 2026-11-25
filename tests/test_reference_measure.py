"""U12.4 step 3: reference.views and reference.measure on synthetic PNGs."""
from __future__ import annotations

import math
import struct
import zlib

import pytest
from click.testing import CliRunner

from hangar.cli import cli
from hangar.ops import OpInputError, call
from hangar.ops import _png


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(path, rows, mode="gray", palette=None, interlace=0):
    """rows: list of rows; gray: ints, rgb: (r,g,b), rgba: (r,g,b,a), palette: indices."""
    ct = {"gray": 0, "rgb": 2, "palette": 3, "rgba": 6}[mode]
    h, w = len(rows), len(rows[0])
    raw = b""
    for r in rows:
        raw += b"\x00"
        for px in r:
            raw += bytes(px) if isinstance(px, tuple) else bytes([px])
    data = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, interlace))
    if palette:
        data += _chunk(b"PLTE", b"".join(bytes(c) for c in palette))
    data += _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b"")
    path.write_bytes(data)
    return str(path)


def canvas(w, h):
    return [[255] * w for _ in range(h)]


def fill(img, x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            img[y][x] = 0


def save(tmp_path, img, name="a.png"):
    return write_png(tmp_path / name, img)


def test_decode_color_types(tmp_path):
    g = [[0, 50, 100, 255], [10, 20, 30, 40], [255, 128, 7, 0]]
    want = [row[:] for row in g]
    assert _png.decode(write_png(tmp_path / "g.png", g)) == (4, 3, want)
    rgb = [[(v, v, v) for v in r] for r in g]
    assert _png.decode(write_png(tmp_path / "c.png", rgb, "rgb"))[2] == want
    rgba = [[(v, v, v, 255) for v in r] for r in g]
    rgba[0][1] = (0, 0, 0, 0)
    w2 = [r[:] for r in want]
    w2[0][1] = 255
    assert _png.decode(write_png(tmp_path / "a.png", rgba, "rgba"))[2] == w2
    pal = [(i, i, i) for i in range(256)]
    assert _png.decode(write_png(tmp_path / "p.png", g, "palette", palette=pal))[2] == want
    with pytest.raises(ValueError, match="interlaced"):
        _png.decode(write_png(tmp_path / "i.png", g, interlace=1))


def test_measure_rectangle_exact(tmp_path):
    img = canvas(200, 100)
    fill(img, 20, 30, 119, 59)
    p = save(tmp_path, img)
    d = call("reference.measure", image=p, known_axis="width", known_m=10.0, stations=5).data
    assert d["scale_m_per_px"] == 0.1 and d["width_m"] == 10.0 and d["height_m"] == 3.0
    assert d["bbox_px"] == [20, 30, 119, 59] and d["ink_px"] == 3000
    assert all(s["top_m"] == 2.9 and s["bottom_m"] == 0.0 for s in d["column_stations"])
    d = call("reference.measure", image=p, known_axis="height", known_m=3.0).data
    assert d["scale_m_per_px"] == 0.1


def test_measure_triangle_stations(tmp_path):
    img = canvas(130, 120)
    for x in range(10, 110):
        for y in range(99 - (x - 10), 100):
            img[y][x] = 0
    d = call("reference.measure", image=save(tmp_path, img), known_axis="width", known_m=10.0, stations=11).data
    st = d["column_stations"]
    for i, s in enumerate(st):
        x = 10 + round(i * 99 / 10)
        assert s["top_m"] == round((x - 10) * 0.1, 4)
        assert s["bottom_m"] == 0.0
    assert st[0]["top_m"] == 0.0 and st[-1]["top_m"] == 9.9 and st[-1]["x_m"] == 9.9


def test_box_selects_second_view(tmp_path):
    img = canvas(200, 80)
    fill(img, 10, 10, 69, 59)
    fill(img, 120, 10, 179, 49)
    d = call("reference.measure", image=save(tmp_path, img), known_axis="width", known_m=6.0, box="120,10,179,49").data
    assert d["height_m"] == 4.0 and d["bbox_px"] == [120, 10, 179, 49]


def test_ignore_cols_removes_dimension_line(tmp_path):
    img = canvas(200, 100)
    fill(img, 20, 30, 119, 59)
    fill(img, 150, 0, 150, 99)
    p = save(tmp_path, img)
    d = call("reference.measure", image=p, known_axis="height", known_m=3.0, ignore_cols="150-150").data
    assert d["width_m"] == 10.0
    d = call("reference.measure", image=p, known_axis="height", known_m=3.0).data
    assert d["width_m"] != 10.0


def test_rotation_levels_a_tilted_bar(tmp_path):
    img = canvas(200, 60)
    a = math.radians(5)
    for t in range(151):
        img[10 + round(t * math.sin(a))][10 + round(t * math.cos(a))] = 0
    p = save(tmp_path, img)

    def hpx(rot):
        b = call("reference.measure", image=p, known_axis="width", known_m=15.0, rotate_deg=rot).data["bbox_px"]
        return b[3] - b[1] + 1
    assert hpx(0.0) >= 12
    assert hpx(5.0) <= 3


def test_views_splits_three_views(tmp_path):
    img = canvas(300, 300)
    fill(img, 20, 10, 250, 39)
    fill(img, 20, 80, 120, 139)
    fill(img, 180, 80, 280, 139)
    fill(img, 100, 200, 102, 202)
    d = call("reference.views", image=save(tmp_path, img)).data
    assert [v["box"] for v in d["views"]] == [[20, 10, 250, 39], [20, 80, 120, 139], [180, 80, 280, 139]]
    assert d["dropped_small"] == 1 and d["image_px"] == [300, 300]


def test_bad_inputs(tmp_path):
    img = canvas(50, 50)
    fill(img, 5, 5, 20, 20)
    p = save(tmp_path, img)
    bad = tmp_path / "x.png"
    bad.write_bytes(b"not a png at all")
    ok = dict(image=p, known_axis="width", known_m=1.0)
    cases = [
        (dict(ok, image=str(tmp_path / "missing.png")), "missing.png"),
        (dict(ok, image=str(bad)), "x.png"),
        (dict(ok, known_axis="depth"), "known_axis"),
        (dict(ok, known_m=0.0), "known_m"),
        (dict(ok, box="0,0,99,99"), "box"),
        (dict(ok, stations=1), "stations"),
    ]
    for kw, word in cases:
        with pytest.raises(OpInputError, match=word):
            _raise(kw)
        res = call("reference.measure", **kw)
        assert not res.ok and res.exit_code == 2 and word in res.messages[0]


def _raise(kw):
    from hangar.ops import registry
    return registry()["reference.measure"].func(**kw)


def test_cli_help():
    res = CliRunner().invoke(cli, ["reference", "measure", "--help"])
    assert res.exit_code == 0 and "--known-axis" in res.output
