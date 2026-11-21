"""DBF-Combined import operations (U2.5b): claim.import-dbf, ledger.import-dbf."""
from __future__ import annotations

from pathlib import Path

from . import op, OpResult, OpInputError
from ..claims.graph import ClaimGraphError
from ..importers.changelog import import_decisions
from ..importers.dbf_claims import import_claims


def _p(s: str) -> str:
    return s.replace("\\", "/")


@op(name="claim.import-dbf", summary="Write claims.yaml for a DBF-Combined concept (claims, parameters, requirements); touches no other file.", mutates=True)
def import_dbf_claims(dbf_root: str, concept: str, out: str) -> OpResult:
    root, out = _p(dbf_root), _p(out)
    if not Path(root).is_dir():
        raise OpInputError(f"no such folder: {root}")
    try:
        path = import_claims(root, concept, out, log=lambda m: None)
    except (FileNotFoundError, ClaimGraphError) as e:
        raise OpInputError(str(e))
    import yaml
    nodes = yaml.safe_load(path.read_text(encoding="utf-8"))["nodes"]
    count = lambda t: sum(1 for n in nodes if n["type"] == t)  # noqa: E731
    return OpResult(ok=True, data={"claims_yaml": str(path).replace("\\", "/"), "nodes": len(nodes),
                                   "parameters": count("parameter"), "claims": count("claim")},
                    changed_files=[str(path).replace("\\", "/")])


@op(name="ledger.import-dbf", summary="Import DBF-Combined's CHANGE-LOG decisions and DECISIONS.md items into a ledger file.", mutates=True)
def import_dbf_decisions(dbf_root: str, ledger: str) -> OpResult:
    root, led = _p(dbf_root), _p(ledger)
    if not Path(root).is_dir():
        raise OpInputError(f"no such folder: {root}")
    try:
        counts = import_decisions(root, led, log=lambda m: None)
    except FileNotFoundError as e:
        raise OpInputError(f"missing file: {e}")
    return OpResult(ok=True, data=counts, changed_files=[led])
