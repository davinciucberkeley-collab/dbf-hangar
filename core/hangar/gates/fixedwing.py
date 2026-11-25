"""U12.1-2: fixed-wing checks (wing loading, cruise/stall ratio) for conventional designs; thresholds in standards/fixed-wing.yaml."""
from __future__ import annotations

from ..design import FAIL, PASS, SKIP, WARN, CheckResult
from . import discipline_check
from .applicability import NEEDS, skip_row
from .fidelity import resolve_threshold

FW = "fixed-wing.yaml"


def _crit(key: str) -> tuple[float, bool]:
    t = resolve_threshold(f"{FW}#{key}")
    return t["value"], t["source"] == "pending"


def _stall_row(rep) -> CheckResult | None:
    return next((r for r in (rep.results if rep else []) if r.check_id == "T3.stall"), None)


def _na(ctx, cid: str, what: str, crit: str) -> CheckResult | None:
    m = ctx.design.data["morphology"]
    if NEEDS["conventional"](m):
        return None
    return skip_row(cid, f"not applicable: {what} is for conventional fixed-wing designs "
                         f"(morphology lift={m['lift']}, vtol_method={m.get('vtol_method', 'none')})", crit)


@discipline_check("T3.wing_loading", 3)
def wing_loading(ctx, rep) -> list[CheckResult]:
    cid, crit = "T3.wing_loading", f"{FW}#wing_loading_max_g_dm2"
    na = _na(ctx, cid, "wing loading limit", crit)
    if na:
        return [na]
    row = _stall_row(rep)
    if row is None or "wing_loading_g_dm2" not in row.data:
        return [CheckResult(cid, SKIP, "T3.stall not available", crit)]
    limit, pending = _crit("wing_loading_max_g_dm2")
    wl = row.data["wing_loading_g_dm2"]
    if wl <= limit:
        return [CheckResult(cid, PASS, f"wing loading {wl} g/dm^2 within {limit}", crit,
                            {"wing_loading_g_dm2": wl, "band": "within"})]
    msg = f"wing loading {wl} g/dm^2 above {limit}"
    if pending:
        return [CheckResult(cid, WARN, msg + f"; provisional: {crit} pending", crit,
                            {"wing_loading_g_dm2": wl, "band": "above"})]
    return [CheckResult(cid, FAIL, msg, crit, {"wing_loading_g_dm2": wl, "band": "above"})]


@discipline_check("T3.cruise_stall_ratio", 3)
def cruise_stall_ratio(ctx, rep) -> list[CheckResult]:
    cid, crit = "T3.cruise_stall_ratio", f"{FW}#cruise_to_stall_ratio_min"
    na = _na(ctx, cid, "cruise/stall ratio", crit)
    if na:
        return [na]
    cruise = ctx.design.data.get("requirements", {}).get("cruise_speed_mps")
    if cruise is None:
        return [CheckResult(cid, SKIP, "requirements.cruise_speed_mps missing", crit)]
    row = _stall_row(rep)
    if row is None or not row.data.get("stall_mps"):
        return [CheckResult(cid, SKIP, "T3.stall not available", crit)]
    lo, pending = _crit("cruise_to_stall_ratio_min")
    r = cruise / row.data["stall_mps"]
    msg = f"cruise {cruise} m/s / stall {row.data['stall_mps']} m/s = {r:.2f} vs min {lo}"
    if r >= lo:
        st = PASS
    else:
        st = WARN if pending else FAIL
        if pending:
            msg += f"; provisional: {crit} pending"
    return [CheckResult(cid, st, msg, crit, {"ratio": round(r, 3)})]
