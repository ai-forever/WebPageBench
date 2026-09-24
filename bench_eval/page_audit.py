"""Layout and asset checks for Playwright bench UI audits."""

from __future__ import annotations

from pathlib import Path
from typing import Any

SCREENSHOT_DIR = Path(__file__).resolve().parents[1] / "tests" / "bench" / "build" / "audit-screenshots"

SKIP_RESOURCE_HOSTS = (
    "google-analytics.com",
    "googletagmanager.com",
    "doubleclick.net",
)


def screenshot(page, name: str, *, full_page: bool = False) -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    return path


def attach_network_listeners(page) -> dict[str, list[str]]:
    """Record failed image/font/css/media responses on the page."""
    bag: dict[str, list[str]] = {"failed": [], "http_error": []}

    def on_failed(req):
        rtype = req.resource_type
        if rtype not in ("image", "font", "stylesheet", "media"):
            return
        url = req.url or ""
        if any(host in url for host in SKIP_RESOURCE_HOSTS):
            return
        bag["failed"].append(f"{rtype} {url} {req.failure}")

    def on_response(resp):
        rtype = resp.request.resource_type
        if rtype not in ("image", "font", "stylesheet", "media"):
            return
        url = resp.url or ""
        if any(host in url for host in SKIP_RESOURCE_HOSTS):
            return
        if resp.status >= 400:
            bag["http_error"].append(f"{resp.status} {rtype} {url}")

    page.on("requestfailed", on_failed)
    page.on("response", on_response)
    return bag


def inspect_images(page) -> list[dict[str, Any]]:
    return page.evaluate(
        """() => {
            const out = [];
            for (const img of document.querySelectorAll('img')) {
                const src = img.currentSrc || img.src || '';
                if (!src || src.startsWith('data:')) continue;
                const rect = img.getBoundingClientRect();
                const visible = rect.width > 1 && rect.height > 1;
                out.push({
                    src,
                    alt: img.alt || '',
                    complete: img.complete,
                    naturalWidth: img.naturalWidth || 0,
                    naturalHeight: img.naturalHeight || 0,
                    visible,
                });
            }
            return out;
        }"""
    )


def broken_visible_images(page) -> list[dict[str, Any]]:
    return [
        img
        for img in inspect_images(page)
        if img.get("visible") and (not img.get("complete") or img.get("naturalWidth", 0) <= 0)
    ]


def page_overflow(page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
            const de = document.documentElement;
            const body = document.body;
            return {
                clientWidth: de.clientWidth,
                scrollWidth: Math.max(de.scrollWidth, body ? body.scrollWidth : 0),
                clientHeight: de.clientHeight,
                scrollHeight: Math.max(de.scrollHeight, body ? body.scrollHeight : 0),
            };
        }"""
    )


def assert_no_horizontal_overflow(page, *, label: str = "page") -> None:
    metrics = page_overflow(page)
    extra = metrics["scrollWidth"] - metrics["clientWidth"]
    assert extra <= 2, f"{label}: horizontal overflow {extra}px ({metrics})"


def rects_overlap(a: dict[str, float], b: dict[str, float], *, slack: float = 2.0) -> bool:
    return not (
        a["x"] + a["w"] <= b["x"] + slack
        or b["x"] + b["w"] <= a["x"] + slack
        or a["y"] + a["h"] <= b["y"] + slack
        or b["y"] + b["h"] <= a["y"] + slack
    )


def element_rect(page, selector: str) -> dict[str, float] | None:
    loc = page.locator(selector).first
    if loc.count() == 0:
        return None
    box = loc.bounding_box()
    if not box:
        return None
    return {"x": box["x"], "y": box["y"], "w": box["width"], "h": box["height"]}


def assert_pairs_do_not_overlap(page, pairs: list[tuple[str, str]], *, label: str = "") -> None:
    problems = []
    for left, right in pairs:
        a = element_rect(page, left)
        b = element_rect(page, right)
        if not a or not b:
            continue
        if a["w"] < 2 or a["h"] < 2 or b["w"] < 2 or b["h"] < 2:
            continue
        if rects_overlap(a, b):
            problems.append(f"{left} overlaps {right}: {a} vs {b}")
    assert not problems, f"{label} overlap: " + "; ".join(problems)


def hit_test_center(page, selector: str) -> dict[str, Any]:
    return page.evaluate(
        """(sel) => {
            const el = document.querySelector(sel);
            if (!el) return { ok: false, reason: 'missing' };
            const r = el.getBoundingClientRect();
            const x = r.x + r.width / 2;
            const y = r.y + r.height / 2;
            const top = document.elementFromPoint(x, y);
            const ok = !!(top && (el === top || el.contains(top) || top.contains(el)));
            return {
                ok,
                x, y,
                expected: el.tagName + '.' + (el.className || ''),
                actual: top ? (top.tagName + '.' + (top.className || '')) : null,
            };
        }""",
        selector,
    )


def assert_click_target_not_covered(page, selector: str, *, label: str = "") -> None:
    loc = page.locator(selector).first
    loc.wait_for(state="visible", timeout=15000)
    result = hit_test_center(page, selector)
    assert result.get("ok"), f"{label or selector} covered by {result.get('actual')}: {result}"


def css_background_urls(page) -> list[str]:
    return page.evaluate(
        """() => {
            const urls = [];
            const nodes = document.querySelectorAll('*');
            for (const el of nodes) {
                const bg = getComputedStyle(el).backgroundImage;
                if (!bg || bg === 'none') continue;
                const re = /url\\(["']?([^"')]+)["']?\\)/g;
                let m;
                while ((m = re.exec(bg))) {
                    const u = m[1];
                    if (u && !u.startsWith('data:')) urls.push(u);
                }
            }
            return [...new Set(urls)];
        }"""
    )


def scroll_page_to_bottom(page) -> None:
    page.evaluate(
        """async () => {
            const step = window.innerHeight || 800;
            const max = Math.min(document.documentElement.scrollHeight, 12000);
            for (let y = 0; y < max; y += step) {
                window.scrollTo(0, y);
                await new Promise(r => setTimeout(r, 80));
            }
            window.scrollTo(0, 0);
        }"""
    )


def assert_assets_ok(page, bag: dict[str, list[str]], *, label: str) -> None:
    broken = broken_visible_images(page)
    failed = bag.get("failed") or []
    http_error = bag.get("http_error") or []
    msgs = []
    if broken:
        sample = broken[:8]
        msgs.append(f"broken images: {sample}")
    if failed:
        msgs.append(f"requestfailed: {failed[:8]}")
    if http_error:
        msgs.append(f"http errors: {http_error[:8]}")
    assert not msgs, f"{label}: " + " | ".join(msgs)
