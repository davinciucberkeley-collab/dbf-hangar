"""Load the agent roster from `.claude/agents/*.md` frontmatter."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

MODELS = ("opus", "sonnet", "haiku")
REQUIRED = ("name", "model", "tools", "description")


@dataclass(frozen=True)
class AgentSpec:
    name: str
    model: Literal["opus", "sonnet", "haiku"]
    tools: tuple[str, ...]
    description: str


def _frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: missing opening '---' frontmatter line")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError(f"{path}: missing closing '---' frontmatter line") from None
    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: invalid frontmatter YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: frontmatter is not a mapping")
    return data


def load_roster(root: Path) -> dict[str, AgentSpec]:
    """Return {name: AgentSpec} for every `root/.claude/agents/*.md`."""
    roster: dict[str, AgentSpec] = {}
    for path in sorted((Path(root) / ".claude" / "agents").glob("*.md")):
        data = _frontmatter(path)
        missing = [k for k in REQUIRED if k not in data]
        if missing:
            raise ValueError(f"{path}: missing field(s) {', '.join(missing)}")
        model = str(data["model"]).strip()
        if model not in MODELS:
            raise ValueError(f"{path}: model {model!r} must be one of {', '.join(MODELS)}")
        tools = tuple(t.strip() for t in str(data["tools"]).split(",") if t.strip())
        spec = AgentSpec(
            name=str(data["name"]).strip(),
            model=model,  # type: ignore[arg-type]
            tools=tools,
            description=str(data["description"]).strip(),
        )
        roster[spec.name] = spec
    return roster
