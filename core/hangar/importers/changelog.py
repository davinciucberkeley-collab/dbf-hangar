"""DBF-Combined decisions as ledger `decision` items (U2.5b).

CHANGE-LOG.md table rows `D-<n>[letter]` become items with their own id; DECISIONS.md headings
`## D<n>. title` become `DD-<n>` (a namespace separate from the plan's D1..D14).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ..ledger import Item, Ledger, _today

SUPERSEDED_BY_D9 = {1, 13, 14}


def _commit(dbf_root) -> str:
    try:
        out = subprocess.run(["git", "-C", str(dbf_root), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def _clean(s: str) -> str:
    return " ".join(s.replace("*", "").split())


def import_decisions(dbf_root, ledger_path, log=print) -> dict:
    root = Path(dbf_root)
    short = _commit(root)
    today = _today()
    ledger = Ledger(Path(ledger_path))
    present = {i.id for i in ledger.items}
    new: list[Item] = []
    counts = {"changelog": 0, "decisions_md": 0, "skipped": 0, "duplicates": 0}

    def add(item: Item, key: str):
        if item.id in present:
            counts["skipped"] += 1
            return
        present.add(item.id)
        new.append(item)
        counts[key] += 1

    cl = root / "redesign" / "params" / "CHANGE-LOG.md"
    if not cl.exists():
        raise FileNotFoundError(str(cl))
    seen: set[str] = set()
    for line in cl.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = cells[1:-1] if line.rstrip().endswith("|") else cells[1:]
        if len(cells) < 2:
            continue
        first = cells[0].replace("*", "").strip()
        m = re.match(r"^D-(\d+[a-z]*)\b(.*)$", first)
        if not m:
            if re.match(r"^[A-Za-z]+-\d+", first):
                log(f"row without a D-number skipped: {first[:60]}")
            continue
        did = f"D-{m.group(1)}"
        rest = m.group(2).strip()
        rev = re.match(r"^rev (\d+)( minors)?", rest)
        if rev and not did[-1].isalpha():
            did += chr((97 if rev.group(2) else 96) + int(rev.group(1)))
        if did in seen:
            counts["duplicates"] += 1
            continue
        seen.add(did)
        add(Item(id=did, kind="decision", text=_clean(f"{rest} {cells[1]}"), source=f"CHANGE-LOG#{did}", owner="",
                 status="open" if rest.upper().startswith("(PROPOSED") else "decided", due="", units=[],
                 evidence=f"DBF-Combined redesign/params/CHANGE-LOG.md @ {short}", decided_in="", updated=today),
            "changelog")

    dm = root / "DECISIONS.md"
    if not dm.exists():
        log(f"{dm} not found, DECISIONS.md items skipped")
    else:
        lines = dm.read_text(encoding="utf-8").splitlines()
        heads = [(n, re.match(r"^## D(\d+)\. (.+)$", l)) for n, l in enumerate(lines)]
        heads = [(n, m) for n, m in heads if m]
        ends = [n for n, _ in heads[1:]] + [len(lines)]
        # a section also ends at any other "## " heading
        for (start, m), end in zip(heads, ends):
            num = int(m.group(1))
            text = m.group(2).strip()
            for l in lines[start + 1:end]:
                if l.startswith("## "):
                    break
                if "Decision needed:" in l:
                    text += " " + _clean(re.sub(r"^\s*-\s*", "", l))
                    break
            moot = num in SUPERSEDED_BY_D9
            add(Item(id=f"DD-{num}", kind="decision", text=text, source=f"DECISIONS.md#D{num}", owner="",
                     status="superseded" if moot else "open", due="", units=[], evidence="",
                     decided_in="D9" if moot else "", updated=today),
                "decisions_md")

    if new:
        ledger._commit(ledger.items + new)
    log(f"decisions: {counts['changelog']} from CHANGE-LOG, {counts['decisions_md']} from DECISIONS.md, "
        f"{counts['skipped']} already present, {counts['duplicates']} duplicate rows")
    return counts
