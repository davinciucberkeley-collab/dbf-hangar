"""Gate T9: recompute every claim of a design and report PASS / FAIL / SKIP / WARN rows."""
from __future__ import annotations

from ..claims.calc import load_claims_standards
from ..claims.graph import ClaimGraphError, claims_path, load_claims
from ..design import FAIL, PASS, SKIP, WARN, CheckResult, Design, TierReport

CRIT = "claims.yaml#recompute_rel_tol"
_MAP = {"PASS": PASS, "FAIL": FAIL, "PROPOSED": SKIP, "STALE": WARN}


def tier9_claims(design: Design) -> TierReport | None:
    if claims_path(design) is None:
        return None
    try:
        graph = load_claims(design)
        res = graph.recompute(load_claims_standards()["recompute_rel_tol"]["value"])
    except ClaimGraphError as e:
        return TierReport(9, "claims", [CheckResult("T9.claims.load", FAIL, str(e), CRIT)])
    rows = [CheckResult(f"T9.claim.{r.id}", _MAP[r.status], r.message or "", CRIT,
                        data={"claim": r.id, "value": r.value, "limit": r.limit, "margin": r.margin,
                              "margin_abs": r.margin_abs, "claim_status": r.status, "read": r.read})
            for r in res]
    return TierReport(9, "claims", rows)
