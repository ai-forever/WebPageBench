"""Shared helpers for Playwright UI tests against the unified bench."""

from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from bench_eval.bench_verify import BENCH_TESTS_DIR, merge
from bench_eval.task_dates import apply_booking_dates, booking_iso_pair
from lib.src.agent_bench import client

FRONTEND_URL = os.environ.get("BENCH_FRONTEND_URL", "http://127.0.0.1:5173")
API_ADDRESS = os.environ.get("BENCH_API_ADDRESS", os.environ.get("EVAL_API_ADDRESS", "localhost:9000"))
API_URL = f"http://{API_ADDRESS.rsplit(':', 1)[0]}:{API_ADDRESS.rsplit(':', 1)[-1]}"


def services_reachable(timeout: float = 0.5) -> bool:
    host, _, port_str = API_ADDRESS.partition(":")
    port = int(port_str or "9000")
    try:
        with socket.create_connection((host or "127.0.0.1", port), timeout=timeout):
            pass
    except OSError:
        return False
    try:
        with socket.create_connection(
            ("127.0.0.1", int(FRONTEND_URL.rsplit(":", 1)[-1].rstrip("/"))),
            timeout=timeout,
        ):
            pass
    except OSError:
        return False
    return True


def create_track(track_id: str, task_stem: str = "hotel_search_scenario") -> str:
    """Create or replace a bench track merged with a task; returns track_id."""
    task_file = BENCH_TESTS_DIR / "tasks" / f"{task_stem}.json"
    base = json.loads((BENCH_TESTS_DIR / "config.json").read_text(encoding="utf-8"))
    task = json.loads(task_file.read_text(encoding="utf-8"))
    cfg = merge(base, task)
    apply_booking_dates(cfg)
    cfg["test_data"]["test_name"] = task_stem
    build = BENCH_TESTS_DIR / "build" / f"{track_id}.json"
    build.parent.mkdir(parents=True, exist_ok=True)
    build.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    client.create_track(
        name=track_id,
        id=track_id,
        filepath=str(build),
        address=API_ADDRESS,
        delete_existing=True,
    )
    return track_id


def create_base_track(track_id: str) -> str:
    """Create or replace a bench track from base config only (no task merge)."""
    base = json.loads((BENCH_TESTS_DIR / "config.json").read_text(encoding="utf-8"))
    build = BENCH_TESTS_DIR / "build" / f"{track_id}.json"
    build.parent.mkdir(parents=True, exist_ok=True)
    build.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
    client.create_track(
        name=track_id,
        id=track_id,
        filepath=str(build),
        address=API_ADDRESS,
        delete_existing=True,
    )
    return track_id


def page_url(
    track_id: str,
    state_id: str,
    view_type: str,
    query: dict[str, str] | None = None,
) -> str:
    base = f"{FRONTEND_URL.rstrip('/')}/{track_id}/{state_id}/{view_type}"
    if query:
        return f"{base}?{urlencode(query)}"
    return base


_HOTEL_CHECK_IN, _HOTEL_CHECK_OUT = booking_iso_pair(14, 5)

HOTEL_SEARCH_QUERY = {
    "dataset": "ch",
    "cityId": "ch-zrh",
    "dest": "Цюрих, Швейцария",
    "checkIn": _HOTEL_CHECK_IN,
    "checkOut": _HOTEL_CHECK_OUT,
    "rooms": "1",
    "guests": "2",
    "children": "0",
}


def hotel_main_url(track_id: str) -> str:
    return page_url(track_id, "state_hotels_main", "bench_hotel_main")


def hotel_search_url(track_id: str, extra: dict[str, str] | None = None) -> str:
    q = {**HOTEL_SEARCH_QUERY, **(extra or {})}
    return page_url(track_id, "state_hotels_search", "bench_hotel_search", q)


def hotel_detail_url(track_id: str, hotel_id: str = "h-ch-zrh-lakeside-grand") -> str:
    q = {**HOTEL_SEARCH_QUERY, "hotelId": hotel_id}
    return page_url(track_id, "state_hotels_hotel", "bench_hotel_hotel", q)


def grocery_main_url(track_id: str) -> str:
    return page_url(track_id, "state_grocery_main", "bench_grocery_main")


def grocery_catalog_url(track_id: str) -> str:
    return page_url(track_id, "state_grocery_catalog", "bench_grocery_catalog")


def grocery_basket_url(track_id: str) -> str:
    return page_url(track_id, "state_grocery_basket", "bench_grocery_basket")


def grocery_category_url(track_id: str, state_id: str) -> str:
    return page_url(track_id, state_id, "bench_grocery_category")


def files_cabinet_url(track_id: str) -> str:
    return page_url(track_id, "state_files_main", "bench_files_cabinet")


def files_collection_url(track_id: str, collection: str = "lab_reports") -> str:
    return page_url(
        track_id,
        "state_files_collection",
        "bench_files_collection",
        {"collection": collection},
    )


def wait_files_ready(page, timeout: int = 15000) -> None:
    page.locator(".bench-files").first.wait_for(state="visible", timeout=timeout)


def goto_files_via_hub(page, track_id: str) -> None:
    page.goto(page_url(track_id, "state_hub", "bench_hub"), wait_until="networkidle")
    page.wait_for_selector(".bench-top-nav__link", state="visible")
    page.locator(".bench-top-nav__link").filter(has_text="Файлы").first.click()
    page.wait_for_url("**/bench_files_cabinet", timeout=15000)
    wait_files_ready(page)


def menu_bar(page):
    return page.locator(".menu-bar").first


def bbox(locator) -> dict[str, float] | None:
    return locator.bounding_box()


def assert_position_stable(
    before: dict[str, float] | None,
    after: dict[str, float] | None,
    *,
    tolerance: float = 3.0,
    label: str = "element",
) -> None:
    assert before is not None, f"{label}: missing initial bounding box"
    assert after is not None, f"{label}: missing bounding box after action"
    dx = abs(before["x"] - after["x"])
    dy = abs(before["y"] - after["y"])
    assert dx <= tolerance, f"{label}: horizontal shift {dx}px (>{tolerance})"
    assert dy <= tolerance, f"{label}: vertical shift {dy}px (>{tolerance})"


def collect_js_errors(page) -> list[str]:
    errors: list[str] = []

    def _on_error(err):
        errors.append(str(err))

    page.on("pageerror", _on_error)
    return errors


def get_track_events(track_id: str) -> list[dict[str, Any]]:
    resp = requests.post(f"{API_URL}/event/get", data={"track_id": track_id}, timeout=10)
    resp.raise_for_status()
    return resp.json().get("events", [])


def event_names(track_id: str) -> list[str]:
    return [e.get("event_name", "") for e in get_track_events(track_id)]


def wait_event(track_id: str, event_name: str, timeout_ms: int = 8000) -> None:
    """Poll POST /event/get until event_name appears. Timeout budget, not a busy-loop."""
    deadline = time.monotonic() + timeout_ms / 1000
    interval = 0.15
    while time.monotonic() < deadline:
        names = event_names(track_id)
        if event_name in names:
            return
        time.sleep(interval)
        interval = min(interval * 1.4, 0.5)
    raise AssertionError(
        f"Timed out after {timeout_ms}ms waiting for {event_name!r}; got {event_names(track_id)}"
    )


def wait_hotels_ready(page, timeout: int = 15000) -> None:
    page.locator(".bench-hotels, .bench-hotels").first.wait_for(state="visible", timeout=timeout)


def bench_nav(page):
    return page.locator(".bench-top-nav")


def hotel_header_widgets(page):
    return page.locator(".bench-hotels .widgets").first


def dismiss_shop_popup(page, timeout: int = 2000) -> bool:
    """Close the «Маркет» first-visit address prompt if it is showing.

    While open, its `.popup-backdrop` is full-screen and intercepts pointer
    events for the whole page — including the bench top nav — so any test that
    navigates away from «Маркет» must dismiss it first (as an agent would).
    Returns True when a backdrop was actually dismissed.
    """
    backdrop = page.locator(".popup-backdrop")
    try:
        if backdrop.count() == 0:
            backdrop.first.wait_for(state="visible", timeout=min(timeout, 600))
    except Exception:
        return False
    if not backdrop.count():
        return False
    backdrop.first.click(force=True)
    backdrop.first.wait_for(state="hidden", timeout=timeout)
    return True


def header_metrics(page) -> dict:
    return page.evaluate(
        """() => {
            const rect = (el) => {
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return { top: r.top, left: r.left, width: r.width, height: r.height };
            };
            return {
                nav: rect(document.querySelector('.bench-files__nav')),
                bench: rect(document.querySelector('.bench-top-nav__inner')),
                navLinks: document.querySelectorAll('.bench-files__nav-btn').length,
                root: document.querySelector('.bench-files') !== null,
            };
        }"""
    )


def normalize_rect(rect: dict | None) -> dict | None:
    if not rect:
        return None
    if "top" in rect:
        return rect
    if "x" in rect and "y" in rect:
        return {
            "top": rect["y"],
            "left": rect["x"],
            "width": rect["width"],
            "height": rect["height"],
        }
    return rect


def assert_rect_stable(
    baseline: dict | None,
    current: dict | None,
    *,
    label: str,
    tol: float = 2.0,
) -> None:
    baseline = normalize_rect(baseline)
    current = normalize_rect(current)
    assert baseline is not None, f"{label}: baseline rect missing"
    assert current is not None, f"{label}: current rect missing"
    for key in ("top", "left", "width", "height"):
        drift = abs(baseline[key] - current[key])
        assert drift <= tol, f"{label} {key} drift {drift}px (baseline={baseline[key]}, current={current[key]})"
