"""Concept A claims generator (U2.5b): DBF-Combined proofs/1 claims plus params-A.json as one claims.yaml.

Reads the generated `claims.*.json` files through `import_proofs1`, declares every referenced
params-A.json value as a constant `parameter` node, rewrites the references that PDL_MAP maps onto
the design (so design changes flow into the claims), lower-cases part ids to PDL component ids,
validates, and writes `<out_dir>/claims.yaml`. Nothing else is written.
"""
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from ..claims.graph import ClaimGraph, ClaimGraphError, SCHEMA_PATH, import_proofs1

# "P:<group>.<key>" of params-A.json -> PDL ref (same unit), or (PDL ref, scale): params value = PDL value x scale.
PDL_MAP = {
    "P:mission.cruise_ms": "P:requirements.cruise_speed_mps",
    "P:mission.clmax": "P:flight.cl_max",
    "P:env.rho_kgm3": "P:flight.air_density_kgm3",
    "P:req.mass_gate_kg": ("P:requirements.mtow_g", 0.001),
    "P:mass.pack_g": "P:components[pwr-001].mass_g",
    "P:cg.chord_mm": "P:components[wng-001].planform.lifting_surface.root_chord",
}


def _commit(dbf_root) -> str:
    try:
        out = subprocess.run(["git", "-C", str(dbf_root), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def _slug(ref: str) -> str:
    return ref[2:].replace("_", "-").replace(".", "-").upper()


def _split(ref: str) -> tuple[str, str]:
    group, _, name = ref[2:].partition(".")
    return group, name


def import_claims(dbf_root, concept: str = "A", out_dir=None, log=print) -> Path:
    if out_dir is None:
        raise ValueError("out_dir is required")
    qp = Path(dbf_root) / "redesign" / "qp" / concept
    files = sorted((qp / "proofs").glob("claims.*.json"))
    if not files:
        raise FileNotFoundError(f"no claims.*.json under {qp / 'proofs'}")
    graph = import_proofs1(files)
    params = json.loads((qp / f"params-{concept}.json").read_text(encoding="utf-8"))
    imported = [copy.deepcopy(n) for n in graph.nodes.values()]
    pfile = f"redesign/qp/{concept}/params-{concept}.json"

    def entry_of(ref: str) -> dict:
        group, name = _split(ref)
        e = params.get(group, {}).get(name) if isinstance(params.get(group), dict) else None
        if not isinstance(e, dict) or "value" not in e:
            raise ClaimGraphError(f"{ref}: not in params-{concept}.json")
        return e

    # 1. PDL_MAP: scale-1 refs become PDL paths; scaled refs become a unit-conversion claim.
    scaled: dict[str, str] = {}   # ref -> claim id, in first-reference order

    def remap(ref):
        if not (isinstance(ref, str) and ref in PDL_MAP):
            return ref
        target = PDL_MAP[ref]
        if isinstance(target, str):
            return target
        scaled.setdefault(ref, f"CL-PDL-{_slug(ref)}")
        return scaled[ref]

    for n in imported:
        if n.get("type") == "calculation":
            n["inputs"] = {k: remap(v) for k, v in n["inputs"].items()}
        elif n.get("type") == "claim" and isinstance(n.get("limit"), dict) and "ref" in n["limit"]:
            n["limit"]["ref"] = remap(n["limit"]["ref"])
        if n.get("type") == "claim" and "parts" in n:
            n["parts"] = [p.lower() for p in n["parts"]]

    # 2. Remaining P: refs become constant parameter nodes, in first-reference order.
    refs: list[str] = []

    targets = {t if isinstance(t, str) else t[0] for t in PDL_MAP.values()}

    def see(ref):
        if isinstance(ref, str) and ref.startswith("P:") and ref not in targets and ref not in refs:
            refs.append(ref)

    for n in imported:
        if n.get("type") == "calculation":
            for v in n["inputs"].values():
                see(v)
        elif n.get("type") == "claim" and isinstance(n.get("limit"), dict):
            see(n["limit"].get("ref"))
    sources = {n["id"] for n in imported if n.get("type") == "source"}
    pnodes = []
    for ref in refs:
        e = entry_of(ref)
        group, name = _split(ref)
        node = {"id": ref, "type": "parameter", "title": f"{group}.{name}", "value": e["value"]}
        if "unit" in e:
            node["unit"] = e["unit"]
        notes = []
        src = e.get("source")
        if src is not None:
            if src in sources:
                node["source"] = src
            else:
                notes.append(f"source {src}")
        if "status" in e:
            node["status"] = e["status"]
        if e.get("note"):
            notes.append(str(e["note"]))
        if notes:
            node["note"] = "\n".join(notes)
        node["file"] = pfile
        pnodes.append(node)

    conv = []
    for ref, cid in scaled.items():
        group, name = _split(ref)
        pdl_ref, k = PDL_MAP[ref]
        slug = _slug(ref)
        conv.append({"id": f"P:scale.{group}.{name}", "type": "parameter", "title": f"unit scale {group}.{name}",
                     "value": k, "unit": "-", "note": "params value = PDL value x scale"})
        conv.append({"id": f"CALC-PDL-{slug}", "type": "calculation",
                     "title": f"PDL value in the claims' unit: {group}.{name}", "function": "scale_value",
                     "inputs": {"v": pdl_ref, "k": f"P:scale.{group}.{name}"}, "equation": "value = PDL value x scale"})
        conv.append({"id": cid, "type": "claim",
                     "title": f"PDL value of {group}.{name} (unit conversion, not a requirement)",
                     "calc": f"CALC-PDL-{slug}", "output": "value", "unit": entry_of(ref).get("unit", "-"),
                     "how": "Unit conversion of a design value so design.set flows into the claims."})

    nodes = pnodes + conv + imported
    ClaimGraph(nodes, design=None)
    doc = {"schema": "claims/1", "nodes": nodes}
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errs = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(map(str, e.absolute_path)))[:5]
    if errs:
        raise ClaimGraphError("; ".join(f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errs))

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "claims.yaml"
    header = (f"# Concept {concept} claims, imported by hangar.importers.dbf_claims from DBF-Combined @ {_commit(dbf_root)}.\n"
              f"# GENERATED: edit the importer or the source claims, not this file. Parameters are constants read from params-{concept}.json;\n"
              "# calculations are registered functions in core/hangar/calcs (D14).\n")
    body = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=1000)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(header + body)
    count = lambda t: sum(1 for n in nodes if n["type"] == t)  # noqa: E731
    log(f"claims.yaml: {len(nodes)} nodes, {len(pnodes)} parameters declared, {count('claim')} claims, "
        f"{count('calculation')} calculations")
    return path
