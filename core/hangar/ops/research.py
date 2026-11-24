"""Research entries: knowledge/sources/<slug>.md and knowledge/diy-projects/<slug>.md (new from template, check)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml

from . import op, OpResult, OpInputError
from ._paths import repo_root, rel

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

SOURCE_KEYS = ["id", "title", "authors", "year", "url", "type", "retrieved", "verified"]
DIY_KEYS = ["id", "title", "source_url", "source_type", "creator", "date", "retrieved", "configuration",
            "outcome", "outcome_evidence", "verified"]
SOURCE_SECTIONS = ["Summary", "Usable rules / numbers", "How we could use it"]
DIY_SECTIONS = ["What's novel", "How it was built", "Problems and fixes", "Lessons for us"]


@op(name="research.new", summary="Create knowledge/sources/<slug>.md or knowledge/diy-projects/<slug>.md from its template.",
    mutates=True, render=lambda r: r.data["path"])
def new_op(kind: Literal["source", "diy"], slug: str) -> OpResult:
    if not SLUG_RE.fullmatch(slug):      # T100: match() accepts a trailing newline after $
        raise OpInputError(f"slug {slug!r} must match {SLUG_RE.pattern}")
    root = repo_root()
    if kind == "source":
        template = root / "knowledge" / "TEMPLATE-source.md"
        target = root / "knowledge" / "sources" / f"{slug}.md"
    else:
        template = root / "knowledge" / "TEMPLATE-diy-project.md"
        target = root / "knowledge" / "diy-projects" / f"{slug}.md"
    if not template.is_file():
        raise OpInputError(f"template missing: {rel(root, template)}")
    if target.exists():
        raise OpInputError(f"already exists: {rel(root, target)}")
    text = template.read_text(encoding="utf-8").replace("id: <kebab-case-slug>", f"id: {slug}", 1)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    path = rel(root, target)
    return OpResult(True, {"path": path}, changed_files=[path])


def _is_missing(value) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, str):
        return value.startswith("<") or " | " in value
    return False


def _sections(body: str) -> dict[str, str]:
    """Map each `## heading` to its text up to the next `## ` line or end of file."""
    found: dict[str, list[str]] = {}
    current = None
    for line in body.splitlines():
        if line.startswith("## "):
            current = line[3:].rstrip()
            found.setdefault(current, [])
        elif current is not None:
            found[current].append(line)
    return {h: "\n".join(ls).strip() for h, ls in found.items()}


@op(name="research.check", summary="List the frontmatter fields and sections of a knowledge entry that are still "
                                   "empty or still the template placeholder.",
    render=lambda r: "\n".join(r.messages))
def check_op(path: str) -> OpResult:
    root = repo_root()
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    if not p.is_file():
        raise OpInputError(f"{path}: no such file")
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise OpInputError(f"{path}: no frontmatter (text must start with ---)")
    close = lines.index("---", 1)
    try:
        fm = yaml.safe_load("\n".join(lines[1:close]))
    except yaml.YAMLError as e:
        raise OpInputError(f"{path}: cannot parse frontmatter: {e}") from e
    if not isinstance(fm, dict):
        raise OpInputError(f"{path}: frontmatter is not a mapping")
    body = "\n".join(lines[close + 1:])

    kind = "diy" if "source_url" in fm else "source"
    keys = DIY_KEYS if kind == "diy" else SOURCE_KEYS
    sections = DIY_SECTIONS if kind == "diy" else SOURCE_SECTIONS

    missing = []
    for key in keys:
        value = fm.get(key)
        if key == "id":
            if _is_missing(value) or value != p.stem:
                missing.append(key)
        elif _is_missing(value) or key not in fm:
            missing.append(key)
    found = _sections(body)
    for heading in sections:
        text_ = found.get(heading)
        if text_ is None or text_ == "" or text_.startswith("<"):
            missing.append(f"section:{heading}")

    ok = not missing
    messages = ["ok"] if ok else ["missing: " + ", ".join(missing)]
    return OpResult(ok, {"kind": kind, "missing_fields": missing}, messages=messages)
