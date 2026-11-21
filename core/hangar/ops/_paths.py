"""Where team files live: the repo root is the first folder at or above the cwd that has pyproject.toml."""
from __future__ import annotations
from pathlib import Path


def repo_root() -> Path:
    cwd = Path.cwd()
    for folder in [cwd, *cwd.parents]:
        if (folder / "pyproject.toml").exists():
            return folder
    return cwd


def rel(root: Path, p: Path) -> str:
    return Path(p).relative_to(root).as_posix()
