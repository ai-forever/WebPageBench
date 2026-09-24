"""Browser test for trace card navigation via gr.HTML js_on_load."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LIDERBOARD_ROOT = _REPO_ROOT / "liderboard"
if str(_LIDERBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIDERBOARD_ROOT))

from app import build_demo  # noqa: E402


def test_trace_card_opens_detail_in_browser():
    pytest = __import__("pytest")
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright
    demo, theme, css = build_demo()

    thread = threading.Thread(
        target=lambda: demo.launch(
            server_name="127.0.0.1",
            server_port=7866,
            show_error=True,
            theme=theme,
            css=css,
        ),
        daemon=True,
    )
    thread.start()
    time.sleep(8)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://127.0.0.1:7866/", wait_until="networkidle")
        time.sleep(2)
        page.get_by_role("tab", name="Traces").click()
        time.sleep(1)
        page.locator(".wab-trace-card").first.click()
        time.sleep(5)
        html = page.inner_html(".wab-traces-wrap")
        assert "wab-trace-detail-view" in html
        assert "wab-trace-split" in html
        browser.close()
