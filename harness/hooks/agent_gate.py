"""PreToolUse hook: gate Task/Agent subagent launches against the roster, the active plan and the builder-ready bar."""
import json
import os
import re
import sys
from pathlib import Path

GATED_TOOLS = ("Task", "Agent")
BUILDER_ROLES = ("builder", "builder-plus")
BRIEF_RE = re.compile(r"plans/\S+/briefs/\S+\.md")


def roster_names(root):
    names = set()
    for path in (root / ".claude" / "agents").glob("*.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != "---":
            continue
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if line.startswith("name:"):
                value = line[len("name:"):].strip().strip("\"'")
                if value:
                    names.add(value)
                break
    return sorted(names)


def active_plan(root):
    plans = sorted((root / "plans").glob("*.md"), key=lambda p: p.name)
    return plans[-1] if plans else None


def block(message):
    sys.stderr.write(message + "\n")
    return 2


def run(event, root):
    if event.get("tool_name") not in GATED_TOOLS:
        return 0
    tool_input = event.get("tool_input") or {}
    role = tool_input.get("subagent_type") or ""

    roster = roster_names(root)
    if role not in roster:
        return block(
            f'Agent "{role}" is not in the hangar roster. Use one of: {", ".join(roster)}. '
            "See .claude/agents/ and the plan's agent table. Builds go to builder (Haiku)."
        )

    plan = active_plan(root)
    if plan is not None:
        text = plan.read_text(encoding="utf-8")
        if f"`{role}`" not in text:
            rel = plan.relative_to(root).as_posix()
            return block(
                f'Agent "{role}" is not in the active plan\'s agent table ({rel}). Add it to the table first.'
            )

    if role in BUILDER_ROLES:
        prompt = tool_input.get("prompt", "") or ""
        lowered = prompt.lower()
        ready = bool(BRIEF_RE.search(prompt)) or ("pass check" in lowered and "stop rule" in lowered)
        if not ready:
            return block(
                f"Brief for {role} is not builder-ready: give a brief file (plans/<plan>/briefs/*.md) "
                "or include exact outputs, exact inputs, a pass check and a stop rule (standards/agents.md)."
            )
    return 0


def main():
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
        env_root = os.environ.get("CLAUDE_PROJECT_DIR")
        if env_root:
            root = Path(env_root)
        elif isinstance(event, dict) and event.get("cwd"):
            root = Path(event["cwd"])
        else:
            root = Path(__file__).resolve().parents[2]
        return run(event, root)
    except Exception as exc:  # never block on unexpected failure
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
