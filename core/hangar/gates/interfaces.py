"""Connection-type library and the T1 connection check (U1.6)."""
from __future__ import annotations
from functools import lru_cache
import yaml
from ..design import FAIL, PASS, REPO_ROOT, CheckResult, Design

LIBRARY_PATH = REPO_ROOT / "standards" / "connection-types.yaml"
CRITERION = "connection-types.yaml"

@lru_cache(maxsize=1)
def _load() -> tuple:
    doc = yaml.safe_load(LIBRARY_PATH.read_bytes().decode("utf-8"))
    return tuple(doc["connection_types"])

def load_connection_types() -> dict[str, dict]:
    """Library entries by id, in file order (each a fresh copy)."""
    return {t["id"]: dict(t) for t in _load()}

def connection_known_results(design: Design) -> list[CheckResult]:
    """[] when no attachment names a connection; else one T1.interfaces.connection_known row."""
    named = [a for a in design.data.get("attachments", []) if "connection" in a]
    if not named:
        return []
    lib = load_connection_types()
    bad = []
    for a in named:
        label = a.get("id") or f"{a['parent']}->{a['child']}"
        if a["connection"] not in lib:
            bad.append((label, a["connection"]))
    if bad:
        return [CheckResult("T1.interfaces.connection_known", FAIL,
                            "connection type not in standards/connection-types.yaml: "
                            + ", ".join(f"{c} ({label})" for label, c in bad),
                            CRITERION, {"joint": [label for label, _ in bad]})]
    return [CheckResult("T1.interfaces.connection_known", PASS,
                        f"all {len(named)} named connections are in the library", CRITERION)]
