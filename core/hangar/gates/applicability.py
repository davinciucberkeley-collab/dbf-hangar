"""Check applicability from morphology (D77): standards/applicability.yaml names the morphology each check needs."""
from __future__ import annotations

from typing import Callable

import yaml

from ..design import REPO_ROOT, SKIP, CheckResult
from . import _text

PATH = REPO_ROOT / "standards" / "applicability.yaml"


def _vtol(m: dict) -> str:
    return m.get("vtol_method", "none")


NEEDS: dict[str, Callable[[dict], bool]] = {
    "hovers": lambda m: _vtol(m) != "none" or m["lift"] == "multirotor",
    "transitions": lambda m: _vtol(m) != "none",
    "winged": lambda m: m["lift"] != "multirotor",
    "conventional": lambda m: m["lift"] != "multirotor" and _vtol(m) == "none",
}


def load_table() -> dict[str, dict]:
    return yaml.safe_load(_text(PATH))["checks"]


def applicable(design, check_id: str) -> tuple[bool, str]:
    row = load_table().get(check_id)
    if row is None:
        return True, ""
    need = row["needs"]
    if need not in NEEDS:
        raise ValueError(f"{check_id}: unknown needs {need!r} in applicability.yaml")
    m = design.data["morphology"]
    return NEEDS[need](m), (f"not applicable: {row['why']} "
                            f"(morphology lift={m['lift']}, vtol_method={_vtol(m)})")


def skip_row(check_id: str, reason: str, criterion: str) -> CheckResult:
    return CheckResult(check_id, SKIP, reason, criterion, {"not_applicable": True})
