"""PreToolUse hook: gate Task/Agent subagent launches against the roster, the active plan and the builder-ready bar."""
import json
import os
import re
import sys
from pathlib import Path

GATED_TOOLS = ("Task", "Agent")
BUILDER_ROLES = ("builder", "builder-plus")
# Claude Code built-in subagents (T112). Explore and Plan have read-only tools (Write and Edit denied);
# Bash is not denied for them but stays under the parent session's permission rules and hooks.
# claude-code-guide's tool list is not documented; it is allowed on the same basis (reviewer re-checks).
# A user or project agent file with the same name replaces the built-in, so the allowance applies only
# when no agent file defines the name. Plugin and --agents overrides the hook cannot see are an
# accepted leftover risk (D69).
BUILTIN_READ_ONLY = ("Explore", "Plan", "claude-code-guide")
BRIEF_RE = re.compile(r"""[^\s"'`<>()]*plans/[^/\s"'`<>()]+/briefs/[^/\s"'`<>()]+\.md""")


def brief_exists(prompt, root):
    """True if the prompt names an existing file plans/<plan>/briefs/<name>.md under root.
    Accepts repo-relative or absolute paths, with / or \\ separators."""
    text = prompt.replace("\\", "/")
    plans = (Path(root) / "plans").resolve()
    for match in BRIEF_RE.finditer(text):
        path = Path(match.group(0))
        full = (path if path.is_absolute() else Path(root) / path).resolve()
        try:
            rel = full.relative_to(plans)
        except ValueError:
            continue
        if len(rel.parts) == 3 and rel.parts[1] == "briefs" and full.is_file():
            return True
    return False


def read_agent_text(path):
    """UTF-8 (BOM tolerated), or UTF-16 when a BOM says so. Anything else raises UnicodeDecodeError."""
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def frontmatter_name(path):
    """The name: value, "" if there is none, or None if the file cannot be read or decoded."""
    try:
        lines = read_agent_text(path).splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line[len("name:"):].split("#", 1)[0].strip().strip("\"'").strip()
    return ""


def roster_names(root):
    names = {frontmatter_name(path) for path in (root / ".claude" / "agents").glob("*.md")}
    return sorted(name for name in names if name)


def defined_agent_names(root):
    """(names, unreadable): names defined by agent files (frontmatter name:) under the project and the user's
    .claude/agents/, recursively. unreadable is True if any file could not be read or decoded, or a folder
    could not be listed. Callers fail closed on it: a built-in name may be redefined by a file they cannot see.
    Plugin and --agents overrides are not visible to this hook (accepted leftover risk, D69)."""
    names, unreadable = set(), False
    for base in (Path(root) / ".claude" / "agents", Path.home() / ".claude" / "agents"):
        try:
            if not base.is_dir():
                continue
            for path in base.rglob("*.md"):
                name = frontmatter_name(path)
                if name is None:
                    unreadable = True
                elif name:
                    names.add(name)
        except OSError:
            unreadable = True
    return names, unreadable


def agent_table_roles(plan_text: str) -> set:
    roles = set()
    in_table = False
    for line in plan_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            continue
        if not in_table:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if "Pass criterion" in cells:
                in_table = True
            continue
        if set(stripped) <= set("|-: "):
            continue
        roles.update(re.findall(r"`([^`]+)`", stripped))
    return roles


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
    if role in BUILTIN_READ_ONLY:
        names, unreadable = defined_agent_names(root)
        if role not in names and not unreadable:
            return 0

    roster = roster_names(root)
    if role not in roster:
        return block(
            f'Agent "{role}" is not in the hangar roster. Use one of: {", ".join(roster)}, or a read-only built-in: {", ".join(BUILTIN_READ_ONLY)}. '
            "See .claude/agents/ and the plan's agent table. Builds go to builder (Haiku)."
        )

    plan = active_plan(root)
    if plan is not None:
        text = plan.read_text(encoding="utf-8")
        if role not in agent_table_roles(text):
            rel = plan.relative_to(root).as_posix()
            return block(
                f'Agent "{role}" is not in the active plan\'s agent table ({rel}). Add it to the table first.'
            )

    if role in BUILDER_ROLES:
        prompt = tool_input.get("prompt", "") or ""
        lowered = prompt.lower()
        ready = brief_exists(prompt, root) or ("pass check" in lowered and "stop rule" in lowered)
        if not ready:
            return block(
                f"Brief for {role} is not builder-ready: give a brief file (plans/<plan>/briefs/*.md) "
                "or include exact outputs, exact inputs, a pass check and a stop rule (standards/agents.md)."
            )
    return 0


def main():
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        raw = sys.stdin.buffer.read().decode("utf-8")
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
