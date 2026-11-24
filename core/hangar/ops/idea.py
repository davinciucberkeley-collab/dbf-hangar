"""Idea records: knowledge/ideas/<date>-<slug>.md, one file per idea per day."""
from __future__ import annotations

import json
import re
from datetime import date

import yaml

from . import op, OpResult, OpInputError
from ._paths import repo_root, rel


@op(name="idea.add", summary="Record an idea as knowledge/ideas/<date>-<slug>.md.", mutates=True,
    render=lambda r: r.data["path"])
def add_op(title: str, body: str, by: str) -> OpResult:
    if not title.strip() or not body.strip() or not by.strip():
        raise OpInputError("title, body and by must not be empty")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40].strip("-") or "idea"
    day = date.today().isoformat()
    root = repo_root()
    target = root / "knowledge" / "ideas" / f"{day}-{slug}.md"
    if target.exists():
        raise OpInputError(f"idea already recorded: {rel(root, target)}")
    target.parent.mkdir(parents=True, exist_ok=True)
    text = f"---\ntitle: {json.dumps(title)}\nby: {json.dumps(by)}\ndate: \"{day}\"\n---\n\n{body}\n"
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    path = rel(root, target)
    return OpResult(True, {"path": path}, changed_files=[path])


def _render_list(res: OpResult) -> str:
    rows = res.data["ideas"]
    if not rows:
        return "no ideas"
    return "\n".join(f"{r['path']}  {r['date']}  {r['by']}  {r['title']}" for r in rows)


@op(name="idea.list", summary="List the recorded ideas (knowledge/ideas/*.md): path, date, title, by.", render=_render_list)
def list_op() -> OpResult:
    root = repo_root()
    rows = []
    for f in sorted((root / "knowledge" / "ideas").glob("*.md")):
        head = {}
        text = f.read_text(encoding="utf-8")
        if text.startswith("---\n") and "\n---\n" in text:
            try:
                parsed = yaml.safe_load(text[4:text.index("\n---\n")])
            except yaml.YAMLError:
                parsed = None
            head = parsed if isinstance(parsed, dict) else {}
        rows.append({"path": rel(root, f), "date": str(head.get("date", f.name[:10])), "title": str(head.get("title", f.stem)),
                     "by": str(head.get("by", ""))})
    return OpResult(True, {"ideas": rows})
