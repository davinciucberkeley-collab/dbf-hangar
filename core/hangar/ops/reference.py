"""Three-view measuring of a reference aircraft PNG: find the views, then read a scaled outline in metres."""
from __future__ import annotations

import math
from pathlib import Path

from . import op, OpResult, OpInputError
from . import _png

MIN_INK = 20


def _load(image: str):
    p = Path(image)
    if not p.is_file():
        raise OpInputError(f"image: no such file {image}")
    try:
        return _png.decode(p)
    except ValueError as e:
        raise OpInputError(f"image {image}: {e} (only non-interlaced 8-bit PNG is supported)") from e


def _ink(gray: list[list[int]], threshold: int, dark_on_light: bool) -> list[list[bool]]:
    if dark_on_light:
        return [[v < threshold for v in row] for row in gray]
    return [[v >= threshold for v in row] for row in gray]


def _runs(flags: list[bool], min_gap: int) -> list[tuple[int, int]]:
    """Spans of True, separated by False runs of at least min_gap."""
    spans, start, last = [], None, None
    for i, f in enumerate(flags):
        if f:
            if start is None:
                start = i
            elif i - last - 1 >= min_gap:
                spans.append((start, last))
                start = i
            last = i
    if start is not None:
        spans.append((start, last))
    return spans


def _render_views(r: OpResult) -> str:
    lines = [f"{v['box']} ink {v['ink_px']}" for v in r.data["views"]]
    return "\n".join(lines + [f"dropped {r.data['dropped_small']} small"])


@op(name="reference.views", summary="Find the separate drawings (views) in a PNG: tight ink boxes in reading order.",
    render=_render_views)
def views(image: str, threshold: int = 128, dark_on_light: bool = True, min_gap: int = 5) -> OpResult:
    w, h, gray = _load(image)
    ink = _ink(gray, threshold, dark_on_light)
    out, dropped = [], 0
    for y0, y1 in _runs([any(r) for r in ink], min_gap):
        band = ink[y0:y1 + 1]
        for x0, x1 in _runs([any(r[x] for r in band) for x in range(w)], min_gap):
            n, ys, xs = 0, [], []
            for j, r in enumerate(band):
                hit = [x for x in range(x0, x1 + 1) if r[x]]
                if hit:
                    n += len(hit)
                    ys.append(j)
                    xs += [hit[0], hit[-1]]
            if n < MIN_INK:
                dropped += 1
                continue
            out.append({"box": [min(xs), y0 + ys[0], max(xs), y0 + ys[-1]], "ink_px": n})
    return OpResult(True, {"image_px": [w, h], "views": out, "dropped_small": dropped})


def _ranges(text: str, name: str) -> list[tuple[int, int]]:
    out = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            a, b = (int(v) for v in part.split("-"))
        except ValueError as e:
            raise OpInputError(f"{name}: expected 'a-b,c-d' pixel ranges, got {text!r}") from e
        out.append((min(a, b), max(a, b)))
    return out


def _render(r: OpResult) -> str:
    d = r.data
    lines = [f"width {d['width_m']} m x height {d['height_m']} m (scale {d['scale_m_per_px']} m/px)",
             "x_m  top_m  bottom_m"]
    lines += [f"{s['x_m']}  {s['top_m']}  {s['bottom_m']}" for s in d["column_stations"]]
    return "\n".join(lines)


@op(name="reference.measure", summary="Measure one view of a PNG in metres from one known dimension; returns per-column "
                                      "and per-row stations of the ink outline.", render=_render)
def measure(image: str, *, known_axis: str, known_m: float, box: str = "", rotate_deg: float = 0.0,
            ignore_cols: str = "", ignore_rows: str = "", stations: int = 21, threshold: int = 128,
            dark_on_light: bool = True) -> OpResult:
    if known_axis not in ("width", "height"):
        raise OpInputError(f"known_axis must be 'width' or 'height', got {known_axis!r}")
    if not known_m > 0:
        raise OpInputError(f"known_m must be > 0, got {known_m}")
    if stations < 2:
        raise OpInputError(f"stations must be >= 2, got {stations}")
    w, h, gray = _load(image)
    if box.strip():
        try:
            x0, y0, x1, y1 = (int(v) for v in box.split(","))
        except ValueError as e:
            raise OpInputError(f"box: expected 'x0,y0,x1,y1', got {box!r}") from e
        if not (0 <= x0 <= x1 < w and 0 <= y0 <= y1 < h):
            raise OpInputError(f"box {box!r} is outside the image ({w}x{h} px) or inverted")
    else:
        x0, y0, x1, y1 = 0, 0, w - 1, h - 1
    cols, rows = _ranges(ignore_cols, "ignore_cols"), _ranges(ignore_rows, "ignore_rows")
    ink = _ink(gray, threshold, dark_on_light)
    pts = set()
    for y in range(y0, y1 + 1):
        if any(a <= y <= b for a, b in rows):
            continue
        r = ink[y]
        for x in range(x0, x1 + 1):
            if r[x] and not any(a <= x <= b for a, b in cols):
                pts.add((x, y))
    if rotate_deg:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        t = math.radians(rotate_deg)
        c, s = math.cos(t), math.sin(t)
        pts = {(round(cx + (x - cx) * c + (y - cy) * s), round(cy - (x - cx) * s + (y - cy) * c)) for x, y in pts}
    if not pts:
        raise OpInputError("box: no ink found in the selected area")
    min_x, max_x = min(p[0] for p in pts), max(p[0] for p in pts)
    min_y, max_y = min(p[1] for p in pts), max(p[1] for p in pts)
    w_px, h_px = max_x - min_x + 1, max_y - min_y + 1
    scale = known_m / (w_px if known_axis == "width" else h_px)

    def m(v: float) -> float:
        return round(v * scale, 4)

    by_col: dict[int, list[int]] = {}
    by_row: dict[int, list[int]] = {}
    for x, y in pts:
        a = by_col.setdefault(x, [y, y])
        a[0], a[1] = min(a[0], y), max(a[1], y)
        b = by_row.setdefault(y, [x, x])
        b[0], b[1] = min(b[0], x), max(b[1], x)

    def pick(n_px: int, lo: int) -> list[int]:
        return [lo + round(i * (n_px - 1) / (stations - 1)) for i in range(stations)]

    col_st = []
    for col in pick(w_px, min_x):
        e = by_col.get(col)
        col_st.append({"x_m": m(col - min_x), "top_m": m(max_y - e[0]) if e else None,
                       "bottom_m": m(max_y - e[1]) if e else None})
    row_st = []
    for row in pick(h_px, min_y):
        e = by_row.get(row)
        row_st.append({"y_m": m(max_y - row), "left_m": m(e[0] - min_x) if e else None,
                       "right_m": m(e[1] - min_x) if e else None})
    return OpResult(True, {
        "scale_m_per_px": round(scale, 6), "width_m": m(w_px), "height_m": m(h_px),
        "bbox_px": [min_x, min_y, max_x, max_y], "ink_px": len(pts),
        "origin": "left edge and bottom edge of the ink", "column_stations": col_st, "row_stations": row_st})
