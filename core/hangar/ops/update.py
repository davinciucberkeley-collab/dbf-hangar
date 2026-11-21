"""Weekly team updates: updates/<week>/updates.yaml, published as viewer/updates/<week>/index.html (gitignored)."""
from __future__ import annotations

import html
import re
from pathlib import Path

import yaml

from . import op, OpResult, OpInputError
from ._paths import repo_root, rel

WEEK_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK_RE = re.compile(r"^https?://\S+$")
PAGES_BASE = "https://davinciucberkeley-collab.github.io/dbf-hangar"


def _check_week(week: str) -> None:
    if not WEEK_RE.match(week):
        raise OpInputError("week must be YYYY-MM-DD")


def _data_path(root: Path, week: str) -> Path:
    return root / "updates" / week / "updates.yaml"


def _write_yaml(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))


def _read_entries(path: Path) -> list[dict]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(doc.get("entries") or [])


def _link_ok(root: Path, link: str) -> bool:
    if LINK_RE.match(link):
        return True
    p = Path(link)
    return not p.is_absolute() and ".." not in p.parts and (root / p).exists()


@op(name="update.new", summary="Create updates/<week>/updates.yaml for a week (week = its Monday, YYYY-MM-DD).",
    mutates=True)
def new_op(week: str) -> OpResult:
    _check_week(week)
    root = repo_root()
    path = _data_path(root, week)
    if path.exists():
        raise OpInputError(f"{rel(root, path)} already exists")
    _write_yaml(path, {"week": week, "entries": []})
    return OpResult(True, {"path": rel(root, path)}, changed_files=[rel(root, path)])


@op(name="update.add", summary="Add or replace one person's entry for a week.", mutates=True)
def add_entry_op(week: str, person: str, link: str, changed: str) -> OpResult:
    _check_week(week)
    root = repo_root()
    path = _data_path(root, week)
    if not path.exists():
        raise OpInputError("run plane update new first")
    if not person.strip() or not changed.strip():
        raise OpInputError("person and changed must not be empty")
    if not _link_ok(root, link):
        raise OpInputError("link must be an http(s) URL or an existing repo-relative path")
    entry = {"person": person, "link": link, "changed": changed}
    entries = _read_entries(path)
    for n, old in enumerate(entries):
        if old.get("person") == person:
            entries[n] = entry
            break
    else:
        entries.append(entry)
    _write_yaml(path, {"week": week, "entries": entries})
    return OpResult(True, {"count": len(entries)}, changed_files=[rel(root, path)])


def _page(week: str, entries: list[dict]) -> str:
    w = html.escape(week)
    items = "".join(
        f"<li><strong>{html.escape(e['person'])}</strong>: {html.escape(e['changed'])} "
        f"(<a href=\"{html.escape(e['link'])}\">link</a>)</li>" for e in entries)
    return (f'<!doctype html><html lang="en"><meta charset="utf-8"><title>Weekly update {w}</title>'
            f"<h1>Weekly update {w}</h1><ul>{items}</ul></html>")


def _index(weeks: list[str]) -> str:
    items = "".join(f'<li><a href="{html.escape(w)}/">{html.escape(w)}</a></li>' for w in weeks)
    return (f'<!doctype html><html lang="en"><meta charset="utf-8"><title>Weekly updates</title>'
            f"<h1>Weekly updates</h1><ul>{items}</ul></html>")


@op(name="update.publish", summary="Write viewer/updates/<week>/index.html and rebuild the updates index.",
    mutates=True, render=lambda r: r.data["url"])
def publish_op(week: str) -> OpResult:
    _check_week(week)
    root = repo_root()
    path = _data_path(root, week)
    if not path.exists():
        raise OpInputError("run plane update new first")
    entries = _read_entries(path)
    if not entries:
        raise OpInputError("no entries to publish")
    out_dir = root / "viewer" / "updates"
    page = out_dir / week / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    with open(page, "w", encoding="utf-8", newline="\n") as f:
        f.write(_page(week, entries))
    weeks = sorted((p.parent.name for p in out_dir.glob("*/index.html")), reverse=True)
    index = out_dir / "index.html"
    with open(index, "w", encoding="utf-8", newline="\n") as f:
        f.write(_index(weeks))
    lines = [f"{e['person']}: {e['changed']} - {e['link']}" for e in entries]
    return OpResult(True, {"url": f"{PAGES_BASE}/updates/{week}/", "path": rel(root, page), "lines": lines},
                    changed_files=[rel(root, page), rel(root, index)])
