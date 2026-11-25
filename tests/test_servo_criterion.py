"""U13.7-3: T6.servo_undriven cites a pending criterion for "every servo drives a mechanism" (T140)."""
import copy
from pathlib import Path

from hangar.checks import validate
from hangar.design import Design, load_design
from hangar.gates.fidelity import resolve_threshold

FIX = Path(__file__).parent / "fixtures" / "mechanism-recipe"
BASE = load_design(FIX / "plane.yaml").data
PFX = "T6.servo_undriven"
SERVO_CRIT = "gate-thresholds.yaml#servo_must_drive_mechanism"


def results(data):
    d = Design(data=copy.deepcopy(data), path=FIX / "plane.yaml")
    card = validate(d)
    return [r for t in card.tiers for r in t.results]


def _no_mech():
    data = copy.deepcopy(BASE)
    del data["mechanisms"]
    return data


def test_entry_is_pending_with_a_rule():
    e = resolve_threshold("gate-thresholds.yaml#servo_must_drive_mechanism")
    assert e["source"] == "pending"
    assert e["value"] is True
    assert e["rule"]


def test_servo_row_cites_the_new_criterion():
    rs = {r.check_id: r for r in results(_no_mech())}
    assert rs[f"{PFX}.servo"].criterion == SERVO_CRIT


def test_other_t6_rows_keep_their_criterion():
    rs = {r.check_id: r for r in results(BASE)}
    assert rs["T6.mechanism.elevator-drive"].criterion == "gate-thresholds.yaml#mechanism_ratio_tol"
