"""PDL version migration. Old files stay valid; migrating only bumps schema_version."""
from __future__ import annotations

import copy
import re

KNOWN_VERSIONS = ("0.1", "0.2", "0.3", "0.4", "1.0")
LATEST = "1.0"

_VERSION_LINE = re.compile(r'^(schema_version:[ \t]*)(["\']?)(0\.[1-4])\2([ \t]*(?:#[^\r\n]*)?)(\r?)$', re.M)


def migrate(data: dict) -> tuple[dict, list[str]]:
    """Return (migrated copy, notes). Never mutates `data`."""
    out = copy.deepcopy(data)
    v = out.get("schema_version") if isinstance(out, dict) else None
    if v not in KNOWN_VERSIONS:
        raise ValueError(f"unsupported schema_version {v!r}; known: 0.1, 0.2, 0.3, 0.4, 1.0")
    if v == LATEST:
        return out, ["already 1.0"]
    out["schema_version"] = LATEST
    return out, [f"schema_version {v} -> 1.0",
                 "no fields added, removed or renamed (all 1.0 blocks are optional)"]


def bump_version_text(text: str) -> str:
    """Replace the one top-level schema_version line with "1.0", leaving every other byte alone."""
    matches = _VERSION_LINE.findall(text)
    if not matches:
        if re.search(r'^schema_version:[ \t]*["\']?1\.0["\']?[ \t]*(?:#[^\r\n]*)?\r?$', text, re.M):
            raise ValueError("already at schema_version 1.0")
        raise ValueError("no top-level schema_version line with a 0.1-0.4 value found")
    if len(matches) > 1:
        raise ValueError("more than one top-level schema_version line found")
    return _VERSION_LINE.sub(r'\1"1.0"\4\5', text)
