import json

from click.testing import CliRunner
import pytest

import hangar.cli as cli_mod


def _real_paths():
    return {p.parent.name: p for p in cli_mod.list_designs()}


def _stub_entry(seen):
    def stub(design, out):
        did = str(design.data.get("id", ""))
        seen.append(did)
        return {"id": did, "name": "", "status": "", "morphology": {}}
    return stub


def test_unknown_design_is_refused_and_creates_nothing(tmp_path):
    res = CliRunner().invoke(cli_mod.cli, ["build-index", "--out", str(tmp_path / "o"), "--design", "nope"])
    assert res.exit_code != 0
    assert "unknown design(s): nope" in res.output
    assert "example-tailsitter-wing" in res.output
    assert not (tmp_path / "o").exists()


def test_only_the_named_design_is_built(tmp_path, monkeypatch):
    import hangar.index as index_mod
    paths = _real_paths()
    chosen = [paths["example-tailsitter-wing"], paths["c0-a1"]]
    monkeypatch.setattr(cli_mod, "list_designs", lambda: chosen)
    seen = []
    monkeypatch.setattr(index_mod, "design_entry", _stub_entry(seen))
    out = tmp_path / "o"
    res = CliRunner().invoke(cli_mod.cli, ["build-index", "--out", str(out), "--design", "example-tailsitter-wing"])
    assert res.exit_code == 0, res.output
    assert seen == ["example-tailsitter-wing"]
    designs = json.loads((out / "index.json").read_text())["designs"]
    assert len(designs) == 1
    assert designs[0]["id"] == "example-tailsitter-wing"


def test_two_designs_and_default(tmp_path, monkeypatch):
    import hangar.index as index_mod
    paths = _real_paths()
    chosen = [paths["example-tailsitter-wing"], paths["c0-a1"]]
    monkeypatch.setattr(cli_mod, "list_designs", lambda: chosen)
    seen = []
    monkeypatch.setattr(index_mod, "design_entry", _stub_entry(seen))
    res = CliRunner().invoke(cli_mod.cli, ["build-index", "--out", str(tmp_path / "a"),
                                           "--design", "example-tailsitter-wing", "--design", "c0-a1"])
    assert res.exit_code == 0, res.output
    assert sorted(seen) == ["c0-a1", "example-tailsitter-wing"]

    seen.clear()
    res = CliRunner().invoke(cli_mod.cli, ["build-index", "--out", str(tmp_path / "b")])
    assert res.exit_code == 0, res.output
    assert sorted(seen) == ["c0-a1", "example-tailsitter-wing"]


def test_option_is_documented():
    res = CliRunner().invoke(cli_mod.cli, ["build-index", "--help"])
    assert res.exit_code == 0
    assert "--design" in res.output


@pytest.mark.slow
def test_real_single_design_build_is_slow_but_works(tmp_path):
    out = tmp_path / "o"
    res = CliRunner().invoke(cli_mod.cli, ["build-index", "--out", str(out), "--design", "example-tailsitter-wing"])
    assert res.exit_code == 0, res.output
    assert (out / "example-tailsitter-wing.glb").exists()
    index = json.loads((out / "index.json").read_text())
    assert [d["id"] for d in index["designs"]] == ["example-tailsitter-wing"]


# U19.2 brief 3: <id>.rows.json next to the scorecard

def _tailsitter():
    from hangar.design import load_design
    return load_design(_real_paths()["example-tailsitter-wing"])


def test_rows_json_written_and_aligned(tmp_path):
    import hangar.index as index_mod
    design = _tailsitter()
    entry = index_mod.design_entry(design, tmp_path)
    fid = "example-tailsitter-wing"
    assert (tmp_path / f"{fid}.rows.json").exists()
    assert entry["rows"] == f"{fid}.rows.json"
    rows = json.loads((tmp_path / f"{fid}.rows.json").read_text())
    card = json.loads((tmp_path / f"{fid}.scorecard.json").read_text())
    assert len(rows["tiers"]) == len(card["tiers"])
    for rt, ct in zip(rows["tiers"], card["tiers"]):
        assert len(rt["rows"]) == len(ct["results"])
        for rr, cr in zip(rt["rows"], ct["results"]):
            assert rr["check_id"] == cr["check_id"]
            assert rr["status"] == cr["status"]


def test_scorecard_json_unchanged_by_rows(tmp_path):
    import hangar.index as index_mod
    from hangar.checks import validate
    design = _tailsitter()
    index_mod.design_entry(design, tmp_path)
    fid = "example-tailsitter-wing"
    # text mode: Path.write_text translates "\n" to CRLF on Windows, so compare decoded text
    assert (tmp_path / f"{fid}.scorecard.json").read_text() == index_mod.dumps(validate(design).to_dict()) + "\n"


def test_rows_json_failure_does_not_break_index(tmp_path, monkeypatch):
    import hangar.index as index_mod
    fid = "example-tailsitter-wing"

    def boom(card, design):
        raise RuntimeError("text problem")
    monkeypatch.setattr(index_mod, "rows_json", boom)
    entry = index_mod.design_entry(_tailsitter(), tmp_path)
    assert entry["rows"] is None
    assert not (tmp_path / f"{fid}.rows.json").exists()
    assert entry["scorecard"] == f"{fid}.scorecard.json"


def test_rows_have_text(tmp_path):
    import hangar.index as index_mod
    fid = "example-tailsitter-wing"
    index_mod.design_entry(_tailsitter(), tmp_path)
    rows = json.loads((tmp_path / f"{fid}.rows.json").read_text())
    for tier in rows["tiers"]:
        for row in tier["rows"]:
            if row["status"] != "PASS":
                assert row["title"], row["check_id"]
                assert row["sentence"], row["check_id"]
