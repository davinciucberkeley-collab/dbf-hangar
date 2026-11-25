"""Minimal read-only PNG decoder to gray (adapted from an untrusted scratch decoder, rewritten; see PROVENANCE.md)."""
from __future__ import annotations

import struct
import zlib

_SIG = b"\x89PNG\r\n\x1a\n"
_MAX_PIXELS = 25_000_000
_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def _unfilter(raw: bytes, h: int, stride: int, bpp: int) -> list[bytearray]:
    rows, prev, q = [], bytearray(stride), 0
    for _ in range(h):
        if q >= len(raw):
            raise ValueError("bad PNG data: truncated")
        f = raw[q]
        line = bytearray(raw[q + 1:q + 1 + stride])
        q += 1 + stride
        if len(line) != stride or f > 4:
            raise ValueError("bad PNG data: truncated or unknown filter")
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        rows.append(line)
        prev = line
    return rows


def _lum(r: int, g: int, b: int) -> int:
    return (r * 299 + g * 587 + b * 114) // 1000


def decode(path) -> tuple[int, int, list[list[int]]]:
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != _SIG:
        raise ValueError("not a PNG")
    pos, idat, palette, hdr = 8, [], b"", None
    while pos + 8 <= len(data):
        n, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if tag == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif tag == b"PLTE":
            palette = body
        elif tag == b"IDAT":
            idat.append(body)
        pos += 12 + n
    if hdr is None:
        raise ValueError("not a PNG: no IHDR")
    w, h, depth, ctype, _, _, interlace = hdr
    if interlace:
        raise ValueError("interlaced PNG not supported")
    if depth == 16:
        raise ValueError("16-bit PNG not supported")
    if depth != 8 or ctype not in _CHANNELS:
        raise ValueError(f"unsupported PNG (bit depth {depth}, colour type {ctype})")
    if w * h > _MAX_PIXELS:
        raise ValueError("image too large")
    ch = _CHANNELS[ctype]
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as e:
        raise ValueError(f"bad PNG data: {e}") from e
    rows = _unfilter(raw, h, w * ch, ch)
    pal = [_lum(palette[i], palette[i + 1], palette[i + 2]) for i in range(0, len(palette) - 2, 3)]
    out = []
    for r in rows:
        if ctype == 0:
            out.append(list(r))
        elif ctype == 4:
            out.append([255 if r[2 * x + 1] < 128 else r[2 * x] for x in range(w)])
        elif ctype == 3:
            if r and max(r) >= len(pal):
                raise ValueError("bad PNG data: palette index out of range")
            out.append([pal[v] for v in r])
        else:
            line = []
            for x in range(w):
                o = x * ch
                if ch == 4 and r[o + 3] < 128:
                    line.append(255)
                else:
                    line.append(_lum(r[o], r[o + 1], r[o + 2]))
            out.append(line)
    return w, h, out
