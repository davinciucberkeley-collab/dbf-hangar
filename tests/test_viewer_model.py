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
