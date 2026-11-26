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
      return { p: P.id, q: P.parent, l1, all, rad };
    }""")
    p, q = out["p"], out["q"]
    print("P", p, "Q", q)
    assert all(abs(a - b) <= 1e-6 for a, b in zip(out["l1"][p], out["l1"][q]))
    assert max(abs(a - b) for a, b in zip(out["all"][p], out["all"][q])) > 1e-4
    assert out["rad"][p] != out["all"][p]
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
