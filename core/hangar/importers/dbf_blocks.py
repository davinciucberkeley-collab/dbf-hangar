"""YAML blocks for plane.yaml that the DBF-Combined importer adds after the geometry: bom, files, wiring, transport, assembly.
Each *_block returns the text of one top-level key (column 0, ends with a newline)."""
from __future__ import annotations

import csv
import re
from pathlib import Path

import yaml

PROXIES = ("hrd-001", "hrn-001")


def _dump(key: str, value: dict) -> str:
    return yaml.safe_dump({key: value}, sort_keys=False, allow_unicode=True, width=10_000)


def bom_block(root: Path, concept: str, parts_csv: dict[str, dict], commit8: str) -> str:
    by_bom: dict[str, list[str]] = {}
    for pid, row in parts_csv.items():
        for b in set(re.findall(r"BOM ([A-Z]\d{2})", row.get("vendor_or_file", "") or "")):
            by_bom.setdefault(b, []).append((row.get("part_id") or pid).lower())
    path = Path(root) / "redesign" / "qp" / concept / "BOM-A.csv"
    items = []
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            # T94: BOM-A.csv qty already includes spares ("4 + 1 spare" is qty 5). Spares is not stored: PDL bom items have no spares field; part_number keeps the item text.
            it: dict = {"id": r["id"].lower(), "qty": int(r["qty"]), "supplier": r["ship_group"],
                        "part_number": r["item"]}
            if (r["unit_usd"] or "").strip():
                it["unit_cost_usd"] = float(r["unit_usd"])
            url = (r["source_url"] or "").strip()
            if url.startswith("http"):
                it["url"] = url
            if by_bom.get(r["id"]):
                it["component_ids"] = sorted(by_bom[r["id"]])
            date = (r["date_checked"] or "").strip()
            if r["status"] == "verified" and url and date:
                it["verified"] = {"by": f"DBF-Combined BOM-A.csv @ {commit8}", "date": date, "method": "browser"}
            items.append(it)
    return _dump("bom", {"items": items})


def files_block(mesh_ids: list[str], commit8: str) -> str:
    note = f"rebuilt from DBF-Combined {commit8} redesign/qp/A/cad by plane import dbf"
    return _dump("files", {"cad": [{"path": f"meshes/{i}.stl", "format": "stl", "role": "derived", "note": note}
                                   for i in sorted(mesh_ids)]})


def wiring_block(edges: list[dict], wire_ids: set[str], commit8: str) -> str:
    hs = [{"id": "hrn-bat" if e["id"] == "E-HRN-13" else e["id"].lower(), "from": e["part_a"].lower(), "to": e["part_b"].lower()}
          for e in edges if e["id"] in wire_ids]
    return _dump("wiring", {"harnesses": hs})


def transport_block(component_ids: list[str]) -> str:
    ids = sorted(i for i in component_ids if i not in PROXIES)
    return _dump("transport", {"disassembly": [{"group": "packed-airframe", "component_ids": ids}]})


def assembly_block(steps: list[dict], component_ids: list[str]) -> str:
    seq: list[dict] = []
    pending = ""
    placed: set[str] = set()
    for s in steps:
        if not s["parts"]:
            pending += f"; before this step, {s['id']}: {s.get('caption', '')}"
            continue
        add = [p.lower() for p in s["parts"]]
        placed.update(add)
        seq.append({"step": len(seq) + 1, "add": add, "note": f"{s['id']}: {s.get('caption', '')}{pending}"})
        pending = ""
    rest = sorted(set(component_ids) - placed)
    if set(rest) != set(PROXIES):
        raise ValueError("assembly plan leaves components unplaced other than the mass proxies: " + ", ".join(sorted(set(rest) - set(PROXIES))
                         or rest))
    seq.append({"step": len(seq) + 1, "add": rest,
                "note": "mass proxies (hardware lumps, wiring harness): the source plan has no step for them; added last" + pending})
    return _dump("assembly", {"sequence": seq})
