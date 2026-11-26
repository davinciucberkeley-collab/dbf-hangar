"""Browser smoke tests for the viewer (one app: Studio with modes; the Pages build is the same app read-only)."""
from __future__ import annotations

import functools
import json
import os
import shutil
import threading
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

if os.environ.get("CI"):
    import playwright.sync_api  # noqa: F401  (a missing install must fail loudly)
else:
    pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Error as PWError, expect, sync_playwright  # noqa: E402

from hangar import cli, design as design_mod, studio  # noqa: E402

pytestmark = pytest.mark.slow

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
EXAMPLE = REPO / "designs" / "example-tailsitter-wing"
CDN = "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js"
MODES = ["designs", "compare", "stress", "updates", "ledger"]


class _Server(ThreadingHTTPServer):
    request_queue_size = 64   # default 5 overflows under Chromium's parallel requests on Windows CI (T57)


def _serve(handler):
    httpd = _Server(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def _seed(designs: Path):
    shutil.copytree(EXAMPLE, designs / "example-tailsitter-wing")
    (designs / "mech-good").mkdir()
    shutil.copy(FIXTURES / "mech-good.yaml", designs / "mech-good" / "plane.yaml")


@pytest.fixture(scope="module")
def pages_base(tmp_path_factory):
    root = tmp_path_factory.mktemp("pages")
    site = root / "site"
    shutil.copytree(REPO / "viewer", site, ignore=shutil.ignore_patterns("data", "updates", "docs"))
    _seed(root / "designs")
    (root / "updates" / "2026-11-16").mkdir(parents=True)
    (root / "updates" / "2026-11-16" / "updates.yaml").write_text(
        'entries:\n  - {person: Ana, link: "https://example.com/a", changed: did x}\n')
    (root / "ledger").mkdir()
    (root / "ledger" / "items.yaml").write_text(
        "schema: ledger/1\nitems:\n  - {id: R1, kind: ruling, text: t, source: quote, status: open, evidence: secret}\n")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(cli, "DESIGNS_DIR", root / "designs", raising=False)
        mp.setattr(design_mod, "DESIGNS_DIR", root / "designs", raising=False)
        res = CliRunner().invoke(cli.cli, ["build-index", "--out", str(site / "data")])
    assert res.exit_code == 0, res.output
    httpd = _serve(functools.partial(SimpleHTTPRequestHandler, directory=str(site)))
    yield f"http://127.0.0.1:{httpd.server_port}/"
    httpd.shutdown()
    httpd.server_close()


def _start_studio(tmp_path, monkeypatch, seed):
    designs = tmp_path / "designs"
    seed(designs)
    for mod in (cli, design_mod, studio):
        monkeypatch.setattr(mod, "DESIGNS_DIR", designs, raising=False)
    monkeypatch.setattr(studio, "STUDIO_DIR", tmp_path / ".studio")
    monkeypatch.setattr(studio, "DATA_DIR", tmp_path / ".studio" / "data")
    monkeypatch.setattr(studio, "CACHE_FILE", tmp_path / ".studio" / "cache.json")
    httpd = _serve(studio.make_handler(studio.Studio()))
    base = f"http://127.0.0.1:{httpd.server_port}"
    t0 = time.time()
    while time.time() - t0 < 240:
        with urllib.request.urlopen(base + "/api/state", timeout=60) as r:
            if not json.loads(r.read())["busy"]:
                break
        time.sleep(0.3)
    else:
        raise AssertionError("studio jobs did not finish")
    return httpd, base + "/"


@pytest.fixture
def studio_base(tmp_path, monkeypatch):
    httpd, base = _start_studio(tmp_path, monkeypatch, _seed)
    yield base
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture
def concept_a_studio(tmp_path, monkeypatch):
    httpd, base = _start_studio(tmp_path, monkeypatch, lambda d: shutil.copytree(REPO / "tests" / "fixtures" / "concept-a-frozen", d / "concept-a"))
    yield base
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture(scope="module")
def browser():
    def bail(msg):
        pytest.fail(msg) if os.environ.get("CI") else pytest.skip(msg)
    try:
        urllib.request.urlopen(CDN, timeout=10).close()
    except Exception:  # noqa: BLE001
        bail("three.js CDN unreachable")
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        except PWError as e:
            if "Executable doesn't exist" not in str(e):
                raise
            bail("run: python -m playwright install chromium")
        yield b
        b.close()


def collect(page):
    errors = []
    page.on("console", lambda m: errors.append(f"{m.text} {m.location.get('url', '')}".strip()) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    return errors


@pytest.mark.parametrize("mode", MODES)
def test_every_mode_renders_without_console_errors(browser, pages_base, mode):
    page = browser.new_page()
    errors = collect(page)
    page.goto(f"{pages_base}#m={mode}&d=mech-good")
    sel = f"#mode-{mode}"
    page.wait_for_selector(f"{sel}[data-ready]", state="attached", timeout=60000)
    assert page.get_attribute(sel, "data-ready") == "1", page.inner_text(sel)
    assert page.is_visible(sel) and page.inner_text(sel).strip()
    assert page.evaluate("document.body.dataset.mode") == mode
    assert errors == []
    page.close()


def test_pages_build_has_no_edit_controls(browser, pages_base, studio_base):
    page = browser.new_page()
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto(pages_base)
    page.wait_for_selector('#mode-designs[data-ready="1"]', timeout=60000)
    assert page.locator("[data-edit]").count() == 0
    assert page.locator("#modes button").count() == 5
    assert "studio" not in page.evaluate("fetch('data/index.json').then(r => r.json())")
    assert not any("modes/edit.js" in u for u in requests)
    assert page.locator('[data-testid="btn-edit"], [data-testid="btn-validate"], [data-testid="btn-propose"], [data-testid="save"]').count() == 0
    page.goto(studio_base)
    page.wait_for_selector("[data-edit]", timeout=30000)
    assert page.locator("[data-edit]").count() > 0
    page.wait_for_selector('[data-testid="btn-validate"]', timeout=30000)
    assert page.locator('[data-testid="btn-propose"]').count() == 1
    assert page.evaluate("document.title") == "Plane Studio"
    page.close()


def test_studio_edit_save_validate_propose(browser, studio_base, monkeypatch):
    from hangar.ops import edit as edit_ops
    calls = []
    URL = "https://github.com/davinciucberkeley-collab/dbf-hangar/pull/999"

    def fake_run(argv, cwd):
        calls.append(list(argv))
        if "--show-toplevel" in argv:
            return str(Path(cwd).parent)
        if "status" in argv:
            return " M plane.yaml\n"
        if "--abbrev-ref" in argv:
            return "main\n"
        if "pr" in argv and "create" in argv:
            return URL + "\n"
        return ""
    monkeypatch.setattr(edit_ops, "_run", fake_run)

    page = browser.new_page()
    errors = collect(page)
    page.goto(studio_base + "#m=designs&d=example-tailsitter-wing")
    page.wait_for_selector('#mode-designs[data-ready="1"]', timeout=60000)
    page.wait_for_selector('[data-testid="btn-validate"]:not([disabled])', timeout=120000)

    # edit one field, first without a why (refused), then with one
    page.click('[data-testid="btn-edit"]')
    page.get_by_role("button", name="Parts", exact=True).click()
    page.fill('tr[data-q^="wing wing"] input.sm', "185")
    page.select_option('[data-testid="save-kind"]', "subtract")
    page.click('[data-testid="save"]')
    page.wait_for_selector(".dlg-err:not([hidden])", timeout=30000)
    assert page.inner_text(".dlg-err") == "Say why in one line."
    page.fill('[data-testid="save-why"]', "lighter foam")
    page.click('[data-testid="save"]')
    page.wait_for_selector("dialog.dlg", state="detached", timeout=30000)

    ddir = studio.DESIGNS_DIR / "example-tailsitter-wing"
    assert "mass_g: 185" in (ddir / "plane.yaml").read_text()
    log = yaml.safe_load((ddir / "CHANGELOG.yaml").read_text())
    assert log[-1]["key"] == "components[wing].mass_g"
    assert log[-1]["why"] == "lighter foam" and log[-1]["kind"] == "subtract"

    # wait for the re-check, then validate
    t0 = time.time()
    while time.time() - t0 < 240:
        with urllib.request.urlopen(studio_base + "api/state", timeout=60) as r:
            if not json.loads(r.read())["busy"]:
                break
        time.sleep(0.3)
    else:
        raise AssertionError("studio jobs did not finish")
    page.wait_for_selector('[data-testid="btn-validate"]:not([disabled])', timeout=120000)
    page.click('[data-testid="btn-validate"]')
    page.wait_for_selector('[data-testid="validate-result"] .result', timeout=120000)
    req = urllib.request.Request(studio_base + "api/op/design.validate",
                                 data=json.dumps({"path": str(ddir)}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        body = e.read()
    card = json.loads(body)["data"]
    expected = {(r["check_id"], r["status"]) for t in card["tiers"] for r in t["results"]}
    actual = page.eval_on_selector_all(
        '[data-testid="validate-result"] .result',
        "els => els.map(e => [e.querySelector('.cid').textContent, e.querySelector('.badge').textContent, e.className.split(' ')[1]])")
    assert {(c, s) for c, s, _ in actual} == expected
    assert all(s == cls for _, s, cls in actual), "each row must show its own status"
    assert page.inner_text('[data-testid="validate-result"] h3').startswith("Validation:")

    # propose a pull request (git and gh are faked at _run)
    page.click('[data-testid="btn-propose"]')
    assert page.input_value('[data-testid="propose-title"]') == "Edit example-tailsitter-wing"
    page.fill('[data-testid="propose-title"]', "Lighter wing foam")
    page.click('[data-testid="propose-go"]')
    page.wait_for_selector('a[data-testid="pr-link"]', timeout=30000)
    assert page.get_attribute('a[data-testid="pr-link"]', "href") == URL
    assert page.inner_text('a[data-testid="pr-link"]') == URL
    assert any(c[-2:] == ["design/example-tailsitter-wing/lighter-wing-foam"]
               or ("switch" in c and "-c" in c and "design/example-tailsitter-wing/lighter-wing-foam" in c) for c in calls)
    assert any("--title" in c and c[c.index("--title") + 1] == "Lighter wing foam" for c in calls)
    assert errors == []
    page.close()


def test_timeline_plays_mechanism_sweep(browser, pages_base):
    page = browser.new_page()
    errors = collect(page)
    page.goto(f"{pages_base}#m=designs&d=mech-good")
    page.wait_for_selector('#mode-designs[data-ready="1"]', timeout=60000)
    assert page.inner_text('[data-follower="flap_hinge"]') == "0.0"
    assert page.inner_text('[data-testid="tl-input"]') == "0"
    before = page.locator("#vp-main canvas").screenshot()
    page.click('[data-testid="tl-play"]')
    page.wait_for_function("document.querySelector('[data-testid=tl-input]').textContent === '20'", timeout=15000)
    assert page.inner_text('[data-follower="flap_hinge"]') == "20.0"
    assert page.input_value('[data-testid="tl-scrub"]') == "20"
    after = page.locator("#vp-main canvas").screenshot()
    assert before != after
    assert errors == []
    page.close()


def _wait_studio_idle(base, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        with urllib.request.urlopen(base + "api/state", timeout=60) as r:
            if not json.loads(r.read())["busy"]:
                return
        time.sleep(0.3)
    raise AssertionError("studio jobs did not finish")


def test_propose_link_survives_real_git_side_effects(browser, concept_a_studio, monkeypatch):
    # Real git does two things the mocked test above does not: switching back to main rewrites plane.yaml to
    # main's version (so the design changes on disk and gets re-checked), and gh prints progress before the URL.
    from hangar.ops import edit as edit_ops
    URL = "https://github.com/davinciucberkeley-collab/dbf-hangar/pull/1"
    plane = studio.DESIGNS_DIR / "concept-a" / "plane.yaml"
    main_text = plane.read_text()  # the committed file; git restores it when we switch back to main

    def fake_run(argv, cwd):
        if "--show-toplevel" in argv:
            return str(Path(cwd).parent)
        if "status" in argv:
            return " M plane.yaml\n"
        if "--abbrev-ref" in argv:
            return "main\n"
        if "switch" in argv and "-c" in argv:
            return ""
        if "switch" in argv:
            time.sleep(2)
            plane.write_text(main_text)
            return ""
        if "pr" in argv and "create" in argv:
            time.sleep(4)  # gh talks to GitHub: seconds, while the poll loop keeps running
            return ("Creating pull request for design/concept-a/avionics-plate-mass into main "
                    f"in davinciucberkeley-collab/dbf-hangar\n\n{URL}\n")
        return ""
    monkeypatch.setattr(edit_ops, "_run", fake_run)

    page = browser.new_page()
    errors = collect(page)
    page.goto(concept_a_studio + "#m=designs&d=concept-a")
    page.wait_for_selector('#mode-designs[data-ready="1"]', timeout=60000)
    page.wait_for_selector('[data-testid="btn-validate"]:not([disabled])', timeout=240000)
    page.click('[data-testid="btn-edit"]')
    page.get_by_role("button", name="Parts", exact=True).click()
    page.fill('tr[data-q^="avn-001"] input.sm', "10")
    page.fill('[data-testid="save-why"]', "heavier plate")
    page.click('[data-testid="save"]')
    page.wait_for_selector("dialog.dlg", state="detached", timeout=30000)
    _wait_studio_idle(concept_a_studio)
    page.wait_for_selector('[data-testid="btn-validate"]:not([disabled])', timeout=240000)
    page.click('[data-testid="btn-validate"]')
    page.wait_for_selector('[data-testid="validate-result"]', timeout=240000)
    page.wait_for_selector('[data-testid="btn-propose"]', timeout=60000)

    page.click('[data-testid="btn-propose"]')
    page.fill('[data-testid="propose-title"]', "Avionics plate mass")
    page.click('[data-testid="propose-go"]')
    page.wait_for_selector('a[data-testid="pr-link"]', timeout=30000)
    expect(page.locator('[data-testid="pr-result"]')).to_be_in_viewport()
    assert page.get_attribute('a[data-testid="pr-link"]', "href") == URL
    assert page.locator(f'#toasts a[href="{URL}"]').count() == 1
    # the PR panel sits above the long validation list
    assert page.evaluate(
        "() => !!(document.querySelector('[data-testid=pr-result]').compareDocumentPosition("
        "document.querySelector('[data-testid=validate-result]')) & Node.DOCUMENT_POSITION_FOLLOWING)")
    page.wait_for_timeout(6000)  # longer than a normal toast lasts: a toast with a link must stay

    _wait_studio_idle(concept_a_studio)  # the revert triggers a re-check; the link must stay
    page.wait_for_selector('[data-testid="btn-validate"]:not([disabled])', timeout=240000)
    assert page.get_attribute('a[data-testid="pr-link"]', "href") == URL
    expect(page.locator('[data-testid="pr-result"]')).to_be_in_viewport()
    assert page.locator(f'#toasts a[href="{URL}"]').count() == 1
    assert errors == []
    page.close()


def test_test_servers_listen_with_a_large_backlog():
    httpd = _serve(SimpleHTTPRequestHandler)
    try:
        assert httpd.request_queue_size >= 64
    finally:
        httpd.shutdown()
        httpd.server_close()
