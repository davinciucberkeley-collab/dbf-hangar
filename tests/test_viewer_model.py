"""Viewer model tests: one renderer per visible viewport, no geometry leak on design switches (U19.1 B0)."""
from __future__ import annotations

import os

import pytest

if os.environ.get("CI"):
    import playwright.sync_api  # noqa: F401  (a missing install must fail loudly)
else:
    pytest.importorskip("playwright.sync_api")

from test_viewer_static import browser, collect, pages_base, studio_base  # noqa: E402,F401

pytestmark = pytest.mark.slow


def _ready(page, mode, timeout=60000):
    page.wait_for_selector(f'#mode-{mode}[data-ready="1"]', timeout=timeout)


def test_model_mode_has_one_canvas(browser, pages_base):
    page = browser.new_page()
    errors = collect(page)
    page.goto(pages_base + "#m=designs&d=mech-good")
    _ready(page, "designs")
    assert page.locator("canvas").count() == 1
    page.goto(pages_base + "#m=compare&a=mech-good&b=example-tailsitter-wing")
    page.click('#modes button[data-mode="compare"]')
    _ready(page, "compare")
    assert page.locator("canvas").count() == 2
    page.click('#modes button[data-mode="designs"]')
    _ready(page, "designs")
    assert page.locator("canvas").count() == 1
    page.click('#modes button[data-mode="stress"]')
    page.wait_for_selector("#mode-stress[data-ready]", state="attached", timeout=60000)
    assert page.locator("canvas").count() == 0
    assert errors == []
    page.close()


def test_design_switches_do_not_leak_geometry(browser, pages_base):
    page = browser.new_page()
    page.goto(pages_base + "#m=designs&d=mech-good")
    _ready(page, "designs")
    ids = ["example-tailsitter-wing", "mech-good"]
    vals = {}
    for n in range(1, 13):
        page.click(f'.design-item[data-id="{ids[(n - 1) % 2]}"]')
        _ready(page, "designs")
        if n in (2, 12):
            page.wait_for_function("window.planeViewer.vp.info().geometries > 0")
            info = page.evaluate("window.planeViewer.vp.info()")
            vals[n] = (info["geometries"], info["textures"])
    print("g2,t2 =", vals[2], "g12,t12 =", vals[12])
    assert vals[2][0] > 0
    assert vals[12][0] == vals[2][0]
    assert vals[12][1] == vals[2][1]
    page.close()


def test_viewport_hooks_exist(browser, pages_base):
    page = browser.new_page()
    page.goto(pages_base + "#m=designs&d=mech-good")
    _ready(page, "designs")
    page.wait_for_function("window.planeViewer.vp.info().calls > 0")
    info = page.evaluate("window.planeViewer.vp.info()")
    print("info", info)
    assert {"geometries", "textures", "calls", "triangles", "canvases", "design"} <= set(info)
    assert info["design"] == "mech-good"
    assert info["triangles"] > 0
    page.close()


def test_look_edges_shadows_tone(browser, pages_base):
    page = browser.new_page()
    errors = collect(page)
    page.goto(pages_base + "#m=designs&d=example-tailsitter-wing")
    _ready(page, "designs")
    page.wait_for_function("window.planeViewer.vp.info().calls > 0")
    i = page.evaluate("window.planeViewer.vp.info()")
    print("look info", i)
    assert i["edgeSegments"] > 0
    assert page.evaluate("window.planeViewer.vp.renderer.toneMapping") != 0
    assert page.evaluate("window.planeViewer.vp.renderer.shadowMap.enabled") is True
    assert page.evaluate("!!window.planeViewer.vp.scene.environment") is True
    assert errors == []
    page.close()


def test_theme_toggle_changes_page_and_canvas(browser, pages_base):
    page = browser.new_page()
    errors = collect(page)
    page.goto(pages_base + "#m=designs&d=example-tailsitter-wing")
    _ready(page, "designs")
    page.wait_for_function("window.planeViewer.vp.info().calls > 0")
    theme = "document.documentElement.dataset.theme"
    bg = "getComputedStyle(document.querySelector('#vp-main')).backgroundColor"
    page.click('[data-testid="theme-toggle"]')
    page.wait_for_timeout(500)
    t1, bg1 = page.evaluate(theme), page.evaluate(bg)
    s1 = page.locator("#vp-main canvas").screenshot()
    page.click('[data-testid="theme-toggle"]')
    page.wait_for_timeout(500)
    t2, bg2 = page.evaluate(theme), page.evaluate(bg)
    s2 = page.locator("#vp-main canvas").screenshot()
    assert {t1, t2} == {"light", "dark"}
    assert bg1 != bg2
    assert s1 != s2
    page.reload()
    _ready(page, "designs")
    assert page.evaluate(theme) == t2
    assert errors == []
    page.close()


def test_stale_mode_callback_does_not_create_viewport(browser, pages_base):
    page = browser.new_page()
    errors = collect(page)
    held = []

    def hold(route):
        held.append(route)

    page.route("**/data/*mechanisms*", hold)
    page.goto(pages_base + "#m=designs&d=mech-good")
    page.wait_for_function("document.querySelector('#mode-designs') !== null")
    for _ in range(60):  # the timeline asks for the sweeps after the scorecard has loaded
        if held:
            break
        page.wait_for_timeout(500)
    assert held, "the mechanisms request was not held"
    page.click('#modes button[data-mode="compare"]')
    _ready(page, "compare")
    for r in held:
        r.continue_()
    page.wait_for_timeout(2500)
    assert page.locator("canvas").count() == 2
    assert page.locator("#vp-main canvas").count() == 0
    assert errors == []
    page.close()


# ---------- U19.1 B2: parts.json, tree, inspector, selection, hide/isolate, views ----------
TREE = "example-tailsitter-wing"


def _open_tree(browser, pages_base):
    page = browser.new_page()
    errors = collect(page)
    page.goto(f"{pages_base}#m=designs&d={TREE}")
    _ready(page, "designs")
    page.wait_for_selector("#parts-tree li.part-row", timeout=30000)
    page.wait_for_function("window.planeViewer.vp && window.planeViewer.vp.state().all.length > 0")
    return page, errors


def _sel(page):
    return page.evaluate("window.planeViewer.vp.state().selection")


def test_index_lists_parts_json(browser, pages_base):
    page = browser.new_page()
    errors = collect(page)
    page.goto(pages_base)
    out = page.evaluate("""async () => {
      const idx = await (await fetch('data/index.json')).json();
      const e = idx.designs.find((d) => d.id === 'example-tailsitter-wing');
      const pj = await (await fetch('data/' + e.parts)).json();
      return { has: !!e.parts, root: pj.root, battery: pj.parts.find((p) => p.id === 'battery') };
    }""")
    assert out["has"] and out["root"] == "center_body" and out["battery"]["parent"] == "center_body"
    assert errors == []
    page.close()


def test_tree_rows_match_parts(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    n = page.evaluate("""async () => {
      const idx = await (await fetch('data/index.json')).json();
      const e = idx.designs.find((d) => d.id === 'example-tailsitter-wing');
      return (await (await fetch('data/' + e.parts)).json()).parts.length;
    }""")
    assert page.locator("#parts-tree li.part-row").count() == n
    assert page.locator('#parts-tree li.part-row[data-id="battery"]').count() == 1
    assert errors == []
    page.close()


def test_tree_click_selects_and_inspects(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    row = '#parts-tree li.part-row[data-id="battery"]'
    page.click(row + " > .row-main")
    assert page.get_attribute(row, "aria-selected") == "true"
    page.wait_for_selector('#inspector[data-id="battery"]')
    assert "battery" in page.inner_text("#inspector")
    assert _sel(page) == ["battery"]
    page.keyboard.press("Escape")
    assert _sel(page) == []
    assert page.get_attribute(row, "aria-selected") == "false"
    assert errors == []
    page.close()


def test_viewport_selection_updates_tree(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    page.evaluate('window.planeViewer.vp.select(["wing"])')
    page.wait_for_selector('#parts-tree li.part-row[data-id="wing"][aria-selected="true"]')
    page.evaluate('window.planeViewer.vp.pick("wing")')
    assert _sel(page) == []
    assert errors == []
    page.close()


def test_ctrl_click_adds_row(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    page.click('#parts-tree li.part-row[data-id="wing"] > .row-main')
    page.click('#parts-tree li.part-row[data-id="battery"] > .row-main', modifiers=["Control"])
    assert sorted(_sel(page)) == ["battery", "wing"]
    assert errors == []
    page.close()


def test_hide_isolate_show_all(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    page.click('[data-testid="eye-wing"]')
    assert page.get_attribute('#parts-tree li.part-row[data-id="wing"]', "data-hidden") == "1"
    assert "wing" not in page.evaluate("window.planeViewer.vp.state().visible")
    page.click('#parts-tree li.part-row[data-id="battery"] > .row-main')
    page.keyboard.press("i")
    assert page.evaluate("window.planeViewer.vp.state().visible") == ["battery"]
    page.keyboard.press("Shift+H")
    st = page.evaluate("window.planeViewer.vp.state()")
    assert sorted(st["visible"]) == sorted(st["all"]) and len(st["all"]) >= 10
    assert errors == []
    page.close()


def _cam(page):
    return page.evaluate("""() => { const v = window.planeViewer.vp;
      const p = v.camera.position.clone().sub(v.controls.target); return { x: p.x, y: p.y, len: p.length() }; }""")


def test_standard_views_move_the_camera(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    page.evaluate('window.planeViewer.vp.view("top")')
    page.wait_for_timeout(400)
    p = _cam(page)
    assert abs(p["y"]) > 0.9 * p["len"]
    page.evaluate('window.planeViewer.vp.view("front")')
    page.wait_for_timeout(400)
    p = _cam(page)
    assert p["x"] > 0.9 * p["len"]
    assert errors == []
    page.close()


def test_fit_to_selection_moves_closer(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    before = _cam(page)["len"]
    page.evaluate('window.planeViewer.vp.fitTo(["battery"])')
    page.wait_for_timeout(400)
    assert before > _cam(page)["len"]
    assert errors == []
    page.close()


# ---------- U19.1 B3: see inside (x-ray, ghost, pick-through, Alt-click cycle, section plane) ----------
SIDE_O, SIDE_D = [140, -800, -27.5], [0, 1, 0]
TOP_O, TOP_D = [140, 0, 800], [0, 0, -1]
VP = "window.planeViewer.vp"


def _ray(page, o, d):
    return page.evaluate(f"([o, d]) => {VP}.pickRay(o, d)", [o, d])


def _canvas_png(page):
    page.wait_for_timeout(300)
    return page.locator("#vp-main canvas").screenshot()


def test_xray_picks_through_the_skin(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    ids = _ray(page, SIDE_O, SIDE_D)
    assert "center_body" in ids and "battery" in ids and ids.index("center_body") < ids.index("battery"), ids
    page.click('[data-testid="btn-xray"]')
    ids2 = _ray(page, SIDE_O, SIDE_D)
    assert "center_body" not in ids2 and ids2[0] == "battery", ids2
    st = page.evaluate(f"{VP}.state()")
    assert st["xray"] is True
    assert "center_body" in st["ghosted"] and "wing" in st["ghosted"] and "battery" not in st["ghosted"]
    assert errors == []
    page.close()


def test_xray_changes_the_picture(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    before = _canvas_png(page)
    again = _canvas_png(page)
    assert before == again  # an unchanged view is stable
    page.click('[data-testid="btn-xray"]')
    after = _canvas_png(page)
    assert before != after
    assert errors == []
    page.close()


def test_ghost_key_and_tree_button(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    page.evaluate(f'{VP}.select(["wing"])')
    page.keyboard.press("g")
    assert "wing" in page.evaluate(f"{VP}.state().ghosted")
    page.wait_for_selector('#parts-tree li.part-row[data-id="wing"][data-ghost="1"]')
    page.keyboard.press("g")
    assert "wing" not in page.evaluate(f"{VP}.state().ghosted")
    page.wait_for_selector('#parts-tree li.part-row[data-id="wing"][data-ghost="0"]')
    page.click('[data-testid="ghost-fin_l"]')
    assert "fin_l" in page.evaluate(f"{VP}.state().ghosted")
    assert errors == []
    page.close()


def test_alt_click_cycles_front_to_back(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    ids = _ray(page, SIDE_O, SIDE_D)
    assert len(ids) == 2, ids
    cyc = [page.evaluate(f"([o, d]) => {VP}.cyclePick(o, d)", [SIDE_O, SIDE_D]) for _ in range(3)]
    assert cyc == [ids[0], ids[1], ids[0]]
    assert page.evaluate(f"{VP}.state().selection") == [cyc[2]]
    assert errors == []
    page.close()


def test_section_clips_and_unclips(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    page.click('[data-testid="btn-xray"]')
    assert _ray(page, TOP_O, TOP_D)[0] == "battery"
    page.evaluate(f'{VP}.section("x", 0.95, false)')
    clipped = _canvas_png(page)
    assert "battery" not in _ray(page, TOP_O, TOP_D)
    assert page.evaluate(f"{VP}.state().section") == {"axis": "x", "value": 0.95, "flip": False}
    page.evaluate(f'{VP}.section("x", 0.95, true)')
    assert "battery" in _ray(page, TOP_O, TOP_D)
    page.evaluate(f"{VP}.section(null)")
    assert page.evaluate(f"{VP}.state().section") is None
    assert "battery" in _ray(page, TOP_O, TOP_D)
    assert _canvas_png(page) != clipped
    assert errors == []
    page.close()


def test_section_controls_drive_the_hook(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    page.select_option('[data-testid="section-axis"]', "y")
    page.fill('[data-testid="section-slider"]', "700")
    page.check('[data-testid="section-flip"]')
    assert page.evaluate(f"{VP}.state().section") == {"axis": "y", "value": 0.7, "flip": True}
    page.select_option('[data-testid="section-axis"]', "off")
    assert page.evaluate(f"{VP}.state().section") is None
    assert errors == []
    page.close()


def test_xray_ghosts_everything_but_internal_types(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    page.click('[data-testid="btn-xray"]')
    g = page.evaluate(f"{VP}.state().ghosted")
    for gone in ("mount_l", "center_body", "wing", "prop_l", "fin_l"):
        assert gone in g, (gone, g)
    for solid in ("battery", "flight_controller", "motor_l"):
        assert solid not in g, (solid, g)
    assert errors == []
    page.close()


def test_section_y_and_z_cut_geometrically(browser, pages_base):
    page, errors = _open_tree(browser, pages_base)
    page.click('[data-testid="btn-xray"]')
    hit = lambda: "battery" in _ray(page, TOP_O, TOP_D)  # noqa: E731
    for axis in ("y", "z"):
        page.evaluate(f'{VP}.section("{axis}", 0, false)')
        assert hit(), axis          # plane at the box min keeps everything
        page.evaluate(f'{VP}.section("{axis}", 1, false)')
        assert not hit(), axis      # plane at the box max keeps nothing
        page.evaluate(f'{VP}.section("{axis}", 1, true)')
        assert hit(), axis          # flipped keeps the other side
        page.evaluate(f'{VP}.section("{axis}", 0, true)')
        assert not hit(), axis
    assert errors == []
    page.close()


# ---------- U19.1 B4: transform layers, explode, timeline replaces Physics ----------
def _open(browser, pages_base, design):
    page = browser.new_page()
    errors = collect(page)
    page.goto(f"{pages_base}#m=designs&d={design}")
    _ready(page, "designs")
    page.wait_for_function("window.planeViewer.vp && window.planeViewer.vp.state().all.length > 0")
    return page, errors


def test_old_physics_link_maps_to_model_with_timeline(browser, pages_base):
    page = browser.new_page()
    errors = collect(page)
    page.goto(pages_base + "#m=physics&d=mech-good")
    _ready(page, "designs")
    assert page.evaluate("document.body.dataset.mode") == "designs"
    assert page.is_visible("#timeline")
    assert "Physics" not in page.locator("#modes button").all_inner_texts()
    assert errors == []
    page.close()


def test_mm_scene_round_trip(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    out = page.evaluate("""async () => {
      const m = await import('./vp/transforms.js');
      return [[10, 0, 0], [-5.5, 12.3, 0.7], [0, 0, -27.5]].map((v) => m.sceneToMm(m.mmToScene(v)));
    }""")
    for got, want in zip(out, [[10, 0, 0], [-5.5, 12.3, 0.7], [0, 0, -27.5]]):
        assert all(abs(a - b) <= 0.05 for a, b in zip(got, want)), (got, want)
    assert errors == []
    page.close()


def test_explode_moves_every_non_root_part_and_zero_restores(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    page.evaluate("window.planeViewer.vp.explode(1)")
    s = page.evaluate("window.planeViewer.vp.state()")
    print("not moved:", set(s["all"]) - {"center_body"} - set(s["moved"]), "moved extra:", set(s["moved"]) - set(s["all"]))
    assert set(s["moved"]) == set(s["all"]) - {"center_body"}
    assert s["explode"]["t"] == 1
    page.evaluate("window.planeViewer.vp.explode(0)")
    s = page.evaluate("window.planeViewer.vp.state()")
    assert s["moved"] == []
    assert not any(page.evaluate("(id) => window.planeViewer.vp.transforms.isMoved(id)", i) for i in s["all"])
    assert errors == []
    page.close()


def test_explode_levels_keep_subassemblies_together(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    out = page.evaluate("""async () => {
      const vp = window.planeViewer.vp, parts = vp.parts.parts, ids = new Set(vp.state().all);
      const P = parts.find((p) => p.depth >= 2 && ids.has(p.id) && ids.has(p.parent));
      vp.explode(1, 1); const l1 = vp.state().offsets;
      vp.explode(1, 'all'); const all = vp.state().offsets;
      vp.explode(1, 'all', 'radial'); const rad = vp.state().offsets;
      vp.explode(1, P.depth); const deep = vp.state().offsets;
      return { p: P.id, q: P.parent, l1, all, rad, deep };
    }""")
    p, q = out["p"], out["q"]
    print("P", p, "Q", q)
    assert all(abs(a - b) <= 1e-6 for a, b in zip(out["l1"][p], out["l1"][q]))
    assert all(abs(a - b) <= 1e-6 for a, b in zip(out["all"][p], out["all"][q]))  # hierarchy: whole subassemblies as units (D109)
    assert out["rad"][p] != out["all"][p]  # radial moves each part on its own
    assert max(abs(a - b) for a, b in zip(out["deep"][p], out["deep"][q])) > 1e-4  # a deeper level separates P from its parent
    assert max(abs(a - b) for a, b in zip(out["rad"][p], out["rad"][q])) > 1e-4
    assert errors == []
    page.close()


def test_explode_controls_drive_the_hook(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    page.fill('[data-testid="explode-slider"]', "500")
    assert page.evaluate("window.planeViewer.vp.state().explode.t") == 0.5
    page.select_option('[data-testid="explode-level"]', "1")
    assert page.evaluate("window.planeViewer.vp.state().explode.level") == 1
    page.select_option('[data-testid="explode-strategy"]', "radial")
    assert page.evaluate("window.planeViewer.vp.state().explode.strategy") == "radial"
    assert errors == []
    page.close()


def test_explode_and_timeline_compose(browser, pages_base):
    page, errors = _open(browser, pages_base, "mech-good")
    page.evaluate("window.planeViewer.vp.explode(0.5)")
    page.click('[data-testid="tl-play"]')
    page.wait_for_function("document.querySelector('[data-testid=tl-input]').textContent === '20'", timeout=15000)
    s = page.evaluate("window.planeViewer.vp.state()")
    assert "flap" in s["moved"] and any(abs(v) > 0 for v in s["offsets"]["flap"])
    page.evaluate("window.planeViewer.vp.explode(0)")
    s = page.evaluate("window.planeViewer.vp.state()")
    assert "flap" in s["moved"] and s["offsets"]["flap"] == [0, 0, 0]
    assert errors == []
    page.close()


def test_timeline_opens_at_input_zero_with_nothing_moved(browser, pages_base):
    page, errors = _open(browser, pages_base, "four-bar")  # sweep runs -20..20
    page.wait_for_selector('[data-testid="tl-scrub"]')
    assert page.inner_text('[data-testid="tl-input"]') == "0"
    assert page.evaluate("window.planeViewer.vp.state().moved") == []
    page.evaluate("document.querySelector('[data-testid=tl-scrub]').value = 0; document.querySelector('[data-testid=tl-scrub]').dispatchEvent(new Event('input'))")
    assert page.inner_text('[data-testid="tl-input"]') == "-20"
    assert page.evaluate("window.planeViewer.vp.state().moved") != []
    assert errors == []
    page.close()


# ---------- U19.1 B5: move parts with a gizmo, review, Apply through design.set ----------
VPJ = "window.planeViewer.vp"
BATTERY = {"id": "battery", "from_mm": [140, 0, -27.5], "to_mm": [150, 0, -27.5], "delta_mm": [10, 0, 0]}


def test_move_hook_and_pending_units(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    assert page.evaluate(f'{VPJ}.move("battery", [10, 0, 0])') is True
    assert page.evaluate(f"{VPJ}.pending()") == [BATTERY]
    assert page.evaluate(f'{VPJ}.move("battery", [0, 5, 2.5])') is True
    assert page.evaluate(f"{VPJ}.pending()[0].delta_mm") == [10, 5, 2.5]
    assert "battery" in page.evaluate(f"{VPJ}.state().moved")
    assert page.get_attribute('li.part-row[data-id="battery"]', "data-moved") == "1"
    assert page.inner_text('[data-testid="apply-count"]').startswith("1 part moved")
    assert errors == []
    page.close()


def test_move_with_attached_parts_toggle(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    assert page.evaluate(f'{VPJ}.move("wing", [0, 0, 5])') is True
    pend = page.evaluate(f"{VPJ}.pending()")
    assert sorted(p["id"] for p in pend) == sorted(["wing", "mount_l", "mount_r", "motor_l", "motor_r", "prop_l", "prop_r", "fin_l", "fin_r"])
    assert all(p["delta_mm"] == [0, 0, 5] for p in pend)
    page.click('[data-testid="btn-revert"]')
    assert page.evaluate(f"{VPJ}.pending()") == []
    assert page.evaluate(f"{VPJ}.state().moved") == []
    page.uncheck('[data-testid="move-with-attached"]')
    assert page.evaluate(f'{VPJ}.move("wing", [0, 0, 5])') is True
    assert [p["id"] for p in page.evaluate(f"{VPJ}.pending()")] == ["wing"]
    assert errors == []
    page.close()


def test_move_is_refused_while_exploded_and_for_unknown(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    page.evaluate(f"{VPJ}.explode(0.5)")
    assert page.evaluate(f'{VPJ}.move("battery", [1, 0, 0])') is False
    assert page.evaluate(f"{VPJ}.pending()") == []
    assert page.is_disabled('[data-testid="tool-move"]')
    page.evaluate(f"{VPJ}.explode(0)")
    assert page.is_enabled('[data-testid="tool-move"]')
    assert page.evaluate(f'{VPJ}.move("nope", [1, 0, 0])') is False
    assert errors == []
    page.close()


def test_tool_move_shows_gizmo_on_selection(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    page.click('[data-testid="tool-move"]')
    page.evaluate(f'{VPJ}.select(["battery"])')
    s = page.evaluate(f"{VPJ}.state()")
    assert s["tool"] == "move" and s["gizmo"] == "battery"
    page.wait_for_function(f"{VPJ}.mover.tc && {VPJ}.mover.tc.object !== undefined")
    page.evaluate(f"{VPJ}.select([])")
    assert page.evaluate(f"{VPJ}.state().gizmo") is None
    page.click('[data-testid="tool-select"]')
    assert page.evaluate(f"{VPJ}.state().tool") == "select"
    assert errors == []
    page.close()


def test_nudge_inputs_set_the_delta(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    page.evaluate(f'{VPJ}.select(["battery"])')
    page.evaluate(f'{VPJ}.move("battery", [10, 0, 0])')
    page.fill('[data-testid="nudge-x"]', "12.5")
    page.press('[data-testid="nudge-x"]', "Tab")
    assert page.evaluate(f"{VPJ}.pending()[0].delta_mm") == [12.5, 0, 0]
    assert page.is_visible('[data-testid="tag-moved"]')
    assert errors == []
    page.close()


def test_timeline_blocked_while_moves_are_pending(browser, pages_base):
    page, errors = _open(browser, pages_base, "mech-good")
    assert page.is_enabled('[data-testid="tl-play"]')
    assert page.evaluate(f'{VPJ}.move("arm", [1, 0, 0])') is True
    assert page.is_disabled('[data-testid="tl-play"]')
    assert page.is_visible('[data-testid="tl-blocked"]')
    page.click('[data-testid="btn-revert"]')
    assert page.is_enabled('[data-testid="tl-play"]')
    assert errors == []
    page.close()


def test_discard_prompt_on_design_switch(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    page.evaluate(f'{VPJ}.move("battery", [10, 0, 0])')
    msgs = []
    action = ["dismiss"]

    def on_dialog(d):
        msgs.append(d.message)
        d.dismiss() if action[0] == "dismiss" else d.accept()
    page.on("dialog", on_dialog)
    page.click('.design-item[data-id="mech-good"]')
    assert page.evaluate("window.planeViewer.selected()") == "example-tailsitter-wing"
    assert len(page.evaluate(f"{VPJ}.pending()")) == 1
    action[0] = "accept"
    page.click('.design-item[data-id="mech-good"]')
    _ready(page, "designs")
    assert page.evaluate("window.planeViewer.selected()") == "mech-good"
    assert page.evaluate(f"{VPJ}.pending()") == []
    assert msgs == ["Discard 1 unsaved move?", "Discard 1 unsaved move?"]
    assert errors == []
    page.close()


def test_pages_build_has_revert_but_no_apply(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    page.evaluate(f'{VPJ}.move("battery", [10, 0, 0])')
    assert page.locator('[data-testid="btn-revert"]').count() == 1
    assert page.locator('[data-testid="btn-review-apply"]').count() == 0
    assert page.locator("[data-edit]").count() == 0
    assert errors == []
    page.close()


def _studio_open(browser, studio_base):
    from hangar import studio
    ddir = studio.DESIGNS_DIR / "example-tailsitter-wing"
    page = browser.new_page()
    errors = collect(page)
    page.goto(studio_base + "#m=designs&d=example-tailsitter-wing")
    _ready(page, "designs")
    page.wait_for_selector('[data-testid="btn-validate"]:not([disabled])', timeout=240000)
    page.wait_for_function("window.planeViewer.vp && window.planeViewer.vp.state().all.length > 0")
    return page, errors, ddir


def _apply(page, why):
    page.click('[data-testid="btn-review-apply"]')
    page.wait_for_selector("dialog.dlg")
    page.fill('[data-testid="apply-why"]', why)
    page.click('[data-testid="apply-go"]')
    page.wait_for_selector("dialog.dlg", state="detached", timeout=30000)


def _positions(ddir):
    import yaml
    doc = yaml.safe_load((ddir / "plane.yaml").read_text())
    return {c["id"]: c["position"] for c in doc["components"]}


def _changelog(ddir):
    import yaml
    f = ddir / "CHANGELOG.yaml"
    return yaml.safe_load(f.read_text()) if f.exists() else []


def test_apply_writes_one_position_and_one_changelog_entry(browser, studio_base):
    page, errors, ddir = _studio_open(browser, studio_base)
    plane_bytes, before, log0 = (ddir / "plane.yaml").read_bytes(), _positions(ddir), _changelog(ddir)
    page.evaluate(f'{VPJ}.select(["battery"])')
    page.evaluate(f'{VPJ}.move("battery", [10, 0, 0])')
    cam = page.evaluate(f"{VPJ}.camera.position.toArray()")
    page.click('[data-testid="btn-review-apply"]')
    page.wait_for_selector("dialog.dlg")
    text = page.inner_text("dialog.dlg")
    assert "components[battery].position" in text
    assert "[140, 0, -27.5] -> [150, 0, -27.5]" in text
    cli = page.inner_text('[data-testid="apply-cli"]')
    assert "plane design set" in cli and '"components[battery].position"' in cli
    page.click('[data-testid="apply-go"]')
    assert page.inner_text("dialog.dlg .dlg-err") == "Say why in one line."
    assert (ddir / "plane.yaml").read_bytes() == plane_bytes
    page.fill('[data-testid="apply-why"]', "battery 10 mm aft for CG")
    page.click('[data-testid="apply-go"]')
    page.wait_for_selector("dialog.dlg", state="detached", timeout=30000)
    after = _positions(ddir)
    assert after["battery"] == [150, 0, -27.5]
    assert {k: v for k, v in after.items() if k != "battery"} == {k: v for k, v in before.items() if k != "battery"}
    log = _changelog(ddir)
    assert len(log) == len(log0) + 1
    assert log[-1]["key"] == "components[battery].position"
    assert log[-1]["why"] == "battery 10 mm aft for CG"
    assert log[-1]["kind"] == "modify"
    from test_viewer_static import _wait_studio_idle
    _wait_studio_idle(studio_base)
    page.wait_for_function(f"{VPJ}.state().pending === 0")
    page.wait_for_function(f"{VPJ}.parts && {VPJ}.parts.parts.find((p) => p.id === 'battery').position_mm[0] === 150", timeout=60000)
    assert page.evaluate(f"{VPJ}.state().selection") == ["battery"]
    now = page.evaluate(f"{VPJ}.camera.position.toArray()")
    assert all(abs(a - b) < 1e-6 for a, b in zip(cam, now)), (cam, now)
    assert errors == []
    page.close()


def test_apply_two_parts_use_also_one_changelog_each(browser, studio_base):
    page, errors, ddir = _studio_open(browser, studio_base)
    before, log0 = _positions(ddir), _changelog(ddir)
    page.uncheck('[data-testid="move-with-attached"]')
    assert page.evaluate(f'{VPJ}.move("fin_l", [0, 0, 3])') is True
    assert page.evaluate(f'{VPJ}.move("fin_r", [0, 0, 3])') is True
    page.click('[data-testid="btn-review-apply"]')
    page.wait_for_selector("dialog.dlg")
    assert "--also" in page.inner_text('[data-testid="apply-cli"]')
    page.click("dialog.dlg footer .ghost")
    page.wait_for_selector("dialog.dlg", state="detached")
    _apply(page, "fins 3 mm up")
    after = _positions(ddir)
    for fid in ("fin_l", "fin_r"):
        assert after[fid] == [before[fid][0], before[fid][1], before[fid][2] + 3]
    log = _changelog(ddir)
    assert len(log) == len(log0) + 2
    assert {e["key"] for e in log[-2:]} == {"components[fin_l].position", "components[fin_r].position"}
    assert all(e["why"] == "fins 3 mm up" for e in log[-2:])
    assert errors == []
    page.close()


def test_revert_leaves_the_file_byte_identical(browser, studio_base):
    page, errors, ddir = _studio_open(browser, studio_base)
    log_file = ddir / "CHANGELOG.yaml"
    plane_bytes = (ddir / "plane.yaml").read_bytes()
    log_bytes = log_file.read_bytes() if log_file.exists() else None
    page.evaluate(f'{VPJ}.move("battery", [10, 0, 0])')
    page.click('[data-testid="btn-revert"]')
    assert page.evaluate(f"{VPJ}.pending()") == []
    assert (ddir / "plane.yaml").read_bytes() == plane_bytes
    assert (log_file.read_bytes() if log_file.exists() else None) == log_bytes
    assert errors == []
    page.close()


_SCREEN = """(d) => { const vp = window.planeViewer.vp, v = vp.mover.proxy.position.clone();
  v.x += d[0]; v.y += d[1]; v.z += d[2]; v.project(vp.camera);
  const r = vp.renderer.domElement.getBoundingClientRect();
  return [r.left + (v.x + 1) / 2 * r.width, r.top + (1 - v.y) / 2 * r.height]; }"""


def test_gizmo_drag_moves_the_part_in_whole_millimetres(browser, pages_base):
    page, errors = _open(browser, pages_base, TREE)
    page.set_viewport_size({"width": 1500, "height": 900})  # the top bars overlap in the default 1280 px window
    page.click('[data-testid="view-side"]')
    page.wait_for_timeout(600)
    page.click('[data-testid="tool-move"]')
    page.evaluate(f'{VPJ}.select(["battery"])')
    page.wait_for_function(f"{VPJ}.mover.tc && {VPJ}.mover.tc.object !== undefined")
    page.wait_for_timeout(300)
    origin = page.evaluate(_SCREEN, [0, 0, 0])
    hit = None
    for k in range(5, 60, 2):  # hover along the scene X arrow until the gizmo reports it
        hit = page.evaluate(_SCREEN, [k / 1000, 0, 0])
        page.mouse.move(*hit)
        page.wait_for_timeout(30)
        if page.evaluate(f"{VPJ}.mover.tc.axis") == "X":
            break
    assert page.evaluate(f"{VPJ}.mover.tc.axis") == "X"
    dx, dy = hit[0] - origin[0], hit[1] - origin[1]
    norm = (dx * dx + dy * dy) ** 0.5
    page.mouse.down()
    for s in range(1, 9):
        page.mouse.move(hit[0] + dx / norm * 8 * s, hit[1] + dy / norm * 8 * s)
        page.wait_for_timeout(30)
    page.mouse.up()
    pend = page.evaluate(f"{VPJ}.pending()")
    assert len(pend) == 1 and pend[0]["id"] == "battery"
    d = pend[0]["delta_mm"]
    assert d[0] != 0 and d[1] == 0 and d[2] == 0 and d[0] == int(d[0])  # one axis, whole millimetres
    assert page.evaluate(f"{VPJ}.state().selection") == ["battery"]  # the click-through did not deselect
    assert errors == []
    page.close()
