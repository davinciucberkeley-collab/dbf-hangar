"""D19: every rule key in standards/*.yaml is read by a gate or named by a skill (no orphan thresholds)."""
from __future__ import annotations

import re

import yaml

from hangar.design import REPO_ROOT

STANDARDS = REPO_ROOT / "standards"
RULE_FILES = sorted(p.name for p in STANDARDS.glob("*.yaml") if p.name != "gates.yaml")
SKIP_TOP = {"connection-types.yaml": {"connection_types", "version"}}

# owner: conductor; wire to a gate or delete (U4.1 step 3)
KNOWN_UNREFERENCED = {
    "program.yaml": ["mass_cap_kg", "transport_pieces_max", "physics_pass", "cad_real_parts",
                     "exposed_wiring_minimised"],
}


def _walk(node, out: list[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, dict) and "source" in v:
                out.append(str(k))
            _walk(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out)


def _keys(fname: str) -> list[str]:
    data = yaml.safe_load((STANDARDS / fname).read_text(encoding="utf-8")) or {}
    if isinstance(data, dict):
        data = {k: v for k, v in data.items() if k not in SKIP_TOP.get(fname, ())}
    out: list[str] = []
    _walk(data, out)
    return out


def _corpus() -> str:
    paths = [*sorted((REPO_ROOT / "core" / "hangar").rglob("*.py")), *sorted((REPO_ROOT / "skills").glob("*/SKILL.md")),
             STANDARDS / "gates.yaml"]
    return "\n".join(p.read_text(encoding="utf-8") for p in paths)


def _referenced(key: str, text: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(key)}(?![A-Za-z0-9_])", text) is not None


def test_every_standards_key_is_referenced():
    text = _corpus()
    missing = [f"{f}#{k}" for f in RULE_FILES for k in _keys(f)
               if k not in KNOWN_UNREFERENCED.get(f, []) and not _referenced(k, text)]
    assert not missing, "standards keys no gate reads and no skill names: " + ", ".join(missing)


def test_known_unreferenced_list_is_exact():
    text = _corpus()
    for f, keys in KNOWN_UNREFERENCED.items():
        present = _keys(f)
        for k in keys:
            assert k in present, f"{f}#{k} is in KNOWN_UNREFERENCED but not in the file"
            assert not _referenced(k, text), f"{f}#{k} is now referenced: remove it from KNOWN_UNREFERENCED"
