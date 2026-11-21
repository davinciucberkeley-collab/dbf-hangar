"""CI rule (U1.4): no single commit may change both designs/** and core/**.

Exempt: a commit whose message has a line starting `migration:`, or any run given the `migration` label (PR label).
Merge commits are skipped (their parents are checked on their own).

Usage: python harness/ci/check_separation.py --base <ref-or-sha> [--labels a,b]
Exit 0 = ok, 1 = violation. Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

MIGRATION_LABEL = "migration"
ZEROS = "0" * 40


def _git(args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def has_migration_line(message: str) -> bool:
    return re.search(r"^migration:", message, re.M) is not None


def check_separation_files(files, labels=(), message="") -> list[str]:
    files = [str(f).replace("\\", "/") for f in files]
    designs = [f for f in files if f.startswith("designs/")]
    core = [f for f in files if f.startswith("core/")]
    if not designs or not core or MIGRATION_LABEL in set(labels) or has_migration_line(message):
        return []
    return [f"{c}: core/** changed in the same commit as designs/** (add a 'migration:' line to the commit message, "
            f"or the '{MIGRATION_LABEL}' label on the PR, if this is a migration)" for c in core]


def resolve_base(base: str, cwd=None) -> str | None:
    """The commit to compare from, or None (with a printed note) when there is nothing to check."""
    if base != ZEROS and _git(["cat-file", "-e", f"{base}^{{commit}}"], cwd).returncode == 0:
        return base
    p = _git(["merge-base", "origin/main", "HEAD"], cwd)
    mb = p.stdout.strip()
    head = _git(["rev-parse", "HEAD"], cwd).stdout.strip()
    if p.returncode != 0 or not mb or mb == head:
        print("check_separation: first push and no origin/main to compare with; nothing checked")
        return None
    return mb


def check_separation(base: str, labels=(), cwd=None, head: str = "HEAD") -> list[str]:
    """Violations among the non-merge commits in base..head, one per offending core file."""
    base = resolve_base(base, cwd)
    if base is None:
        return []
    log = _git(["log", "--no-merges", "--format=%H", f"{base}..{head}"], cwd)
    if log.returncode != 0:
        raise RuntimeError(f"git log failed: {log.stderr.strip()}")
    out: list[str] = []
    for sha in log.stdout.split():
        files = _git(["diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha], cwd).stdout.splitlines()
        msg = _git(["show", "-s", "--format=%B", sha], cwd).stdout
        out += [f"{sha[:7]} {v}" for v in check_separation_files(files, labels, msg)]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--labels", default="")
    a = ap.parse_args(argv)
    labels = [x.strip() for x in a.labels.split(",") if x.strip()]
    violations = check_separation(a.base, labels)
    for v in violations:
        print(v)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
