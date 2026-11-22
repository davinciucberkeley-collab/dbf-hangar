"""Docs operations: generate docs/cli.md."""
from __future__ import annotations

from pathlib import Path

from . import OpResult, op
from ..clidoc import write_cli_reference


@op(name="docs.cli", summary="Write the command reference (markdown) generated from the ops registry", mutates=True)
def docs_cli(*, out: Path) -> OpResult:
    p = write_cli_reference(out)
    return OpResult(ok=True, data={"path": str(p), "bytes": p.stat().st_size}, changed_files=[str(p)])
