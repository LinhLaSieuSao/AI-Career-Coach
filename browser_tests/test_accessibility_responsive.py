"""Real Chromium checks for browser-only layout, keyboard, links, and reload."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Browser, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


@pytest.fixture(scope="session")
def local_app(tmp_path_factory):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"
    log_path = tmp_path_factory.mktemp("streamlit-e2e") / "streamlit.log"
    log_file = log_path.open("w", encoding="utf-8")
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    process = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", str(APP),
            "--server.address=127.0.0.1", f"--server.port={port}",
            "--server.headless=true", "--browser.gatherUsageStats=false",
        ],
        cwd=ROOT,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    try:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(f"Streamlit exited before ready:\n{log_path.read_text(encoding='utf-8')}")
            try:
                with urlopen(base_url, timeout=2) as response:
                    if response.status == 200:
                        break
            except (OSError, URLError):
                time.sleep(0.25)
        else:
            pytest.fail(f"Streamlit did not start within 45 seconds:\n{log_path.read_text(encoding='utf-8')}")
        yield base_url
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        log_file.close()


@pytest.fixture(scope="session")
def chromium() -> Browser:
    if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        local_browser_cache = ROOT.parent / ".playwright-browsers"
        if local_browser_cache.exists():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(local_browser_cache)
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as exc:  # missing platform browser is an environment setup issue
            if os.environ.get("CI"):
                pytest.fail(f"Chromium required in CI but could not start: {exc}")
            pytest.skip(f"Chromium is not installed; run `python -m playwright install chromium`: {exc}")
        yield browser
        browser.close()


@pytest.fixture
def page(chromium: Browser) -> Page:
    context = chromium.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    yield page
    context.close()


def _confirm_review_with_keyboard(page: Page) -> None:
    for _ in range(150):
        page.keyboard.press("Tab")
        focused = page.evaluate(
            """() => ({tag: document.activeElement?.tagName,
                         text: (document.activeElement?.innerText || '').trim()})"""
        )
        if focused["tag"] == "BUTTON" and "Xác nhận hồ sơ và xem kết quả" in focused["text"]:
            page.keyboard.press("Enter")
            page.get_by_role("tab", name="Tóm tắt").wait_for(timeout=15_000)
            for _ in range(150):
                page.keyboard.press("Tab")
                role_focus = page.evaluate(
                    """() => ({tag: document.activeElement?.tagName,
                                 text: (document.activeElement?.innerText || '').trim()})"""
                )
                if role_focus["tag"] == "BUTTON" and "Chọn Chuyên viên phân tích dữ liệu" in role_focus["text"]:
                    page.keyboard.press("Enter")
                    page.get_by_text("Đánh giá cho Chuyên viên phân tích dữ liệu", exact=False).wait_for(state="attached", timeout=15_000)
                    return
            pytest.fail("Tab navigation could not reach the suggested role button")
    pytest.fail("Tab navigation could not reach the profile confirmation button")


def _load_demo_results(page: Page) -> None:
    page.get_by_role("button", name="Dùng hồ sơ mẫu · Phân tích dữ liệu").click()
    page.get_by_text("Bước 2/2 · Rà soát kỹ năng và Level").wait_for(timeout=15_000)
    page.get_by_role("button", name="Xác nhận hồ sơ và xem kết quả").click()
    page.get_by_role("tab", name="Tóm tắt").wait_for(timeout=15_000)
    page.get_by_role("button", name="Chọn Chuyên viên phân tích dữ liệu").click()
    page.get_by_text("Đánh giá cho Chuyên viên phân tích dữ liệu", exact=False).wait_for(state="attached", timeout=15_000)


def test_keyboard_only_demo_flow_and_visible_focus_ring(page: Page, local_app: str):
    page.goto(local_app, wait_until="domcontentloaded")
    page.get_by_text("Bước 1/2 · Tạo hoặc nạp hồ sơ").wait_for(timeout=20_000)
    target_name = "Dùng hồ sơ mẫu · Phân tích dữ liệu"
    reached = False
    focus_style = {}
    for _ in range(120):
        page.keyboard.press("Tab")
        focus = page.evaluate(
            """() => {
                const el = document.activeElement;
                const s = getComputedStyle(el);
                return {tag: el?.tagName, text: (el?.innerText || '').trim(),
                        outlineStyle: s.outlineStyle, outlineWidth: s.outlineWidth,
                        boxShadow: s.boxShadow, matchesVisible: el?.matches(':focus-visible')};
            }"""
        )
        if focus["tag"] == "BUTTON" and target_name in focus["text"]:
            focus_style = focus
            page.keyboard.press("Enter")
            reached = True
            break
    assert reached, "The primary demo button was not reachable with Tab."
    assert focus_style["matchesVisible"] or focus_style["outlineWidth"] != "0px" or focus_style["boxShadow"] != "none", focus_style
    page.get_by_text("Bước 2/2 · Rà soát kỹ năng và Level").wait_for(timeout=15_000)
    _confirm_review_with_keyboard(page)
    for tab_name in ("Tóm tắt", "Khoảng cách", "Lộ trình", "Tài liệu", "Phỏng vấn"):
        assert page.get_by_role("tab", name=tab_name).count() == 1


def test_mobile_and_zoomed_layout_has_no_document_level_horizontal_overflow(page: Page, local_app: str):
    page.goto(local_app, wait_until="domcontentloaded")
    page.get_by_text("Bước 1/2 · Tạo hoặc nạp hồ sơ").wait_for(timeout=20_000)
    measurements = []
    for width in (375, 414):
        page.set_viewport_size({"width": width, "height": 850})
        page.evaluate("window.dispatchEvent(new Event('resize'))")
        measurements.append(page.evaluate(
            """() => ({viewport: document.documentElement.clientWidth,
                         document: document.documentElement.scrollWidth,
                         body: document.body.scrollWidth})"""
        ))
    assert all(max(item["document"], item["body"]) <= item["viewport"] + 1 for item in measurements), measurements

    _load_demo_results(page)
    results_measurements = []
    for width in (375, 414):
        page.set_viewport_size({"width": width, "height": 850})
        page.evaluate("window.dispatchEvent(new Event('resize'))")
        results_measurements.append(page.evaluate(
            """() => ({viewport: document.documentElement.clientWidth,
                         document: document.documentElement.scrollWidth,
                         body: document.body.scrollWidth})"""
        ))
    assert all(max(item["document"], item["body"]) <= item["viewport"] + 1 for item in results_measurements), results_measurements

    page.set_viewport_size({"width": 800, "height": 900})
    page.evaluate("document.documentElement.style.zoom = '200%'")
    zoomed = page.evaluate(
        """() => ({viewport: document.documentElement.clientWidth,
                     document: document.documentElement.scrollWidth,
                     body: document.body.scrollWidth})"""
    )
    assert max(zoomed["document"], zoomed["body"]) <= zoomed["viewport"] + 1, zoomed
    print({"landing_375_414": measurements, "results_375_414": results_measurements, "zoom_200": zoomed})


def test_reload_recovers_app_and_resource_links_are_safe_new_tabs(page: Page, local_app: str):
    page.goto(local_app, wait_until="domcontentloaded")
    _load_demo_results(page)
    page.get_by_role("tab", name="Tài liệu").click()
    external_links = page.locator("main a[href^='http']")
    external_link_count = external_links.count()
    assert external_link_count > 0, "The selected demo did not render any external learning links."
    bad_links = []
    for index in range(external_links.count()):
        link = external_links.nth(index)
        attributes = link.evaluate("el => ({href: el.href, target: el.target, rel: el.rel})")
        rel_values = set(attributes["rel"].casefold().split())
        if attributes["target"] != "_blank" or not {"noopener", "noreferrer"} <= rel_values:
            bad_links.append(attributes)
    assert not bad_links, bad_links

    page.reload(wait_until="domcontentloaded")
    page.get_by_text("AI Career Coach").wait_for(timeout=20_000)
    assert not page.get_by_text("Exception", exact=False).count()
    print({"external_learning_links": external_link_count, "bad_target_rel_pairs": len(bad_links), "reload": "passed"})


def test_live_roadmap_discloses_pending_level_scope(page: Page, local_app: str):
    page.goto(local_app, wait_until="domcontentloaded")
    _load_demo_results(page)
    page.get_by_role("tab", name="Tài liệu").click()
    page.locator('main p:visible').filter(has_text="Level do dự án gán cho mapping").first.wait_for(timeout=15_000)
    page.locator('main p:visible').filter(has_text="Chưa xác định đủ bài học/mục cụ thể").first.wait_for(timeout=15_000)


def test_axe_reports_no_critical_or_serious_violations(page: Page, local_app: str):
    page.goto(local_app, wait_until="domcontentloaded")
    page.get_by_text("Bước 1/2 · Tạo hoặc nạp hồ sơ").wait_for(timeout=20_000)
    violations = []
    for stage in ("landing", "results"):
        page.wait_for_timeout(500)
        result = Axe().run(page)
        violations.extend(
            {"stage": stage, "id": item["id"], "impact": item["impact"], "help": item["help"],
             "nodes": [
                 {"target": node["target"], "html": node["html"], "failureSummary": node.get("failureSummary")}
                 for node in item["nodes"]
             ]}
            for item in result.response["violations"]
        )
        if stage == "landing":
            _load_demo_results(page)
    severe = [item for item in violations if item["impact"] in {"critical", "serious"}]
    print({"axe_total_violations_landing_and_results": len(violations), "severe": len(severe)})
    print({"non_severe": [(item["stage"], item["id"], item["impact"], len(item["nodes"]))
                           for item in violations if item["impact"] not in {"critical", "serious"}]})
    if violations:
        print(ascii([{"stage": item["stage"], "id": item["id"], "nodes": item["nodes"]}
                     for item in violations if item["impact"] not in {"critical", "serious"}]))
    if severe:
        print(ascii(severe))
    assert not severe, severe


def test_manual_profile_negation_and_duplicate_custom_skill(page: Page, local_app: str):
    """A real form submission must not claim negated experience or crash on duplicates."""
    page.goto(local_app, wait_until="domcontentloaded")
    page.get_by_text("Bước 1/2 · Tạo hoặc nạp hồ sơ").wait_for(timeout=20_000)
    page.get_by_label("Kỹ năng bạn muốn đưa vào hồ sơ (*)").fill("Python 3.12; SQL")
    page.get_by_label("Kinh nghiệm (không bắt buộc)").fill(
        "Đã dùng Python và SQL để tổng hợp báo cáo, chưa sử dụng Docker."
    )
    page.get_by_role("button", name="Tiếp tục rà soát hồ sơ").click()
    page.get_by_text("Bước 2/2 · Rà soát kỹ năng và Level").wait_for(timeout=15_000)
    assert page.get_by_role("button", name="Remove docker").count() == 0

    page.get_by_label("Thêm hoặc sửa tên kỹ năng khác (không bắt buộc)").fill("Docker; SQL")
    page.get_by_text("Bước 2/2 · Rà soát kỹ năng và Level").click()
    page.get_by_role("combobox", name="Level · Docker").wait_for(timeout=15_000)
    assert page.get_by_role("combobox", name="Level · sql").count() == 1
    page.get_by_role("button", name="Xác nhận hồ sơ và xem kết quả").click()
    page.get_by_role("tab", name="Tóm tắt").wait_for(timeout=15_000)
    assert not page.get_by_text("StreamlitDuplicateElementKey").count()
    assert page.get_by_text("Kỹ năng:  docker, python, sql").count() == 1
