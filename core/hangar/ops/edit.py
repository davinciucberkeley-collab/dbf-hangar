"""Edit, sweep, diff, copy, propose (U1.4). Every edit goes through hangar.pdledit; plane.yaml is never re-emitted."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml

from . import op, OpResult, OpInputError
from .. import design as design_mod
from .. import pdledit
from ..checks import validate
from ..design import FAIL, load_design
from ..mass import mass_properties

SWEEP_ROOT = design_mod.REPO_ROOT / ".sweeps"
GH_REPO = "davinciucberkeley-collab/dbf-hangar"
OWNER_TRAILER = "Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>"
_SKIP_COPY = ("fea", ".sweeps", "CHANGELOG.yaml", "baseline.json", "import-report.json", "__pycache__")


def _plane(path: str) -> Path:
    p = pdledit.resolve_design_path(path)
    if p.suffix != ".yaml" or not p.is_file():
        raise OpInputError(f"{path}: no plane.yaml found")
    return p


def _text(p: Path) -> str:
    return p.read_bytes().decode("utf-8")     # never read_text: it would turn CRLF into LF


@op(name="design.set", summary="Change or add values in plane.yaml (byte-preserving; --kind add also takes one-line [list] or {mapping} values; --also KEY=VALUE for more pairs in one atomic call) and log them in CHANGELOG.yaml.",
    mutates=True, render=lambda r: "\n".join(r.messages))
def set_op(path: str, key: str, *, value: str, why: str,
           kind: Literal["add", "subtract", "modify"] = "modify", also: list[str] = None) -> OpResult:
    plane = _plane(path)
    text = _text(plane)
    if not why.strip():
        raise OpInputError("why must not be empty")
    pairs = [(key, value)]
    for item in also or []:
        k, sep, v = item.partition("=")
        if not sep or not k.strip():
            raise OpInputError("--also needs KEY=VALUE")
        pairs.append((k.strip(), v))
    if len({k for k, _ in pairs}) != len(pairs):
        raise OpInputError("a key is given more than once")
    before = yaml.safe_load(text)
    working, entries = text, []
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for k, raw in pairs:
        new = pdledit.parse_value(raw) if kind == "add" else pdledit.parse_scalar(raw)
        data = yaml.safe_load(working)
        if pdledit.exists(data, k):
            if isinstance(new, (list, dict)):
                raise OpInputError(f"{k}: already set; a list or mapping cannot replace an existing value")
            old = pdledit.get_value(data, k)
            if len(pairs) == 1 and old == new and type(old) is type(new):
                return OpResult(True, {"key": k, "old": old, "new": new, "changed": False}, [f"{k}: unchanged"])
            working = pdledit.patch_text(working, k, new)
        elif kind == "add":
            old = None
            working = pdledit.add_value(working, k, new)
        else:
            pdledit.get_value(data, k)      # raises the "no key" error
        entries.append({"date": stamp, "key": k, "old": old, "new": new, "why": why, "kind": kind})
    pdledit.check_schema(before, yaml.safe_load(working), key)
    log = plane.with_name("CHANGELOG.yaml")
    eol = "\r\n" if "\r\n" in text else "\n"
    log_text = _text(log) if log.exists() else ""
    if log_text.strip() == "[]":
        log_text = ""
    block = yaml.safe_dump(entries, sort_keys=False, allow_unicode=True).replace("\n", eol)
    if log_text and not log_text.endswith("\n"):
        log_text += eol
    combined = log_text + block
    parsed = yaml.safe_load(combined)
    if not isinstance(parsed, list) or len(parsed) < len(entries) or parsed[-len(entries):] != entries:
        raise OpInputError("CHANGELOG.yaml is not a YAML list; fix it by hand")
    plane.write_bytes(working.encode("utf-8"))
    log.write_bytes(combined.encode("utf-8"))
    msgs = [f"{e['key']}: {e['old']!r} -> {e['new']!r}" for e in entries]
    return OpResult(True, {"key": key, "old": entries[0]["old"], "new": entries[0]["new"], "kind": kind, "changed": True,
                           "changes": [{"key": e["key"], "old": e["old"], "new": e["new"]} for e in entries]},
                    msgs, changed_files=[str(plane), str(log)])


@op(name="design.diff", summary="List the keys whose values differ between two designs.",
    render=lambda r: "\n".join(f"{c['key']}: {c['a']!r} -> {c['b']!r}" for c in r.data["changes"]) or "no differences")
def diff_op(a: str, b: str) -> OpResult:
    fa = pdledit.flatten(yaml.safe_load(_text(_plane(a))))
    fb = pdledit.flatten(yaml.safe_load(_text(_plane(b))))
    keys = list(fa) + [k for k in fb if k not in fa]
    changes = [{"key": k, "a": fa.get(k), "b": fb.get(k)} for k in keys
               if k not in fa or k not in fb or fa[k] != fb[k]]
    return OpResult(True, {"changes": changes})


@op(name="design.copy", summary="Copy a design folder to a new id (without fea/ and logs).",
    mutates=True, render=lambda r: r.data["path"])
def copy_op(src: str, new_id: str) -> OpResult:
    from ..cli import ID_RE
    if not ID_RE.match(new_id):
        raise OpInputError(f"bad id {new_id!r}")
    src_dir = _plane(src).parent
    dst = Path(design_mod.DESIGNS_DIR) / new_id
    if dst.exists():
        raise OpInputError(f"{dst} already exists")
    shutil.copytree(src_dir, dst, ignore=shutil.ignore_patterns(*_SKIP_COPY))
    p = dst / "plane.yaml"
    try:
        p.write_bytes(pdledit.patch_text(_text(p), "id", new_id).encode("utf-8"))
    except OpInputError:
        shutil.rmtree(dst)
        raise
    return OpResult(True, {"path": str(p)}, [f"copied {src_dir.name} -> {new_id}"], changed_files=[str(p)])


@op(name="design.sweep", summary="Try several values for one key; each goes to a scratch copy (source untouched).",
    render=lambda r: "\n".join(
        f"{x['value']}: accepted={x['accepted']} mass_g={x['mass_g']} static_margin={x['static_margin']} "
        f"stall_speed_mps={x['stall_speed_mps']} hover_tw={x['hover_tw']} failures={x['failures']}"
        for x in r.data["rows"]))
def sweep_op(path: str, key: str, *, values: list[str]) -> OpResult:
    plane = _plane(path)
    text = _text(plane)
    before = yaml.safe_load(text)
    if not values:
        raise OpInputError("give at least one value")
    pdledit.get_value(before, key)
    pairs = []
    for raw in values:
        t = pdledit.patch_text(text, key, pdledit.parse_scalar(raw))
        pdledit.check_schema(before, yaml.safe_load(t), key)
        pairs.append((raw, t))
    did = str(before.get("id", plane.parent.name))
    root = SWEEP_ROOT / did
    if root.exists():
        shutil.rmtree(root)
    rows = []
    for n, (raw, t) in enumerate(pairs, 1):
        dst = root / str(n)
        shutil.copytree(plane.parent, dst, ignore=shutil.ignore_patterns("fea", ".sweeps"))
        (dst / "plane.yaml").write_bytes(t.encode("utf-8"))
        d = load_design(dst)
        card = validate(d)
        by = {r.check_id: r for tr in card.tiers for r in tr.results}
        rows.append({
            "value": raw,
            "accepted": card.accepted,
            "mass_g": round(mass_properties(d)["mass_g"], 3),
            "static_margin": by["T3.static_margin"].data.get("static_margin") if "T3.static_margin" in by else None,
            "stall_speed_mps": by["T3.stall"].data.get("stall_mps") if "T3.stall" in by else None,
            "hover_tw": by["T3.hover_tw"].data.get("thrust_to_weight") if "T3.hover_tw" in by else None,
            "failures": sorted(c for c, r in by.items() if r.status == FAIL),
        })
    return OpResult(True, {"rows": rows, "sweep_dir": str(root)}, [f"{len(rows)} designs in {root}"])


def _gh() -> str:
    return os.environ.get("HANGAR_GH") or shutil.which("gh") or "C:/Program Files/GitHub CLI/gh.exe"


def _run(argv: list[str], cwd: str) -> str:
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise OpInputError(f"{argv[0]} not found; set HANGAR_GH to the gh executable") from e
    if p.returncode != 0:
        raise OpInputError(f"{' '.join(argv[:4])} failed: {(p.stderr or p.stdout).strip()}")
    return p.stdout


@op(name="design.propose", summary="Commit a design change on a new branch, push it and open a PR against main.",
    mutates=True, render=lambda r: r.data["pr_url"])
def propose_op(path: str, title: str) -> OpResult:
    plane = _plane(path)
    ddir = str(plane.parent)
    did = str(yaml.safe_load(_text(plane))["id"])
    if not title.strip():
        raise OpInputError("title must not be empty")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40].strip("-") or "change"
    branch = f"design/{did}/{slug}"
    subject = f"design({did}): {title}"
    root = _run(["git", "-C", ddir, "rev-parse", "--show-toplevel"], ddir).strip()
    if _run(["git", "-C", root, "status", "--porcelain", "--", ddir], root).strip() == "":
        raise OpInputError(f"no uncommitted changes under {ddir}")
    start = _run(["git", "-C", root, "rev-parse", "--abbrev-ref", "HEAD"], root).strip()
    body = f"Design change proposed with `plane design propose`.\n\nDesign: {did}\nBranch: {branch}"
    _run(["git", "-C", root, "switch", "-c", branch], root)
    try:
        _run(["git", "-C", root, "add", "--", ddir], root)
        _run(["git", "-C", root, "commit", "-m", f"{subject}\n\n{OWNER_TRAILER}"], root)
        _run(["git", "-C", root, "push", "-u", "origin", branch], root)
        out = _run([_gh(), "-R", GH_REPO, "pr", "create", "--head", branch, "--base", "main",
                    "--title", subject, "--body", body], root)
    finally:
        _run(["git", "-C", root, "switch", start], root)
    url = [l for l in out.splitlines() if l.strip()][-1].strip()
    return OpResult(True, {"pr_url": url, "branch": branch}, [url])
