"""plane generators list / show read the geometry generator registry (U13.2)."""
from __future__ import annotations

from hangar.geom import registry as greg
from hangar.ops import call, registry


def test_list_has_every_registered_generator():
    r = call("generators.list")
    assert r.ok
    assert [g["name"] for g in r.data["generators"]] == greg.names()


def test_list_required_for_wing_panel():
    r = call("generators.list")
    entry = next(g for g in r.data["generators"] if g["name"] == "wing_panel")
    assert entry["required"] == ["airfoil_file", "span", "root_chord", "tip_chord"]


def test_show_wing_panel_params():
    r = call("generators.show", name="wing_panel")
    assert r.ok
    params = {p["name"]: p for p in r.data["params"]}
    assert params["span"]["kind"] == "number"
    assert params["span"]["required"] is True
    assert params["span"]["exclusive_minimum"] == 0
    assert params["span"]["doc"] == "tip to tip, mm"
    assert params["placement"]["choices"] == ["none", "high", "mid", "low"]
    assert params["placement"]["default"] == "none"
    assert params["sweep_le_deg"]["default"] == 0.0
    assert params["sweep_le_deg"]["required"] is False
    assert len(r.data["params"]) == len(greg.get("wing_panel").params)


def test_show_unknown_names_the_known_ones():
    r = call("generators.show", name="nope")
    assert r.ok is False
    assert r.data.get("error") == "input"
    msg = " ".join(r.messages)
    assert "known:" in msg
    assert "wing_panel" in msg


def test_show_renders_text():
    text = registry()["generators.show"].render(call("generators.show", name="tube"))
    assert "units:" in text
    assert "example: geometry: {generator: tube, params: {" in text


def test_every_generator_shows():
    for name in greg.names():
        assert call("generators.show", name=name).ok, name


def test_cli_and_mcp_expose_it():
    reg = registry()
    assert "generators.list" in reg
    assert "generators.show" in reg
