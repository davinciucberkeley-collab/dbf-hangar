"""Ledger of rulings, tasks, ideas and decisions, stored in ledger/items.yaml.

Status changes follow evidence rules (see Ledger.set and Ledger.check). Saving uses the
round-trip YAML helpers in hangar.yamlio and validates against schema/ledger.schema.json.
"""
from __future__ import annotations

import copy
import json
import re
from dataclasses import asdict, dataclass, field, replace
from datetime import date
from pathlib import Path

import jsonschema
from ruamel.yaml.scalarstring import SingleQuotedScalarString
from yaml.nodes import ScalarNode
from yaml.resolver import Resolver

from . import yamlio
from .design import REPO_ROOT

SCHEMA_PATH = REPO_ROOT / "schema" / "ledger.schema.json"
LEDGER_SCHEMA_VERSION = "ledger/1"
KINDS = ("ruling", "task", "idea", "decision")
STATUSES = ("open", "done", "dropped", "superseded", "decided")
PREFIX = {"ruling": "R", "task": "T", "idea": "I", "decision": "D"}
_URL_RE = re.compile(r"^https?://\S+$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")
_UNIT_RE = re.compile(r"U\d+\.\d+")
_RESOLVER = Resolver()


def _check_due(due: str) -> None:
    """due is empty or a real YYYY-MM-DD date; ValueError otherwise."""
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", due):
            raise ValueError(due)
        date.fromisoformat(due)  # rejects 2026-13-45
    except ValueError:
        raise ValueError(f"due must be YYYY-MM-DD, got {due!r}") from None


def _today() -> str:
    return date.today().isoformat()


@dataclass
class Item:
    id: str
    kind: str
    text: str
    source: str
    owner: str = ""
    status: str = "open"
    due: str = ""
    units: list = field(default_factory=list)
    evidence: str = ""
    decided_in: str = ""
    updated: str = ""


@dataclass
class Issue:
    item_id: str
    kind: str
    message: str


def count_table(items, total_row: bool) -> list[str]:
    """Markdown count table: header, separator, one row per kind; plus an '**all**' row when total_row."""
    lines = ["| kind | " + " | ".join(STATUSES) + " | total |", "|" + "---|" * (len(STATUSES) + 2)]
    totals = [0] * len(STATUSES)
    for kind in KINDS:
        rows = [i for i in items if i.kind == kind]
        counts = [sum(1 for i in rows if i.status == s) for s in STATUSES]
        totals = [a + b for a, b in zip(totals, counts)]
        lines.append(f"| {kind} | " + " | ".join(map(str, counts)) + f" | {len(rows)} |")
    if total_row:
        lines.append("| **all** | " + " | ".join(map(str, totals)) + f" | {len(items)} |")
    return lines


def _item_from(d) -> Item:
    return Item(
        id=str(d["id"]), kind=str(d["kind"]), text=str(d["text"]), source=str(d.get("source", "")),
        owner=str(d.get("owner", "")), status=str(d.get("status", "open")), due=str(d.get("due", "") or ""),
        units=[str(u) for u in (d.get("units") or [])], evidence=str(d.get("evidence", "") or ""),
        decided_in=str(d.get("decided_in", "") or ""), updated=str(d.get("updated", "") or ""),
    )


def _quoted(value):
    """Quote strings that YAML 1.1 readers (PyYAML) would read as non-strings (dates, numbers, empty)."""
    if isinstance(value, str) and _RESOLVER.resolve(ScalarNode, value, (True, False)) != "tag:yaml.org,2002:str":
        return SingleQuotedScalarString(value)
    return value


def _plan_rows(lines: list[str], heading: str, prefix: str, ncells: int) -> list[list[str]]:
    """Table rows (cells, stripped) of the plan section whose heading starts with `heading`."""
    start = next((n for n, l in enumerate(lines) if l.startswith(heading)), None)
    if start is None:
        raise ValueError(f"plan section {heading.strip()!r} not found")
    rows = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if not re.match(rf"^\|\s*{prefix}\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != ncells:
            raise ValueError(f"cannot parse plan row ({ncells} cells expected): {line}")
        rows.append(cells)
    if not rows:
        raise ValueError(f"no {prefix}<n> rows in plan section {heading.strip()!r}")
    return rows


class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.items: list[Item] = self._load()

    def _load(self) -> list[Item]:
        if not self.path.exists():
            return []
        doc = yamlio.load(self.path.read_text(encoding="utf-8")) or {}
        return [_item_from(d) for d in (doc.get("items") or [])]

    def _index(self, item_id: str) -> int:
        for n, item in enumerate(self.items):
            if item.id == item_id:
                return n
        raise KeyError(item_id)

    def get(self, item_id) -> Item:
        return self.items[self._index(item_id)]

    def _save(self, items: list[Item]) -> None:
        doc = {"schema": LEDGER_SCHEMA_VERSION, "items": []}
        for item in items:
            d = asdict(item)
            doc["items"].append({k: ([_quoted(u) for u in v] if k == "units" else _quoted(v)) for k, v in d.items()})
        try:
            jsonschema.validate(doc, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
        except jsonschema.ValidationError as e:
            raise ValueError(f"ledger would be invalid: {e.message}") from e
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8", newline="\n") as f:
            f.write(yamlio.dump(doc))
        self.items = items

    def _commit(self, items: list[Item]) -> None:
        old = self.items
        try:
            self._save(items)
        except Exception:
            self.items = old
            raise

    def add(self, kind, text, source, owner="", item_id=None, due="") -> str:
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {', '.join(KINDS)}, got {kind!r}")
        if due:
            _check_due(due)
        if item_id is None:
            prefix = PREFIX[kind]
            nums = [int(i.id[len(prefix):]) for i in self.items
                    if i.id.startswith(prefix) and i.id[len(prefix):].isdigit()]
            item_id = f"{prefix}{max(nums, default=0) + 1}"
        elif any(i.id == item_id for i in self.items):
            raise ValueError(f"{item_id} already exists")
        item = Item(id=item_id, kind=kind, text=text, source=source, owner=owner, due=due, updated=_today())
        self._commit(self.items + [item])
        return item_id

    def set(self, item_id, status, evidence="", decided_in="", *, due=None, units=None, note="") -> None:
        """Set status (with its evidence rules). due, units and note are optional: None or empty leaves the field as it is;
        a note is appended to the text as ' [<note>]'."""
        n = self._index(item_id)
        if due is not None and due != "":
            _check_due(due)
        if status not in STATUSES:
            raise ValueError(f"status must be one of {', '.join(STATUSES)}, got {status!r}")
        item = self.items[n]
        if status in ("done", "decided") and not evidence.strip():
            raise ValueError(f"{status} needs evidence")
        if status in ("dropped", "superseded") and not decided_in.strip():
            raise ValueError(f"{status} needs decided_in")
        kept = decided_in if status in ("dropped", "superseded") else ""
        new = replace(item, status=status, evidence=evidence, decided_in=kept, updated=_today())
        if due:
            new = replace(new, due=due)
        if units:
            new = replace(new, units=[str(u) for u in units])
        if note.strip():
            new = replace(new, text=f"{item.text} [{note.strip()}]")
        items = list(self.items)
        items[n] = new
        self._commit(items)

    def check(self, repo: Path) -> list[Issue]:
        repo = Path(repo).resolve()
        issues = []
        for item in self.items:
            if item.status == "done" and not self._evidence_ok(item.evidence, repo):
                issues.append(Issue(item.id, "missing-evidence",
                                    f"done, but evidence {item.evidence!r} is not a URL, an existing "
                                    f"repo-relative path or a commit id"))
            if item.status in ("dropped", "superseded") and not item.decided_in.strip():
                issues.append(Issue(item.id, "dropped-without-decision", f"{item.status} without decided_in"))
        return issues

    @staticmethod
    def _evidence_ok(evidence: str, repo: Path) -> bool:
        if not evidence.strip():
            return False
        if _URL_RE.match(evidence) or _COMMIT_RE.match(evidence):
            return True
        if Path(evidence).is_absolute():
            return False
        target = (repo / evidence).resolve()
        return target.is_relative_to(repo) and target.exists()

    def report_overdue(self, today: str) -> list[str]:
        return [i.id for i in self.items if i.status == "open" and i.due and i.due < today]

    def report(self, today: str | None = None, prompts: Path | None = None) -> str:
        """Markdown: counts per kind and status, overdue items as of `today`, open prompts in `prompts` (JSONL)."""
        today = today or date.today().isoformat()
        lines = ["# Ledger", ""] + count_table(self.items, total_row=True)
        overdue = [f"- {i} (due {self.get(i).due}): {self.get(i).text}" for i in self.report_overdue(today)]
        latest = {}
        if prompts is not None and Path(prompts).exists():
            for line in Path(prompts).read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                latest[rec.get("id")] = rec.get("status")
        open_prompts = sum(1 for s in latest.values() if s == "open")
        return ("\n".join(lines) + "\n" + f"\n## Overdue as of {today}\n\n" + ("\n".join(overdue) if overdue else "none")
                + f"\n\nOpen prompts: {open_prompts}")

    def seed_from_plan(self, plan: Path) -> int:
        lines = Path(plan).read_text(encoding="utf-8").splitlines()
        rulings = _plan_rows(lines, "## 1. ", "R", 4)
        decisions = _plan_rows(lines, "## 3. ", "D", 6)
        items = list(self.items)
        index = {i.id: n for n, i in enumerate(items)}
        changed = 0
        for rid, who, requirement, unit_cell in rulings:
            units = _UNIT_RE.findall(unit_cell)
            if rid not in index:
                items.append(Item(id=rid, kind="ruling", text=requirement, source=f"plan §1; {who}",
                                  units=units, updated=_today()))
                changed += 1
            else:
                old = items[index[rid]]
                if old.text != requirement or old.units != units:
                    items[index[rid]] = replace(old, text=requirement, units=units, updated=_today())
                    changed += 1
        for did, question, default, _ask, by, status in decisions:
            if not re.fullmatch(r"\d{2}-\d{2}", by):
                raise ValueError(f"cannot parse plan row (by must be MM-DD): {did} | {by}")
            due = f"2026-{by}"
            if did not in index:
                decided = status.startswith("decided")
                items.append(Item(id=did, kind="decision", text=question, source="plan §3", due=due,
                                  status="decided" if decided else "open",
                                  evidence=f"default: {default}" if decided else "", updated=_today()))
                changed += 1
            else:
                old = items[index[did]]
                if old.text != question or old.due != due:
                    items[index[did]] = replace(old, text=question, due=due, updated=_today())
                    changed += 1
        self._commit(items)
        return changed
