"""SessionStart hook: re-inject hangar context. Never raises."""
import json
import sys
from pathlib import Path


def _unfinished_units(plan_path):
    sections = []  # [heading, has_unchecked]
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## ") or line.startswith("### "):
            sections.append([line, False])
        elif sections and "- [ ]" in line:
            sections[-1][1] = True
    return [h[len("### "):] for h, open_ in sections if open_ and h.startswith("### Unit")]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import ledger

    event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    root = ledger.project_root(event)
    plans = sorted((Path(root) / "plans").glob("*.md"), key=lambda p: p.name)
    plan_rel = plans[-1].relative_to(root).as_posix() if plans else "none"

    out = [f"hangar: roles in .claude/agents/ (launch only these); plan: {plan_rel}"]
    if event.get("source") in ("compact", "resume"):
        open_items = ledger.open_prompts(root)
        if open_items:
            out.append("Open prompts:")
            for p in open_items:
                out.append(ledger.format_line(p))
        else:
            out.append("Open prompts: none")
        out.append("Unfinished units:")
        if plans:
            out += _unfinished_units(plans[-1])
    else:
        out.append(f"Open prompts: {len(ledger.open_prompts(root))}")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as e:
        print(f"reinject: {e!r}", file=sys.stderr)
        code = 0
    sys.exit(code)
