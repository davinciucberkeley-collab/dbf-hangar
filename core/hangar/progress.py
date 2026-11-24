"""Generate PROGRESS.md from the plan, reviews/ and ledger/items.yaml. Pure and deterministic."""
from __future__ import annotations

import re
from pathlib import Path

from .ledger import Ledger, count_table

UNIT_RE = re.compile(r"^### Unit (U\d+\.\d+): (.*)$")
UNIT_ID_RE = re.compile(r"U\d+\.\d+")
WAVE_RE = re.compile(r"^\|\s*(W\d+\b[^|]*)\|[^|]*\|([^|]*)\|")
CHECK_RE = re.compile(r"^- \[( |x)\]")
REVIEW_HEAD_RE = re.compile(r"^## (U\d+\.\d+[a-z]?)\b")
SUB_SUFFIX_RE = re.compile(r"[a-z]$")
VERDICT_RE = re.compile(r"^###\s+Verdict\b[^:\n]*:\s*(ACCEPT|REJECT)\b")


def active_plan(root: Path) -> Path:
    """Newest plans/*.md by file name (same rule as harness/hooks/agent_gate.py)."""
    plans = sorted((Path(root) / "plans").glob("*.md"), key=lambda p: p.name)
    if not plans:
        raise FileNotFoundError("no plans/*.md")
    return plans[-1]


def archive_path(plan: Path) -> Path:
    """plans/<plan stem>/archive.md: finished units moved out of the plan. A sub-folder, so it is never a plans/*.md plan."""
    return Path(plan).with_suffix("") / "archive.md"


def parse_units(lines: list[str]) -> dict[str, dict]:
    """Units under '## 7.' -> {id: {title, done, total}}. Checkboxes inside code fences are ignored."""
    units: dict[str, dict] = {}
    in_units = False
    fenced = False
    current = None
    for line in lines:
        if line.startswith("## "):
            in_units = line.startswith("## 7.")
            current = None
            fenced = False
            continue
        if not in_units:
            continue
        m = UNIT_RE.match(line)
        if m:
            current = m.group(1)
            units[current] = {"title": m.group(2).strip(), "done": 0, "total": 0}
            fenced = False
            continue
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if current and not fenced:
            c = CHECK_RE.match(line)
            if c:
                units[current]["total"] += 1
                if c.group(1) == "x":
                    units[current]["done"] += 1
    return units


def parse_waves(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Rows of the '## 6.' table whose first cell starts with W<digit> -> [(wave name, [unit ids])]."""
    waves = []
    in_sched = False
    for line in lines:
        if line.startswith("## "):
            in_sched = line.startswith("## 6.")
            continue
        if line.startswith("### "):
            in_sched = False
        if in_sched:
            m = WAVE_RE.match(line)
            if m:
                waves.append((m.group(1).strip(), UNIT_ID_RE.findall(m.group(2))))
    return waves


def latest_verdicts(root: Path) -> dict[str, str]:
    """Heading id -> ACCEPT/REJECT. Rule: files in reviews/*.md sorted by name; inside a file, each '## U<n>.<n>' or
    '## U<n>.<n><a-z>' section (sub-units are keyed by their own id, e.g. 'U2.4a'); the LAST line in that section
    matching '### Verdict...: ACCEPT|REJECT' wins; later files override earlier."""
    verdicts: dict[str, str] = {}
    for path in sorted((Path(root) / "reviews").glob("*.md"), key=lambda p: p.name):
        unit = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                m = REVIEW_HEAD_RE.match(line)
                unit = m.group(1) if m else None
                continue
            v = VERDICT_RE.match(line)
            if v and unit:
                verdicts[unit] = v.group(1)
    return verdicts


def parent_verdicts(verdicts: dict[str, str]) -> dict[str, str]:
    """Roll heading ids up to unit ids: 'U2.4a' counts for 'U2.4'. A unit is REJECT if any of its sections
    (its own heading or any sub-unit heading) is REJECT, else ACCEPT."""
    out: dict[str, str] = {}
    for hid, verdict in verdicts.items():
        parent = SUB_SUFFIX_RE.sub("", hid)
        if verdict == "REJECT" or parent not in out:
            out[parent] = verdict
    return out


def _status(done: int, total: int) -> str:
    if total and done == total:
        return "done"
    return "in progress" if done else "not started"


def _unit_row(uid: str, u: dict, verdicts: dict[str, str]) -> str:
    return f"| {uid} | {u['title']} | {u['done']}/{u['total']} | {_status(u['done'], u['total'])} | {verdicts.get(uid, '-')} |"


SYSTEM_LINE = (
    "DBF Hangar keeps the team's aircraft designs in one format (PDL), one tool (`plane`: CLI, MCP and Studio) "
    "and one set of checks (`standards/`). v1.0 is due 2026-12-02."
)
LEAD_OWNERS = ("", "Tristan", "conductor")  # every other owner is a teammate
TEAM_LIST_MAX = 10


def _id_num(item_id: str) -> int:
    m = re.search(r"\d+", item_id)
    return int(m.group()) if m else 0


def _cut(text: str, limit: int = 100) -> str:
    """Shorten to at most `limit` characters at a word boundary, marking the cut with an ellipsis."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip() + "..."


def summary_lines(waves, units: dict, items) -> list[str]:
    """One-page reader summary: what the system is, units by wave, open ledger items by owner and for teammates."""
    out = ["## Summary", "", SYSTEM_LINE, "", "| area | units | done |", "|---|---|---|"]
    for name, ids in waves:
        present = [u for u in ids if u in units]
        if present:
            done = sum(1 for u in present if _status(units[u]["done"], units[u]["total"]) == "done")
            out.append(f"| {name} | {len(present)} | {done} |")
    in_wave = {u for _, ids in waves for u in ids}
    other = [u for u in units if u not in in_wave]
    if other:
        done = sum(1 for u in other if _status(units[u]["done"], units[u]["total"]) == "done")
        out.append(f"| Other (no wave row) | {len(other)} | {done} |")
    all_done = sum(1 for u in units.values() if _status(u["done"], u["total"]) == "done")
    out.append(f"| **all** | {len(units)} | {all_done} |")
    open_items = [i for i in items if i.status == "open"]
    out += ["", "### Open ledger items by owner", "", "| owner | open | next due |", "|---|---|---|"]
    for owner in sorted({i.owner for i in open_items}, key=lambda o: (o == "", o)):
        mine = [i for i in open_items if i.owner == owner]
        dues = sorted(i.due for i in mine if i.due)
        out.append(f"| {owner or '(unassigned)'} | {len(mine)} | {dues[0] if dues else '-'} |")
    team = sorted((i for i in open_items if i.owner not in LEAD_OWNERS), key=lambda i: (i.due or "9999", _id_num(i.id)))
    out += ["", "### Open items for teammates", ""]
    out += [f"- {i.id} ({i.owner}, due {i.due or '-'}): {_cut(i.text)}" for i in team[:TEAM_LIST_MAX]] or ["none"]
    if len(team) > TEAM_LIST_MAX:
        out.append(f"- and {len(team) - TEAM_LIST_MAX} more in `ledger/items.yaml`")
    return out


def build_progress(root: Path, today: str | None = None) -> str:
    root = Path(root)
    plan = active_plan(root)
    lines = plan.read_text(encoding="utf-8").splitlines()
    units: dict[str, dict] = {}
    archive = archive_path(plan)
    if archive.is_file():
        units.update(parse_units(archive.read_text(encoding="utf-8").splitlines()))
    units.update(parse_units(lines))  # a unit still in the plan wins over an archived copy
    verdicts = parent_verdicts(latest_verdicts(root))
    out = [
        "# Progress",
        "",
        f"> GENERATED by `plane progress --write` from `plans/{plan.name}`, `reviews/` and `ledger/items.yaml`. Do not edit by hand.",
    ]
    if today:
        out.append(f"> As of {today}.")
    ledger = Ledger(root / "ledger" / "items.yaml")
    out += [""] + summary_lines(parse_waves(lines), units, ledger.items)
    placed: set[str] = set()
    out += ["", "## Units by wave"]
    header = ["", "| unit | title | done/total | status | review |", "|---|---|---|---|---|"]
    for name, ids in parse_waves(lines):
        out += ["", f"### {name}"] + header
        for uid in ids:
            if uid in units:
                out.append(_unit_row(uid, units[uid], verdicts))
                placed.add(uid)
    rest = sorted(set(units) - placed, key=lambda s: tuple(int(x) for x in s[1:].split(".")))
    if rest:
        out += ["", "### Unscheduled"] + header
        out += [_unit_row(uid, units[uid], verdicts) for uid in rest]
    out += ["", "## Ledger", ""] + count_table(ledger.items, total_row=False)
    if today:
        overdue = sorted(ledger.report_overdue(today))
        out += ["", f"## Overdue as of {today}", ""]
        out += [f"- {i} (due {ledger.get(i).due}): {ledger.get(i).text}" for i in overdue] or ["none"]
    else:
        out += ["", "## Overdue", "", "not computed (run `plane progress --today YYYY-MM-DD`)"]
    return "\n".join(out) + "\n"
