"""DaVinci adapter: D3 decided as SKIP-with-reason; real calls come after Dec 1. No network code."""
from __future__ import annotations

from ..ops import OpResult
from . import skip_result

_TEXT = "D3 open: no API access configured; fix: answer D3 (plans/2026-11-20-standardization.md), then configure access"


class DaVinci:
    name = "davinci"
    planned = False

    def available(self) -> tuple[bool, str]:
        return False, _TEXT

    def push(self, design, **params) -> OpResult:
        return skip_result("davinci", _TEXT, "push")

    def pull(self, **params) -> OpResult:
        return skip_result("davinci", _TEXT, "pull")

    def run(self, design, **params) -> OpResult:
        return skip_result("davinci", _TEXT, "run")
