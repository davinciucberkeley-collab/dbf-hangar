"""Plain-text description of scorecard rows (U19.2). Templates live in describe.yaml; limits come from standards/ through the row's criterion.

Texts are computed at render time and never stored in CheckResult, so the scorecard JSON does not change.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from hangar.design import REPO_ROOT, CheckResult, Scorecard

REGISTRY_PATH = Path(__file__).with_name("describe.yaml")
_FORMAT_ERRORS = (KeyError, ValueError, IndexError, TypeError)
_STATUS_ORDER = {"FAIL": 0, "WARN": 1, "SKIP": 2, "PASS": 4}


@dataclass(frozen=True)
class PartRef:
    id: str
    label: str            # "Hub (cge-001)"


@dataclass(frozen=True)
class RowText:
    check_id: str
    status: str           # PASS / FAIL / WARN / SKIP, unchanged from the row
    family: str           # first two id segments, "T7.wiring"
    title: str            # plain name, from the registry (humanised family if no entry)
    sentence: str         # one sentence; the unwrapped raw message when a template cannot be filled
    hint: str             # "" when the registry has none
    details: str          # the raw message with the report-only prefix removed
    parts: tuple[PartRef, ...]
    group: str            # "part" | "problem" | "design"
    source: str           # first 100 chars of the limit's `source:` (cut at a word), "" if none
    report_only: bool     # message started with gates.REPORT_ONLY_PREFIX
    would_be: str         # data.would_be or data.raw_status or ""
    not_applicable: bool  # CheckResult.not_applicable
    subject: str = ""     # what a folded entry lists: data.joint, else the first part label, else the id tail (used by fold)


def family_of(check_id: str) -> str:
    return ".".join(check_id.split(".")[:2])


_REGISTRY: dict | None = None


def load_registry() -> dict:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    return _REGISTRY


_STANDARDS: dict[str, Any] = {}


def _standards_file(name: str) -> Any:
    path = REPO_ROOT / "standards" / name
    key = str(path)
    if key not in _STANDARDS:
        try:
            _STANDARDS[key] = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            _STANDARDS[key] = None
    return _STANDARDS[key]


def standard_limit(criterion: str) -> dict:
    """{"value", "min", "max", "source"} (those present) of "file#key" in standards/; {} if unknown."""
    if "#" not in criterion:
        return {}
    name, key = criterion.split("#", 1)
    if not name or Path(name).name != name:
        return {}
    doc = _standards_file(name)
    if not isinstance(doc, dict):
        return {}
    entry = doc.get(key)
    if entry is None:
        for v in doc.values():
            if isinstance(v, dict) and key in v:
                entry = v[key]
                break
    if not isinstance(entry, dict):
        return {}
    return {k: entry[k] for k in ("value", "min", "max", "source") if k in entry}


def _cut_words(s: str, n: int) -> str:
    s = s.strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    if s[n] != " " and " " in cut:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(" ,;:")


def _source_text(lim: dict) -> str:
    if "source" not in lim:
        return ""
    src = str(lim["source"]).strip()
    return "source pending" if src == "pending" else _cut_words(src, 100)


def _component(design, comp_id: str) -> dict | None:
    for c in design.components:
        if c.get("id") == comp_id:
            return c
    return None


def _label_of(comp: dict | None, comp_id: str) -> str:
    if comp is None:
        return comp_id
    if comp.get("name"):
        return str(comp["name"])
    desc = str(comp.get("description") or "").strip()
    if desc:
        cuts = [i for i in (desc.find(sep) for sep in (" (", ", ", "; ", " - ")) if i > 0]
        clause = desc[:min(cuts)] if cuts else desc
        clause = _cut_words(clause, 40)
        if clause:
            return clause
    return comp_id.replace("-", " ").replace("_", " ")


def part_label(design, comp_id: str) -> str:
    return _label_of(_component(design, comp_id), comp_id)


def row_parts(design, row: CheckResult) -> list[PartRef]:
    if design is None:
        return []
    comps = {c.get("id"): c for c in design.components}
    d = row.data or {}
    ids: list[str] = []

    def add(x):
        if isinstance(x, str) and x in comps and x not in ids:
            ids.append(x)

    add(d.get("component"))
    if isinstance(d.get("parts"), list):
        for x in d["parts"]:
            add(x)
    pair = d.get("pair")
    if isinstance(pair, list) and len(pair) == 2 and all(isinstance(x, str) and x in comps for x in pair):
        for x in pair:
            add(x)
    if isinstance(d.get("link_pairs"), list):
        for p in d["link_pairs"]:
            if isinstance(p, list):
                for x in p:
                    add(x)
    joint = d.get("joint")
    if isinstance(joint, str):
        att = next((a for a in (design.data.get("attachments") or []) if a.get("id") == joint), None)
        if att is not None:
            add(att.get("parent"))
            add(att.get("child"))
        else:
            add(joint)
    return [PartRef(i, f"{_label_of(comps[i], i)} ({i})") for i in ids]


def _text(v: Any) -> Any:
    if isinstance(v, (list, tuple)):
        return ", ".join(" & ".join(map(str, i)) if isinstance(i, (list, tuple)) else str(i) for i in v)
    return v


def _fmt(template: str, values: dict) -> str:
    return template.format_map(values)


def _hint_template(entry: dict, status: str) -> str:
    h = entry.get("hint")
    if isinstance(h, dict):
        h = h.get(status)
    return h or ""


def _describe(row: CheckResult, design, design_id: str | None) -> RowText:
    from hangar.gates import REPORT_ONLY_PREFIX   # inside: gates imports checks, which imports design

    family = family_of(row.check_id)
    entry = load_registry().get(family) or {}
    report_only = row.message.startswith(REPORT_ONLY_PREFIX)
    details = row.message[len(REPORT_ONLY_PREFIX):] if report_only else row.message
    data = row.data or {}
    parts = tuple(row_parts(design, row))
    lim = standard_limit(row.criterion)
    source = _source_text(lim)

    values: dict[str, Any] = {k: _text(v) for k, v in data.items()}
    for k in ("value", "min", "max"):
        if k in lim:
            values["limit" if k == "value" else k] = lim[k]
    values["source"] = source
    if parts:
        values["label"] = parts[0].label
        values["labels"] = ", ".join(p.label for p in parts)
    if design_id is not None:
        values["design_id"] = design_id
    values["message"] = details
    if entry.get("extract"):
        m = re.search(entry["extract"], details)
        if m:
            values.update({k: v for k, v in m.groupdict().items() if v is not None})

    template = (entry.get("what") or {}).get(row.status)
    variant: dict = {}
    if isinstance(template, list):   # [{when: <data key>, text, hint?}, ..., {text}]: the first item whose key is in row.data wins
        variant = next((v for v in template if not v.get("when") or v["when"] in data), {})
        template = variant.get("text")
    sentence = details
    if template:
        try:
            sentence = _fmt(template, values)
        except _FORMAT_ERRORS:
            sentence = details
    hint = ""
    hint_template = variant["hint"] if "hint" in variant else _hint_template(entry, row.status)
    if hint_template:
        try:
            hint = _fmt(hint_template, values)
        except _FORMAT_ERRORS:
            hint = ""

    tail = family.split(".", 1)[1].replace("_", " ") if "." in family else family
    title = entry.get("title") or (tail[:1].upper() + tail[1:])
    joint = data.get("joint")
    subject = joint if isinstance(joint, str) else (parts[0].label if parts else row.check_id.split(".")[-1])
    return RowText(
        check_id=row.check_id, status=row.status, family=family, title=title, sentence=sentence, hint=hint,
        details=details, parts=parts, group=entry.get("group") or "problem", source=source,
        report_only=report_only, would_be=str(data.get("would_be") or data.get("raw_status") or ""),
        not_applicable=row.not_applicable, subject=subject)


def describe_row(row: CheckResult, design=None) -> RowText:
    return _describe(row, design, design.id if design is not None else None)


def describe_card(card: Scorecard, design=None) -> list[list[RowText]]:
    return [[_describe(r, design, card.design_id) for r in t.results] for t in card.tiers]


def fold(texts: list[RowText]) -> list[dict]:
    reg = load_registry()
    buckets: dict[tuple, list[RowText]] = {}
    for t in texts:
        buckets.setdefault((t.family, t.status, t.not_applicable), []).append(t)
    entries: list[tuple[int, dict]] = []   # (first index, entry)
    first = {id(t): i for i, t in enumerate(texts)}
    for (family, status, na), rows in buckets.items():
        e = reg.get(family) or {}
        if e.get("fold") and len(rows) >= 3:
            subjects = list(dict.fromkeys(r.subject for r in rows))
            labels = ", ".join(subjects[:5]) + (", ..." if len(subjects) > 5 else "")
            try:
                sentence = _fmt(e["fold_what"], {"count": len(rows), "labels": labels})
            except _FORMAT_ERRORS:
                sentence = rows[0].sentence
            hint = ""
            if _hint_template(e, status):
                try:
                    hint = _fmt(_hint_template(e, status), {"count": len(rows), "labels": labels})
                except _FORMAT_ERRORS:
                    hint = ""
            entries.append((first[id(rows[0])], {
                "key": f"{family}|{status}", "status": status, "title": f"{rows[0].title}: {len(rows)} {e.get('fold_noun', 'rows')}",
                "count": len(rows), "sentence": sentence, "hint": hint, "rows": rows, "_na": na}))
        else:
            for r in rows:
                entries.append((first[id(r)], {
                    "key": r.check_id, "status": status, "title": r.title, "count": 1,
                    "sentence": r.sentence, "hint": r.hint, "rows": [r], "_na": na}))

    def order(item):
        idx, e = item
        rank = 3 if (e["status"] == "SKIP" and e["_na"]) else _STATUS_ORDER.get(e["status"], 4)
        return (rank, idx)
    out = []
    for _, e in sorted(entries, key=order):
        e.pop("_na")
        out.append(e)
    return out
