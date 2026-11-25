"""Plain helpers shared by the validator tests. Not a conftest, so importing it never collides with tests/harness/conftest.py."""
from hangar.design import DESIGNS_DIR, Scorecard

EXAMPLE_PATH = DESIGNS_DIR / "example-tailsitter-wing" / "plane.yaml"


def statuses(scorecard: Scorecard, check_id: str) -> list[str]:
    """Statuses of every result with this check_id, across all tiers."""
    return [r.status for t in scorecard.tiers for r in t.results if r.check_id == check_id]

# PDL 1.0 designs that predate generators; new designs are not listed on purpose
LEGACY_DESIGNS = ("c0-a1", "c0-a2", "c0-a3", "c0-lift-cruise", "concept-a", "example-tailsitter-wing", "tiltwing-cakir")
