"""Prompt ledger: append-only JSONL record of user prompts and their status.

Data lives in <root>/ledger/prompts.jsonl (one JSON object per line; the latest
line for an id wins) and <root>/ledger/events.jsonl. Standard library only.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROMPT_TEXT_MAX = 2000
STATUSES = ("open", "addressed", "deferred")
_ID_RE = re.compile(r"^P(\d+)$")


def _now():
    return datetime.now(timezone.utc).isoformat()


def project_root(event=None):
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    if event and event.get("cwd"):
        return Path(event["cwd"])
    return Path(__file__).resolve().parents[1]


def _num(item_id):
    m = _ID_RE.match(str(item_id))
    return int(m.group(1)) if m else None


def _read(root, name):
    path = Path(root) / "ledger" / name
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue  # corrupt line: skip, keep reading
    return out


def _append(root, name, obj):
    path = Path(root) / "ledger" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")


def add_prompt(root, session, text):
    nums = [n for n in (_num(l.get("id")) for l in _read(root, "prompts.jsonl")) if n is not None]
    item_id = f"P{max(nums, default=0) + 1}"
    _append(root, "prompts.jsonl", {
        "id": item_id,
        "session": session,
        "ts": _now(),
        "text": text[:PROMPT_TEXT_MAX],
        "status": "open",
    })
    return item_id


def set_status(root, item_id, status, evidence=""):
    if status not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}, got {status!r}")
    if status in ("addressed", "deferred") and not (evidence or "").strip():
        raise ValueError("evidence")
    known = {l.get("id") for l in _read(root, "prompts.jsonl")}
    if item_id not in known:
        raise KeyError(item_id)
    _append(root, "prompts.jsonl", {
        "id": item_id,
        "ts": _now(),
        "status": status,
        "evidence": evidence,
    })


def prompts(root, session=None):
    state = {}
    for line in _read(root, "prompts.jsonl"):
        pid = line.get("id")
        if pid is None:
            continue
        if pid not in state:
            state[pid] = dict(line)
        else:
            state[pid].update(line)
    items = list(state.values())
    if session is not None:
        items = [p for p in items if p.get("session") == session]
    items.sort(key=lambda p: _num(p.get("id")) or 0)
    return items


def open_prompts(root, session=None):
    return [p for p in prompts(root, session) if p.get("status") == "open"]


def log_event(root, event):
    _append(root, "events.jsonl", dict(event, ts=_now()))


def format_line(p):
    sid = (p.get("session") or "")[:8]
    text = (p.get("text") or "").replace("\n", " ")[:80]
    return f"{p['id']} [{p.get('status')}] s={sid} {text}"


def _main(argv=None):
    parser = argparse.ArgumentParser(prog="ledger.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("addressed")
    a.add_argument("id")
    a.add_argument("--evidence", default="")

    d = sub.add_parser("defer")
    d.add_argument("id")
    d.add_argument("--reason", default="")

    r = sub.add_parser("reopen")
    r.add_argument("id")

    lst = sub.add_parser("list")
    lst.add_argument("--open", action="store_true")
    lst.add_argument("--session", default=None)

    args = parser.parse_args(argv)
    root = project_root()
    try:
        if args.cmd == "addressed":
            set_status(root, args.id, "addressed", args.evidence)
            print(f"{args.id} addressed")
        elif args.cmd == "defer":
            set_status(root, args.id, "deferred", args.reason)
            print(f"{args.id} deferred")
        elif args.cmd == "reopen":
            set_status(root, args.id, "open")
            print(f"{args.id} open")
        elif args.cmd == "list":
            items = open_prompts(root, args.session) if args.open else prompts(root, args.session)
            for p in items:
                print(format_line(p))
    except (ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(_main())
