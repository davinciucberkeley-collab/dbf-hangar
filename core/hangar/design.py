"""Loading design files and the shared result types every check returns."""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml

from . import yamlfast

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schema" / "plane.schema.json"
STANDARDS_PATH = REPO_ROOT / "standards" / "design-standards.yaml"
DESIGNS_DIR_ENV = "PLANE_DESIGNS_DIR"      # U6.1 (T91): the bench grader points this at the run's workspace designs/ folder
DESIGNS_DIR = Path(os.environ[DESIGNS_DIR_ENV]) if os.environ.get(DESIGNS_DIR_ENV) else REPO_ROOT / "designs"

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"


@dataclass
class Design:
    data: dict[str, Any]
    path: Path | None = None
    raw: dict | None = None            # PDL 1.2: the unresolved data ("$name" references, no generated mass_g); None otherwise
    resolve_errors: dict = field(default_factory=dict)   # PDL 1.2: {component id: why its generated geometry/mass failed}

    _mass_pending = False              # True between load_design and the first read of data/resolve_errors (lazy generated mass_g)

    def __getattribute__(self, name):
        if (name == "data" or name == "resolve_errors") and object.__getattribute__(self, "__dict__").get("_mass_pending"):
            from hangar.geom.resolve import fill_generated_mass, fill_swept_poses   # inside: hangar.geom imports hangar.design
            d, errs = self.__dict__["data"], self.__dict__["resolve_errors"]
            fill_swept_poses(d, self.base_dir, errs)
            fill_generated_mass(d, self.base_dir, errs)
            self._mass_pending = False   # only after both fills succeeded
        return object.__getattribute__(self, name)

    def data_without_mass(self) -> dict:
        """The resolved data without forcing the generated-part mass fill (the same dict `data` returns, filled or not)."""
        return self.__dict__["data"]

    @property
    def id(self) -> str:
        return self.data.get("id", "<no id>")

    @property
    def components(self) -> list[dict]:
        return self.data.get("components", [])

    def component(self, cid: str) -> dict:
        for c in self.components:
            if c["id"] == cid:
                return c
        raise KeyError(cid)

    @property
    def base_dir(self) -> Path:
        return self.path.parent if self.path else Path.cwd()


@dataclass
class CheckResult:
    check_id: str          # e.g. "T1.connectivity"
    status: str            # PASS / FAIL / WARN / SKIP
    message: str
    criterion: str = ""    # link into standards/, e.g. "design-standards.yaml#static_margin"
    data: dict = field(default_factory=dict)

    @property
    def not_applicable(self) -> bool:
        """A SKIP row for a check that does not apply to the design's morphology (D77); not a result."""
        return self.status == SKIP and bool(self.data.get("not_applicable"))


@dataclass
class TierReport:
    tier: int
    name: str
    results: list[CheckResult]

    @property
    def status(self) -> str:
        s = [r.status for r in self.results if not r.not_applicable]
        if not s and self.results:
            return SKIP
        if FAIL in s:
            return FAIL
        if not s or SKIP in s:
            return SKIP
        if WARN in s:
            return WARN
        return PASS


@dataclass
class Scorecard:
    design_id: str
    tiers: list[TierReport]
    max_tier: int = 9
    fidelity: dict = field(default_factory=dict)

    @property
    def partial(self) -> bool:
        return self.max_tier < 9

    @property
    def clean(self) -> bool:
        """No FAIL/SKIP among the tiers that ran."""
        return all(r.status not in (FAIL, SKIP) or r.not_applicable for t in self.tiers for r in t.results)

    @property
    def accepted(self) -> bool:
        """Full-run verdict only: a partial run (max_tier < 9) is never accepted."""
        return not self.partial and all(r.status not in (FAIL, SKIP) or r.not_applicable for t in self.tiers for r in t.results)

    def to_dict(self) -> dict:
        d = {
            "design_id": self.design_id,
            "accepted": self.accepted,
            "partial": self.partial,
            "max_tier": self.max_tier,
            "tiers": [
                {"tier": t.tier, "name": t.name, "status": t.status,
                 "results": [asdict(r) for r in t.results]}
                for t in self.tiers
            ],
        }
        if self.fidelity:
            d["fidelity"] = self.fidelity
        return d

    def to_markdown(self, design=None) -> str:
        from .gates import REPORT_ONLY_PREFIX
        from .gates.describe import describe_card, fold
        texts = describe_card(self, design)
        flat = [t for tier in texts for t in tier]
        until = REPORT_ONLY_PREFIX.removeprefix("report-only until ").rstrip(": ")
        F = sum(1 for t in flat if t.status == FAIL)
        W = sum(1 for t in flat if t.status == WARN)
        P = sum(1 for t in flat if t.status == PASS)
        N = sum(1 for t in flat if t.not_applicable)
        S = sum(1 for t in flat if t.status == SKIP and not t.not_applicable)

        def entry_lines(e: dict) -> list[str]:
            rows = e["rows"]
            single = len(rows) == 1
            head = f"- **{e['status']}** **{e['title']}**"
            if single and rows[0].parts:
                head += ": " + ", ".join(p.label for p in rows[0].parts)
            if rows and all(r.report_only for r in rows):
                wb = {r.would_be for r in rows}
                tag = f"report-only until {until}"
                if len(wb) == 1 and next(iter(wb)):
                    tag += f", would be {next(iter(wb))} today"
                head += f" _[{tag}]_"
            lines = [head, f"  {e['sentence']}"]
            if e["hint"]:
                lines.append(f"  Fix: {e['hint']}")
            if single:
                r = rows[0]
                lines.append(f"  Details: {r.details}")
                lines.append(f"  Check: `{r.check_id}`")
            else:
                for r in rows:
                    lines.append(f"  - {', '.join(p.label for p in r.parts) or r.details} (`{r.check_id}`)")
            return lines

        lines = [f"# Scorecard: {self.design_id}", "",
                 (f"**Partial run (tiers 0\u2013{self.max_tier}):** {'no failures' if self.clean else 'failures found'}"
                  if self.partial else f"**Accepted:** {'yes' if self.accepted else 'no'}"), "",
                 f"**Summary:** {F} FAIL, {W} WARN, {S} not checked, {N} not applicable, {P} PASS.", ""]
        sections = [
            ("## Needs fixing", fold([t for t in flat if t.status == FAIL])),
            ("## Warnings", fold([t for t in flat if t.status == WARN])),
            ("## Not checked", fold([t for t in flat if t.status == SKIP and not t.not_applicable])),
        ]
        for heading, entries in sections:
            if entries:
                lines += [heading, ""]
                for e in entries:
                    lines += entry_lines(e)
                lines.append("")
        if N:
            lines += [f"## Not applicable ({N})", ""]
            seen: dict[str, object] = {}
            for t in flat:
                if t.not_applicable:
                    seen.setdefault(t.family, t)
            for t in seen.values():
                lines.append(f"- {t.title}: {t.details}")
            lines.append("")
        if P:
            lines += [f"## Passing ({P} checks)", ""]
            counts: dict[str, list] = {}
            for t in flat:
                if t.status == PASS:
                    counts.setdefault(t.family, [t.title, 0])[1] += 1
            for title, n in counts.values():
                lines.append(f"- {title}: {n} ok")
            lines.append("")
        lines += ["## Full table", "",
                  "| Tier | Status | Check | Result | Criterion |", "|---|---|---|---|---|"]
        for t in self.tiers:
            for r in t.results:
                lines.append(f"| {t.tier} {t.name} | {r.status} | {r.check_id} | {r.status}: {r.message} | {r.criterion} |")
        out = "\n".join(lines) + "\n"
        if self.fidelity:
            f = self.fidelity
            out += (f"\nFidelity: {f['sourced_blocking']} of {f['blocking']} blocking checks use sourced thresholds; "
                    f"{f['measured_mass_parts']} components have measured mass.\n")
        return out


def load_design(path: str | Path) -> Design:
    p = Path(path)
    if p.is_dir():
        p = p / "plane.yaml"
    text = p.read_text()
    data = json.loads(text) if p.suffix == ".json" else yamlfast.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{p}: top level must be a mapping")
    design = Design(data=data, path=p.resolve())
    comps = data.get("components") or []
    if "parameters" in data or any(isinstance(c, dict) and ("mass_model" in c or "generator" in (c.get("geometry") or {}))
                                   for c in comps):
        from hangar.geom.resolve import resolve_design_data   # inside: hangar.geom imports hangar.design
        design.raw = data
        design.data, design.resolve_errors = resolve_design_data(data, design.base_dir, mass=False)
        design._mass_pending = True
    return design


_STANDARDS_CACHE: dict[tuple, dict] = {}


def load_standards() -> dict:
    """design-standards.yaml, parsed once per file version (path + mtime + size); a deep copy every call."""
    st = STANDARDS_PATH.stat()
    key = (str(STANDARDS_PATH), st.st_mtime_ns, st.st_size)
    data = _STANDARDS_CACHE.get(key)
    if data is None:
        _STANDARDS_CACHE.clear()
        data = _STANDARDS_CACHE[key] = yaml.safe_load(STANDARDS_PATH.read_text())
    return copy.deepcopy(data)


def list_designs() -> list[Path]:
    return sorted(DESIGNS_DIR.glob("*/plane.yaml"))
