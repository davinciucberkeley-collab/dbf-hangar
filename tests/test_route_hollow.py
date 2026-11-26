"""D121: T7 wire routing tests the closed outer volume of a hollow fuselage_loft."""
import copy
from pathlib import Path

from hangar.checks import validate
from hangar.design import Design, load_design

FIX = Path(__file__).parent / "fixtures" / "wires"
STATIONS = [[-50, 100, 50], [100, 120, 60], [250, 100, 50]]


def rows(wall, waypoints=None):
    data = copy.deepcopy(load_design(FIX).data)
    body = next(c for c in data["components"] if c["id"] == "body")
    body["geometry"] = {"generator": "fuselage_loft",
                        "params": {"stations": STATIONS, "shape": "rect", "wall": wall}}
    body["position"] = [0, 0, 0]
    if waypoints:
        data["wiring"]["harnesses"][0]["waypoints"] = waypoints
    d = Design(data=data, path=FIX / "plane.yaml")
    return {r.check_id: r for t in validate(d).tiers for r in t.results}


def test_cavity_route_passes_with_wall():
    assert rows(3.0)["T7.wiring.w1"].status == "PASS"


def test_cavity_route_passes_without_wall():
    assert rows(0.0)["T7.wiring.w1"].status == "PASS"


def test_leaving_the_outer_skin_still_fails():
    r = rows(3.0, [[46.07, -6, 0], [46.07, 500, 0]])["T7.wiring.w1"]
    assert r.status in ("FAIL", "WARN") and "leaves the envelopes" in r.message
