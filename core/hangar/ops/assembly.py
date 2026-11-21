"""Assembly animation: write a .glb of the design with one animation per assembly step (U2.4-c)."""
from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np

from .. import pdledit
from ..design import load_design
from ..export import export_glb
from . import op, OpResult, OpInputError


@op(name="assembly.animate", summary="Write a .glb of the design with one animation per assembly step (parts slide in from above, in step order).",
    mutates=True, render=lambda r: r.data["path"])
def animate_op(path: str, out: str) -> OpResult:
    try:
        design = load_design(pdledit.resolve_design_path(path))
    except Exception as e:  # noqa: BLE001 - any load failure is bad input
        raise OpInputError(f"cannot load {path}: {e}") from e
    seq = (design.data.get("assembly") or {}).get("sequence") or []
    if not seq:
        raise OpInputError("design has no assembly.sequence")
    steps = sorted(((int(s["step"]), list(s.get("add") or [])) for s in seq), key=lambda t: t[0])
    ids = {c.get("id") for c in (design.components or [])}
    for number, add in steps:
        for cid in add:
            if cid not in ids:
                raise OpInputError(f"step {number}: unknown component {cid}")
    export_glb(design, out)
    glb = Path(out).read_bytes()
    skipped: list[str] = []
    new = _animate_glb(glb, steps, skipped)
    Path(out).write_bytes(new)
    return OpResult(True, {"path": out, "steps": len(steps), "animations": [f"step-{n}" for n, _ in steps]},
                    skipped=skipped, changed_files=[out])


def _animate_glb(glb, steps, skipped):
    _magic, _version, _total = struct.unpack("<4sII", glb[:12])
    jlen, _jt = struct.unpack("<I4s", glb[12:20])
    doc = json.loads(glb[20:20 + jlen])
    off = 20 + jlen
    blen, _bt = struct.unpack("<I4s", glb[off:off + 8])
    binary = bytearray(glb[off + 8:off + 8 + blen])
    while len(binary) % 4:
        binary.append(0)
    names = {n.get("name"): i for i, n in enumerate(doc["nodes"])}
    doc.setdefault("bufferViews", [])
    doc.setdefault("accessors", [])
    doc["animations"] = []

    def accessor(values, type_, with_range):
        arr = np.asarray(values, dtype="<f4")
        data = arr.tobytes()
        doc["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)})
        binary.extend(data)
        acc = {"bufferView": len(doc["bufferViews"]) - 1, "componentType": 5126, "count": len(arr), "type": type_}
        if with_range:
            acc["min"] = [float(arr.min())]
            acc["max"] = [float(arr.max())]
        doc["accessors"].append(acc)
        return len(doc["accessors"]) - 1

    for k, (number, ids) in enumerate(steps):
        time_acc = accessor([float(k), float(k + 1)], "SCALAR", True)
        anim = {"name": f"step-{number}", "samplers": [], "channels": []}
        for cid in ids:
            if cid not in names:
                skipped.append(f"step {number}: {cid} has no geometry")
                continue
            node = doc["nodes"][names[cid]]
            if "matrix" in node:
                raise OpInputError(f"node {cid} uses a matrix; cannot animate it")
            end = [float(x) for x in node.get("translation", [0.0, 0.0, 0.0])]
            start = [end[0], end[1] + 0.15, end[2]]
            out_acc = accessor([start, end], "VEC3", False)
            anim["samplers"].append({"input": time_acc, "output": out_acc, "interpolation": "LINEAR"})
            anim["channels"].append({"sampler": len(anim["samplers"]) - 1,
                                     "target": {"node": names[cid], "path": "translation"}})
        if not anim["channels"]:
            raise OpInputError(f"step {number} adds nothing drawable")
        doc["animations"].append(anim)
    doc["buffers"][0]["byteLength"] = len(binary)
    j = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    j += b" " * (-len(j) % 4)
    body = struct.pack("<I4s", len(j), b"JSON") + j + struct.pack("<I4s", len(binary), b"BIN\x00") + bytes(binary)
    return struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body
