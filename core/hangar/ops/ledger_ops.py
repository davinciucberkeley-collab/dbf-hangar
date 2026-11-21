"""Ledger operations: seed, add, set, check, report and ingest (ledger/items.yaml)."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import jsonschema
import yaml

from . import op, OpResult, OpInputError
from ..ledger import Ledger, SCHEMA_PATH
from ._paths import repo_root, rel


def _ledger() -> tuple[Path, Ledger]:
    root = repo_root()
    return root, Ledger(root / "ledger" / "items.yaml")


@contextmanager
def _input_errors():
    """Ledger raises ValueError (bad value) and KeyError (unknown id): both are bad input."""
    try:
        yield
    except KeyError as e:
        raise OpInputError(f"unknown id {e.args[0]}") from e
    except ValueError as e:
        raise OpInputError(str(e)) from e


@op(name="ledger.seed", summary="Load rulings (plan section 1) and decisions (plan section 3) into the ledger.",
    mutates=True, render=lambda r: f"seeded {r.data['seeded']}")
def seed_op(*, plan: str) -> OpResult:
    src = Path(plan)
    if not src.is_file():
        raise OpInputError(f"{plan}: no such file")
    root, ledger = _ledger()
    with _input_errors():
        n = ledger.seed_from_plan(src)
    return OpResult(True, {"seeded": n}, changed_files=[rel(root, ledger.path)])


@op(name="ledger.add", summary="Add an item and print its id.", mutates=True, render=lambda r: r.data["id"])
def add_op(kind: Literal["ruling", "task", "idea", "decision"], text: str, *, source: str, owner: str = "",
           due: str = "") -> OpResult:
    root, ledger = _ledger()
    with _input_errors():
        item_id = ledger.add(kind, text, source=source, owner=owner, due=due)
    return OpResult(True, {"id": item_id}, changed_files=[rel(root, ledger.path)])


@op(name="ledger.set", summary="Set an item's status. done and decided need evidence; dropped and superseded need decided_in.",
    mutates=True, render=lambda r: f"{r.data['id']} {r.data['status']}")
def set_op(item_id: str, status: Literal["open", "done", "dropped", "superseded", "decided"], *,
           evidence: str = "", decided_in: str = "") -> OpResult:
    root, ledger = _ledger()
    with _input_errors():
        ledger.set(item_id, status, evidence=evidence, decided_in=decided_in)
    return OpResult(True, {"id": item_id, "status": status}, changed_files=[rel(root, ledger.path)])


@op(name="ledger.check", summary="Print evidence and decision problems; exit 1 if there are any.",
    render=lambda r: "\n".join(r.messages))
def check_op() -> OpResult:
    root, ledger = _ledger()
    issues = ledger.check(root)
    data = {"issues": [{"item_id": i.item_id, "kind": i.kind, "message": i.message} for i in issues]}
    messages = [f"{i.item_id} {i.kind}: {i.message}" for i in issues] or ["ledger check: no problems"]
    return OpResult(not issues, data, messages=messages)


@op(name="ledger.report", summary="Markdown summary: counts per kind and status, overdue items, open prompts.",
    render=lambda r: r.data["markdown"])
def report_op(*, today: str = "") -> OpResult:
    root, ledger = _ledger()
    with _input_errors():
        text = ledger.report(today=today or None, prompts=root / "ledger" / "prompts.jsonl")
    return OpResult(True, {"markdown": text})


def _inbox_schema() -> dict:
    props = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["$defs"]["item"]["properties"]
    entry = {"type": "object", "additionalProperties": False, "required": ["kind", "text", "source"],
             "properties": {k: props[k] for k in ("kind", "text", "source", "owner", "due")}}
    return {"type": "object", "additionalProperties": False, "required": ["items"],
            "properties": {"transcript": {"type": "string"}, "items": {"type": "array", "items": entry}}}


def _render_ingest(r: OpResult) -> str:
    if "would_add" in r.data:
        return f"would add {r.data['would_add']}, skip {len(r.skipped)}"
    return f"added {len(r.data['added'])}, skipped {len(r.skipped)}"


@op(name="ledger.ingest", summary="Validate a scout's transcript extract (ledger/inbox/<date>.yaml: items of kind, "
                                  "text, source, owner?, due?) and append it to the ledger.",
    mutates=True, render=_render_ingest)
def ingest_op(path: str, *, dry_run: bool = False) -> OpResult:
    src = Path(path)
    if not src.is_file():
        raise OpInputError(f"{path}: no such file")
    try:
        doc = yaml.safe_load(src.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise OpInputError(f"{path}: cannot parse YAML: {e}") from e
    errors = [f"{'/'.join(map(str, e.absolute_path))}: {e.message}"
              for e in jsonschema.Draft202012Validator(_inbox_schema()).iter_errors(doc)]
    if errors:
        raise OpInputError("; ".join(errors))

    root, ledger = _ledger()
    existing = {}
    for item in ledger.items:
        existing.setdefault(item.text.strip().casefold(), item.id)
    kept = []
    skipped = []
    for entry in doc["items"]:
        key = entry["text"].strip().casefold()
        if key in existing:
            skipped.append(f"duplicate of {existing[key]}: {entry['text']}")
        else:
            kept.append(entry)

    if dry_run:
        return OpResult(True, {"added": [], "would_add": len(kept)}, skipped=skipped)

    items_path = ledger.path
    before = items_path.read_bytes() if items_path.exists() else None
    ids = []
    try:
        for entry in kept:
            ids.append(ledger.add(entry["kind"], entry["text"], source=entry["source"],
                                  owner=entry.get("owner") or "", due=entry.get("due") or ""))
    except Exception as e:  # noqa: BLE001 - roll the ledger back to its exact prior bytes
        if before is None:
            items_path.unlink(missing_ok=True)
        else:
            items_path.write_bytes(before)
        raise OpInputError(f"ingest rolled back: {e}") from e
    changed = [rel(root, items_path)] if ids else []
    return OpResult(True, {"added": ids}, changed_files=changed, skipped=skipped)
