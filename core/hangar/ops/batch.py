"""U13.3: design.apply, a batch of plane.yaml edits with one regeneration pass."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import op, OpResult, OpInputError
from . import edit
from .. import pdledit, yamlfast

_VERBS = ("set", "add", "append", "remove")


def _parse_edits(edits: Path) -> list[tuple[str, str, object]]:
    edits = Path(edits)
    if not edits.is_file():
        raise OpInputError(f"no such file: {edits}")
    raw = yaml.safe_load(edits.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise OpInputError("edit file must be a YAML list of mappings")
    out = []
    for n, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            raise OpInputError(f"edit {n}: must be a mapping")
        verbs = [k for k in item if k in _VERBS]
        extra = [k for k in item if k not in _VERBS and k != "value"]
        if extra:
            raise OpInputError(f"edit {n}: unknown key {extra[0]!r}; use one of set, add, append, remove (plus value)")
        if len(verbs) != 1:
            raise OpInputError(f"edit {n}: exactly one of set, add, append, remove is needed")
        verb = verbs[0]
        key = item[verb]
        if not isinstance(key, str) or not key.strip():
            raise OpInputError(f"edit {n}: {verb} needs a key")
        if verb == "remove":
            if "value" in item:
                raise OpInputError(f"edit {n}: remove takes no value")
            out.append((verb, key, None))
        else:
            if "value" not in item:
                raise OpInputError(f"edit {n}: {verb} needs a value")
            out.append((verb, key, item["value"]))
    return out


@op(name="design.apply", summary="Apply many edits from a YAML file (set / add / append / remove) in one atomic step: one schema check, one regeneration and one interference pass for the whole batch, one compact CHANGELOG entry.",
    mutates=True, render=lambda r: "\n".join(r.messages))
def apply_op(path: str, *, edits: Path, why: str) -> OpResult:
    plane = edit._plane(path)
    text = edit._text(plane)
    if not why.strip():
        raise OpInputError("why must not be empty")
    todo = _parse_edits(edits)
    before = yamlfast.safe_load(text)
    working = text
    counts = {"set": 0, "add": 0, "append": 0, "remove": 0}
    unchanged = 0
    keys = []
    for n, (verb, key, value) in enumerate(todo, 1):
        try:
            if verb == "set":
                data = yamlfast.safe_load(working)
                old = pdledit.get_value(data, key)      # raises the "no key" error
                if isinstance(value, dict):
                    raise OpInputError("set takes a scalar or a list; use add or append")
                if isinstance(value, list):
                    if not isinstance(old, list):
                        raise OpInputError(f"{key} is not a list")
                    if old == value:
                        unchanged += 1
                        continue
                    working = pdledit.replace_list(working, key, value)[0]
                elif old == value and type(old) is type(value):
                    unchanged += 1
                    continue
                else:
                    working = pdledit.patch_text(working, key, value)
            elif verb == "add":
                if pdledit.exists(yamlfast.safe_load(working), key):
                    raise OpInputError(f"{key} is already set")
                if isinstance(value, (list, dict)) and not value:
                    raise OpInputError(f"{key}: a list or mapping value must not be empty")
                working = pdledit.add_value(working, key, value)
            elif verb == "append":
                if isinstance(value, dict):
                    working, _, _ = pdledit.append_element(working, key, value)
                else:
                    working, _, _ = pdledit.append_item(working, key, value)
            else:
                working, _ = pdledit.remove_element(working, key)
        except OpInputError as e:
            raise OpInputError(f"edit {n}: {e}") from e
        counts[verb] += 1
        keys.append(key)
    if working == text:
        return OpResult(True, {"count": 0, "unchanged": unchanged, "verbs": counts}, ["no changes"])
    from ..geom.params import expression_errors
    after = yamlfast.safe_load(working)
    fresh = [e for e in expression_errors(after) if e not in set(expression_errors(before))]
    if fresh:
        raise OpInputError("; ".join(f"{o}: {p}: {m}" for o, p, m in fresh))
    pdledit.check_schema(before, after, "batch")
    from ..geom.resolve import regeneration_report
    regen = regeneration_report(text, working, plane)
    n = sum(counts.values())
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {"date": stamp, "kind": "batch", "key": "batch", "old": None, "new": None, "why": why,
             "count": n, "keys": keys, "file": Path(edits).name}
    log = edit._write_with_log(plane, text, working, [entry])
    msgs = [f"applied {n} edits ({counts['set']} set, {counts['add']} add, {counts['append']} append, "
            f"{counts['remove']} remove; {unchanged} unchanged)"]
    out = {"count": n, "unchanged": unchanged, "verbs": counts}
    if regen is not None and regen["components"]:
        (m0, m1), (c0, c1) = regen["mass_g"], regen["cg_mm"]
        fmt_cg = lambda c: " ".join(f"{x:.2f}" for x in c) if c else "n/a"
        msgs.append(f"regenerated {', '.join(sorted(regen['components']))}: mass "
                    f"{'n/a' if m0 is None else f'{m0:.1f}'} -> {'n/a' if m1 is None else f'{m1:.1f}'} g, "
                    f"CG {fmt_cg(c0)} -> {fmt_cg(c1)} mm")
        out["regenerated"] = regen
    inter = regen["interference"] if regen is not None else None
    if inter and (inter["moved"] or inter["joints"]):
        msgs.append(f"moved {len(inter['moved'])} part(s), {len(inter['joints'])} joint(s); interference: "
                    f"{len(inter['new'])} new, {len(inter['cleared'])} cleared")
        msgs += [f"new interference: {r['message']}" for r in inter["new"]]
        msgs += [f"cleared: {r['message']}" for r in inter["cleared"]]
        out["interference"] = inter
    if regen is not None and regen["failing"]:
        msgs += [f"still failing (not caused by this edit): {cid}: {m}" for cid, m in sorted(regen["failing"].items())]
        out["still_failing"] = regen["failing"]
    return OpResult(True, out, msgs, changed_files=[str(plane), str(log)])
