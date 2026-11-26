from pathlib import Path
import copy, shutil, pytest
from hangar import yamlfast
from hangar.design import load_design
from hangar.checks import validate
from hangar.geom.resolve import resolve_design_data

FIX = Path(__file__).parent / "fixtures" / "derived-hinge"
ROOT = Path(__file__).parent.parent


def raw_fix():
    return yamlfast.safe_load((FIX / "plane.yaml").read_text(encoding="utf-8"))


def with_hinges(span):
    raw = raw_fix()
    raw["parameters"]["span_mm"] = span
    for a in raw["attachments"]:
        a["hinge_from"] = "generator"
    return resolve_design_data(raw, FIX)


def att(data, i):
    return next(a for a in data["attachments"] if a["id"] == i)


def test_stored_values_are_replaced():
    data, errors = with_hinges(1000)
    r, l = att(data, "hinge-r"), att(data, "hinge-l")
    assert r["location"] == pytest.approx([257.24, 275, 16.343], abs=0.05)
    assert r["articulation"]["pivot"] == pytest.approx([257.24, 275, 16.343], abs=0.05)
    assert r["articulation"]["axis"] == pytest.approx([0.0263, 0.9984, 0.0497], abs=2e-4)
    assert l["articulation"]["pivot"] == pytest.approx([257.24, -275, 16.343], abs=0.05)
    assert l["articulation"]["axis"] == pytest.approx([-0.0263, 0.9984, -0.0497], abs=2e-4)
    assert r["articulation"]["range_deg"] == [-10, 10]
    assert errors == {}


def test_follows_the_parameter():
    data, _ = with_hinges(1200)
    r = att(data, "hinge-r")
    assert r["articulation"]["pivot"] == pytest.approx([264.115, 275, 16.465], abs=0.05)
    assert r["articulation"]["axis"] == pytest.approx([0.0512, 0.9974, 0.0501], abs=2e-4)
    for c in data["components"]:
        if c["id"] in ("aileron-r", "aileron-l"):
            assert c["geometry"]["params"]["span"] == 1200


def _copy(tmp_path, span, hinge=True):
    d = tmp_path / "d"
    shutil.copytree(FIX, d)
    t = (d / "plane.yaml").read_text(encoding="utf-8").replace("span_mm: 1000", f"span_mm: {span}")
    if hinge:
        t = t.replace("method: hinge,", "method: hinge, hinge_from: generator,")
    (d / "plane.yaml").write_text(t, encoding="utf-8", newline="\n")
    return d


def _rows(d):
    card = validate(load_design(d), 1)
    return {r.check_id: r for t in card.tiers for r in t.results}


@pytest.mark.parametrize("span", [1000, 1200])
def test_t1_has_no_hinge_fail(tmp_path, span):
    rows = _rows(_copy(tmp_path, span))
    card = validate(load_design(tmp_path / "d"), 1)
    fails = [r.check_id for t in card.tiers for r in t.results if r.status == "FAIL"]
    assert fails == []
    for k in ("T1.attachment", "T1.articulation", "T1.pose"):
        assert k in rows


def test_stale_without_hinge_from(tmp_path):
    rows = _rows(_copy(tmp_path, 1200, hinge=False))
    assert rows["T1.attachment_location"].status == "FAIL"


def test_without_hinge_from_nothing_changes():
    data, _ = resolve_design_data(raw_fix(), FIX)
    r = att(data, "hinge-r")
    assert r["location"] == [250, 275, 10]
    assert r["articulation"]["axis"] == [0, 1, 0]


def test_bad_child_is_an_error():
    raw = raw_fix()
    a = raw["attachments"][0]
    a["child"] = "wing"
    a["parent"] = "aileron-r"
    a["hinge_from"] = "generator"
    data, errors = resolve_design_data(raw, FIX)
    assert "hinge_from" in errors["wing"]
    assert att(data, "hinge-r")["location"] == [250, 275, 10]


def test_schema_and_docs(tmp_path):
    d = _copy(tmp_path, 1000)
    p = d / "plane.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("hinge_from: generator", "hinge_from: mesh"),
                 encoding="utf-8", newline="\n")
    rows = _rows(d)
    assert rows["T0.schema"].status == "FAIL"
    assert "hinge_from" in (ROOT / "docs" / "pdl" / "reference.md").read_text(encoding="utf-8")


def test_no_existing_design_uses_it():
    for f in (ROOT / "designs").glob("*/plane.yaml"):
        if f.parent.name == "c172-rc":  # c172-rc opted in (U16.1 S6 Part B, D112 showcase)
            continue
        assert "hinge_from" not in f.read_text(encoding="utf-8"), f


def test_swept_pockets_see_the_derived_axis(monkeypatch):
    """U16.2: the resolver derives hinge_from before sampling swept poses, so the pockets sweep about the derived axis."""
    seen = []

    def fake(data, cut_files, base_dir, wing_id=None):
        seen.append(copy.deepcopy(att(data, "hinge-r")["articulation"]["axis"]))
        return []
    monkeypatch.setattr("hangar.geom.sweeps.swept_cut_poses", fake)
    raw = raw_fix()
    for a in raw["attachments"]:
        a["hinge_from"] = "generator"
    next(c for c in raw["components"] if c["id"] == "wing")["geometry"]["params"]["cut_files"] = ["x.stl"]
    data, errors = resolve_design_data(raw, FIX)
    assert seen and seen[0] == pytest.approx([0.0263, 0.9984, 0.0497], abs=2e-4) and errors == {}
