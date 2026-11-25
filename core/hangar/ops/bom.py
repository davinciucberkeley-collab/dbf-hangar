"""Design bill of materials: record a verification stamp on a line (never scrapes a shop), and cost the BOM."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from ruamel.yaml import YAML

from .. import pdledit
from . import op, OpResult, OpInputError
from ._paths import repo_root, rel


def _load(path: str):
    p = Path(pdledit.resolve_design_path(path))
    if not p.is_absolute():
        p = repo_root() / p
    if not p.is_file():
        raise OpInputError(f"{path}: no such design file")
    text = p.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise OpInputError(f"{path}: cannot parse YAML: {e}") from e
    if not isinstance(data, dict):
        raise OpInputError(f"{path}: not a mapping")
    bom = data.get("bom")
    items = (bom.get("items") if isinstance(bom, dict) else None) or []
    if not items:
        raise OpInputError("design has no bom.items")
    return p, text, data, items


@op(name="bom.verify", summary="Record that someone verified a BOM line (browser, datasheet, in-hand or webfetch). "
                               "Records only; the CLI never scrapes a shop.",
    mutates=True, render=lambda r: r.data["line"])
def verify_op(path: str, item: str, method: Literal["browser", "datasheet", "in-hand", "webfetch"], evidence: str,
              by: str) -> OpResult:
    if not evidence.strip() or not by.strip():
        raise OpInputError("evidence and by must not be empty")
    p, text, data, items = _load(path)
    index = next((i for i, it in enumerate(items) if isinstance(it, dict) and it.get("id") == item), None)
    if index is None:
        raise OpInputError(f"no bom item {item!r}")
    existing = items[index].get("verified")
    if existing is not None and not isinstance(existing, dict):
        raise OpInputError(f"{item}: verified must be a mapping (by, date, method, evidence); edit by hand")
    if existing is not None:
        raise OpInputError(f"{item} already verified by {existing.get('by')} on {existing.get('date')}; edit by hand")

    ruamel_root = YAML().load(text)
    start = ruamel_root["bom"]["items"].lc.item(index)[0]
    lines = text.splitlines(keepends=True)
    if lines[start].lstrip().startswith("- {"):
        raise OpInputError("flow-style bom line; edit by hand")
    eol = "\r\n" if "\r\n" in text else "\n"
    dash = len(lines[start]) - len(lines[start].lstrip())
    last = start
    for n in range(start + 1, len(lines)):
        stripped = lines[n].strip()
        if not stripped:
            continue
        indent = len(lines[n]) - len(lines[n].lstrip())
        if indent <= dash:
            break
        if not stripped.startswith("#"):
            last = n

    today = date.today().isoformat()
    new = (" " * (dash + 2) + f"verified: {{by: {json.dumps(by)}, date: \"{today}\", method: {method}, "
           f"evidence: {json.dumps(evidence)}}}")
    if not lines[last].endswith("\n"):
        lines[last] = lines[last] + eol
    lines.insert(last + 1, new + eol)
    patched = "".join(lines)

    after = yaml.safe_load(patched)
    want = {"by": by, "date": today, "method": method, "evidence": evidence}
    if after["bom"]["items"][index].get("verified") != want:
        raise OpInputError("verification stamp did not round-trip as written")
    pdledit.check_schema(data, after, f"bom[{item}].verified")
    p.write_bytes(patched.encode("utf-8"))
    shown = rel(repo_root().resolve(), p.resolve()) if p.resolve().is_relative_to(repo_root().resolve()) else str(path)
    return OpResult(True, {"path": shown, "item": item, "line": new.strip()}, changed_files=[shown])


@op(name="bom.cost", summary="Total cost of a design's BOM and which lines lack a cost or a verification.",
    render=lambda r: f"total ${r.data['total_usd']:.2f} ({r.data['costed']} lines costed; "
                     f"{len(r.data['missing_cost'])} without cost; {len(r.data['unverified'])} unverified)")
def cost_op(path: str) -> OpResult:
    _, _, _, items = _load(path)
    total = 0.0
    costed = 0
    missing_cost = []
    unverified = []
    for n, it in enumerate(items):
        if not isinstance(it, dict) or "id" not in it:
            raise OpInputError(f"bom.items[{n}]: must be a mapping with an id")
        if isinstance(it.get("qty"), bool) or not isinstance(it.get("qty"), (int, float)):
            raise OpInputError(f"bom item {it['id']}: qty is missing or not a number")
        if "unit_cost_usd" in it:
            if isinstance(it["unit_cost_usd"], bool) or not isinstance(it["unit_cost_usd"], (int, float)):
                raise OpInputError(f"bom item {it['id']}: unit_cost_usd is not a number")
            total += it["qty"] * it["unit_cost_usd"]
            costed += 1
        else:
            missing_cost.append(it["id"])
        if "verified" not in it:
            unverified.append(it["id"])
    data = {"total_usd": round(total, 2), "costed": costed, "missing_cost": missing_cost, "unverified": unverified}
    return OpResult(True, data)


def _render_list(res: OpResult) -> str:
    rows = res.data["items"]
    if not rows:
        return "no bom items"
    w = max(len(r["id"]) for r in rows)
    cost = lambda r: "-" if r["unit_cost_usd"] is None else r["unit_cost_usd"]  # noqa: E731
    return "\n".join(f"{r['id']:<{w}}  x{r['qty']}  {cost(r)}  {'verified' if r['verified'] else 'unverified'}" for r in rows)


@op(name="bom.list", summary="List the BOM lines of a design (id, qty, unit cost, verified, url).", render=_render_list)
def list_op(path: str) -> OpResult:
    _, _, _, items = _load(path)
    rows = []
    for n, it in enumerate(items):
        if not isinstance(it, dict) or "id" not in it:
            raise OpInputError(f"bom.items[{n}]: must be a mapping with an id")
        rows.append({"id": str(it["id"]), "qty": it.get("qty"), "unit_cost_usd": it.get("unit_cost_usd"),
                     "verified": "verified" in it, "url": it.get("url")})
    return OpResult(True, {"items": rows})
