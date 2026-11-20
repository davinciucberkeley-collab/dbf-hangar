"""Stop hook: block stopping while this session has open prompts. Never raises.

Exit 2 blocks the stop (message on stderr). After 3 blocks in a row the stop is
forced and logged to ledger/events.jsonl. HANGAR_ALLOW_STOP=1 overrides.
"""
import json
import os
import sys
from pathlib import Path

MAX_BLOCKS = 3


def _save(path, counts):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(counts), encoding="utf-8")


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import ledger

    event = json.load(sys.stdin)
    if os.environ.get("HANGAR_ALLOW_STOP") == "1":
        return 0

    root = ledger.project_root(event)
    session = event.get("session_id") or ""
    counts_path = Path(root) / "ledger" / ".stop_blocks.json"
    counts = json.loads(counts_path.read_text(encoding="utf-8")) if counts_path.exists() else {}

    open_items = ledger.open_prompts(root, session)
    if not open_items:
        if session in counts:
            counts.pop(session)
            _save(counts_path, counts)
        return 0

    n = counts.get(session, 0) + 1
    if n > MAX_BLOCKS:
        ledger.log_event(root, {"event": "stop-forced", "session": session,
                                "ids": [p["id"] for p in open_items]})
        counts.pop(session, None)
        _save(counts_path, counts)
        return 0

    counts[session] = n
    _save(counts_path, counts)
    lines = ["Open prompts in this session: " + ", ".join(p["id"] for p in open_items)]
    for p in open_items:
        lines.append(f"- {p['id']}: {(p.get('text') or '')[:100].replace(chr(10), ' ')}")
    lines.append('Address each (python harness/ledger.py addressed <ID> --evidence "...") '
                 "or say why it is not done. Override: HANGAR_ALLOW_STOP=1.")
    print("\n".join(lines), file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        code = main()
    except Exception as e:
        print(f"stop_gate: {e!r}", file=sys.stderr)
        code = 0
    sys.exit(code)
