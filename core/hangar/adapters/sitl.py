"""ArduPilot SITL adapter: planned stub."""
from __future__ import annotations

from ..ops import OpResult
from . import skip_result

_TEXT = "planned, not implemented in v1.0 (ArduPilot SITL flight-case plant, report-only)"


class Sitl:
    name = "sitl"
    planned = True

    def available(self) -> tuple[bool, str]:
        return False, _TEXT

    def run(self, design, **params) -> OpResult:
        return skip_result("sitl", _TEXT, "run")
