"""Idea records: knowledge/ideas/<date>-<slug>.md, one file per idea per day."""
from __future__ import annotations

import json
import re
from datetime import date

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
