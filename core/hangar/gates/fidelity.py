"""Fidelity line: how many blocking checks rest on a sourced threshold."""
from __future__ import annotations

import yaml

from ..design import REPO_ROOT, Design, TierReport

STANDARDS_DIR = REPO_ROOT / "standards"
_UNSOURCED = ("pending", "internal convention")


CRITERION_ALIASES = {   # U17.1 2b: criteria that name a definition, not a standards key, resolve to a pending key
    "requirements.mtow_g": "gate-thresholds.yaml#mtow_declared_in_design",
    "connection-types.yaml": "gate-thresholds.yaml#connection_named_in_library",
}


CRITERION_ALIASES = {   # U17.1 2b: criteria that name a definition, not a standards key, resolve to a pending key
    "schema/plane.schema.json": "gate-thresholds.yaml#schema_valid",
    "requirements.mtow_g": "gate-thresholds.yaml#mtow_declared_in_design",
    "connection-types.yaml": "gate-thresholds.yaml#connection_named_in_library",
}


def resolve_threshold(criterion: str) -> dict | None:
    """`file#key` -> {"file", "key", "value", "rule", "source"} from standards/<file> (a yaml), else None.
    The key is an entry (a dict with `source`) at the top level or one level inside a top-level group, or a machine
    `id` in the top-level `machines` list. A name in CRITERION_ALIASES resolves as its target."""
    criterion = CRITERION_ALIASES.get(criterion, criterion)
    if "#" not in criterion:
        return None
    fname, key = criterion.split("#", 1)
    path = STANDARDS_DIR / fname
    if path.suffix not in (".yaml", ".yml") or not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    entry = data.get(key)
    if not (isinstance(entry, dict) and "source" in entry):
        entry = None
        for grp in data.values():
            if isinstance(grp, dict) and isinstance(grp.get(key), dict) and "source" in grp[key]:
                entry = grp[key]
                break
    if entry is None:
        m = next((m for m in data.get("machines", []) if isinstance(m, dict) and m.get("id") == key and "source" in m), None)
        if m is None:
            return None
        return {"file": fname, "key": key, "value": m.get("build_volume_mm"), "rule": m.get("notes"), "source": m["source"]}
    return {"file": fname, "key": key, "value": entry.get("value"), "rule": entry.get("rule"),
            "source": entry["source"]}


def compute_fidelity(design: Design, tiers: list[TierReport]) -> dict:
    from . import load_discipline_table, load_gate_table
    blocking_tiers = {g["tier"] for g in load_gate_table() if g["blocking"]}
    nb = {d["id"] for d in load_discipline_table() if not d["blocking"]}
    blocking = sourced = 0
    cache: dict[str, bool] = {}
    for t in tiers:
        if t.tier not in blocking_tiers:
            continue
        for r in t.results:
            if r.check_id.endswith((".error", ".blocked")) or r.check_id in nb:
                continue
            blocking += 1
            if r.criterion not in cache:
                th = resolve_threshold(r.criterion)
                cache[r.criterion] = bool(th) and str(th["source"]).strip().lower() not in _UNSOURCED
            sourced += cache[r.criterion]
    measured = sum(1 for c in design.components if (c.get("provenance") or {}).get("mass_source") == "measured")
    return {"sourced_blocking": sourced, "blocking": blocking, "measured_mass_parts": measured}
