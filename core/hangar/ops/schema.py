"""PDL operations: generate the reference doc, migrate a design file to the latest version."""
from __future__ import annotations

from pathlib import Path

import yaml

from . import OpInputError, OpResult, op
from ..checks import tier0_schema
from ..design import Design
from ..migrate import LATEST, bump_version_text, migrate
from ..pdlref import write_reference


@op(name="schema.docs", summary="Write the PDL reference (markdown) generated from schema/plane.schema.json",
    mutates=True)
def schema_docs(*, out: Path) -> OpResult:
    p = write_reference(out)
    return OpResult(ok=True, data={"path": str(p), "bytes": p.stat().st_size}, changed_files=[str(p)])


@op(name="design.migrate", summary="Migrate a design file to the latest PDL version (dry run unless write is true)",
    mutates=True)
def design_migrate(path: str, *, write: bool = False) -> OpResult:
    try:
        p = Path(path.replace("\\", "/"))
        if p.is_dir():
            p = p / "plane.yaml"
        if p.suffix == ".json":
            raise ValueError("JSON designs are not migrated")
        if not p.is_file():
            raise FileNotFoundError(f"no such file: {p}")
        raw = p.read_bytes().decode("utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError("not a mapping")
        old = data.get("schema_version")
        new, notes = migrate(data)
        already = old == LATEST
        if not already:
            bump_version_text(raw)   # raises ValueError when the version line cannot be patched
    except (OSError, ValueError, yaml.YAMLError, UnicodeDecodeError) as e:
        raise OpInputError(f"cannot load {path}: {e}")
    info = {"path": str(p), "from_version": old, "to_version": LATEST, "notes": notes, "written": False}
    if already:
        return OpResult(ok=True, data=info, messages=notes)
    rep = tier0_schema(Design(new, p))
    if rep.status != "PASS":
        return OpResult(ok=False, data=info,
                        messages=[f"{r.check_id}: {r.message}" for r in rep.results if r.status != "PASS"])
    if not write:
        return OpResult(ok=True, data=info, messages=notes)
    p.write_bytes(bump_version_text(raw).encode("utf-8"))
    info["written"] = True
    return OpResult(ok=True, data=info, messages=notes, changed_files=[str(p)])
