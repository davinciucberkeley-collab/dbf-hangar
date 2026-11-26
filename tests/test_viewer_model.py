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
    page.click('#modes button[data-mode="physics"]')
    _ready(page, "physics")
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
    page.goto(pages_base + "#m=physics&d=mech-good")
    page.wait_for_function("document.querySelector('#mode-physics') !== null")
    page.wait_for_timeout(1500)
    assert held, "the mechanisms request was not held"
    page.click('#modes button[data-mode="designs"]')
    _ready(page, "designs")
    for r in held:
        r.continue_()
    page.wait_for_timeout(2500)
    assert page.locator("canvas").count() == 1
    assert page.locator("#vp-phys canvas").count() == 0
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
