"""Playwright helpers for UI taxonomy tests (docs/UI_TAXONOMY.md)."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

import requests

from bench_eval.bench_verify import BENCH_TESTS_DIR
from bench_eval.ui_helpers import (
    API_ADDRESS,
    FRONTEND_URL,
    files_cabinet_url,
    hotel_main_url,
    page_url,
    wait_files_ready,
)
from bench_eval.ui_helpers import dismiss_shop_popup as _dismiss_shop_popup

from rail_ui_helpers import (
    rail_url,
    seed_booking_session,
    seed_checkout_ticket,
    wait_rail_ready,
)

CARD_DATA = {
    "number": "4000060000000006",
    "date": "10/35",
    "cvv": "102",
}


def make_taxonomy_track() -> str:
    """Create a fresh bench track with auto-login disabled for AUTH tests."""
    return make_variant_track()


def make_variant_track(profile: str | None = None, *, overlay: dict | None = None) -> str:
    """Create a bench track, optionally with a UI variant profile from tests/bench/configs/."""
    from lib.src.agent_bench import client

    from ui_variant_profiles import build_variant_config, load_variant_overlay

    track_id = f"ui_taxonomy_{uuid.uuid4().hex[:10]}"
    if profile:
        overlay_data = load_variant_overlay(BENCH_TESTS_DIR / "configs" / f"{profile}.json")
    elif overlay:
        overlay_data = overlay
    else:
        overlay_data = {}

    base = build_variant_config(overlay_data)
    base.setdefault("test_data", {})["is_login"] = False
    if profile:
        base["test_data"]["ui_variant_profile"] = profile

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


def track_base(track_id: str) -> str:
    return f"{FRONTEND_URL.rstrip('/')}/{track_id}"


def hub_url(track_id: str) -> str:
    return page_url(track_id, "state_hub", "bench_hub")


def shop_main_url(track_id: str) -> str:
    return page_url(track_id, "state_shop_main", "bench_catalog_main")


BOOKS_SEARCH_QUERY = "эшвуд"


def books_main_url(track_id: str) -> str:
    return page_url(track_id, "state_books_main", "bench_books_main")


def books_search_url(track_id: str, query: str = BOOKS_SEARCH_QUERY) -> str:
    return page_url(track_id, "state_search", "bench_books_search", {"q": query})


def books_item_url(track_id: str, item_id: str = "item_51565901") -> str:
    return page_url(track_id, item_id, "bench_books_item")


def get_track_events(track_id: str) -> list[dict[str, Any]]:
    host, _, port_str = API_ADDRESS.partition(":")
    api_url = f"http://{host or '127.0.0.1'}:{port_str or '9000'}"
    resp = requests.post(f"{api_url}/event/get", data={"track_id": track_id}, timeout=10)
    resp.raise_for_status()
    return resp.json().get("events", [])


def event_names(track_id: str) -> list[str]:
    return [e.get("event_name", "") for e in get_track_events(track_id)]


def find_events(track_id: str, event_name: str) -> list[dict[str, Any]]:
    return [e for e in get_track_events(track_id) if e.get("event_name") == event_name]


def assert_has_event(track_id: str, event_name: str, **params: Any) -> None:
    events = find_events(track_id, event_name)
    assert events, f"Expected event {event_name!r}, got {event_names(track_id)}"
    if not params:
        return
    for event in events:
        data = event.get("event_data") or {}
        if isinstance(data, str):
            data = json.loads(data)
        if all(data.get(key) == value for key, value in params.items()):
            return
    sample = [e.get("event_data") for e in events[-3:]]
    raise AssertionError(f"No {event_name!r} matching {params}. Recent payloads: {sample}")


def wait_shop_ready(page, timeout: int = 30000) -> None:
    page.locator(".bench-market").first.wait_for(state="visible", timeout=timeout)
    page.locator(".cards .card, .fav-btn").first.wait_for(state="visible", timeout=timeout)


def wait_books_ready(page, timeout: int = 30000) -> None:
    page.locator(".bench-books.bench-books, .bench-books").first.wait_for(state="visible", timeout=timeout)
    page.locator(".searchbar .search-input").first.wait_for(state="visible", timeout=timeout)


def pause(page, ms: int = 1200) -> None:
    page.wait_for_timeout(ms)


def dismiss_shop_popup(page) -> None:
    _dismiss_shop_popup(page)


def goto_shop_via_hub(page, track_id: str) -> None:
    page.goto(hub_url(track_id), wait_until="networkidle")
    page.wait_for_selector(".bench-hub__card", state="visible")
    page.locator(".bench-hub__card").filter(has_text="Маркет").first.click()
    page.wait_for_url(re.compile(r"bench_catalog_main"), timeout=20000)
    wait_shop_ready(page)
    dismiss_shop_popup(page)
    pause(page)


def goto_files_via_hub(page, track_id: str) -> None:
    from bench_eval.ui_helpers import goto_files_via_hub as _goto

    _goto(page, track_id)
    pause(page)


def nav_hub_card(page, track_id: str, label: str) -> None:
    page.goto(hub_url(track_id), wait_until="networkidle")
    page.wait_for_selector(".bench-hub__card", state="visible")
    page.locator(".bench-hub__card").filter(has_text=label).first.click()
    page.wait_for_url(re.compile(r"bench_(catalog|books|grocery|rail|hotel|files)_"), timeout=20000)
    page.wait_for_load_state("networkidle")
    pause(page, 800)


def nav_top_link(page, label: str) -> None:
    page.locator(".bench-top-nav__link").filter(has_text=label).first.click()
    page.wait_for_load_state("networkidle")
    pause(page)


def fill_books_search(page, query: str) -> None:
    field = page.locator(".searchbar .search-input input").first
    field.click()
    field.fill(query)
    page.locator(".searchbar .search-btn").first.click()
    pause(page)


def select_rail_station(page, field: str, name: str) -> None:
    index = 0 if field == "from" else 1
    widget = page.locator(".rail-search-widget .station-field").nth(index)
    widget.locator("input").click()
    widget.locator("input").fill(name[:4])
    item = page.locator(".dropdown-item").filter(has_text=name).first
    item.wait_for(state="visible", timeout=10000)
    item.click()
    pause(page, 1000)


def select_rail_departure_date(page, *, complete: bool = True) -> None:
    picker = page.locator(".datepicker-container")
    if not picker.count() or not picker.first.is_visible():
        page.locator(".date-field .field-inner").first.click()
    enabled = page.locator(".datepicker-container .day-cell:not(.disabled):not(.empty) .day-number")
    enabled.first.wait_for(state="visible", timeout=10000)
    enabled.first.click()
    pause(page, 400)
    if not complete:
        pause(page)
        return
    no_return = page.locator(".no-return-btn, button:has-text('Обратный билет не нужен')")
    if no_return.count():
        no_return.first.click()
    else:
        enabled.nth(min(3, max(0, enabled.count() - 1))).click()
    pause(page)


def close_rail_passengers_if_open(page) -> None:
    if page.locator(".rail-passengers-dropdown").count():
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)


def submit_rail_search(page) -> None:
    close_rail_passengers_if_open(page)
    page.locator(".rail-search-widget .search-btn").click()
    page.wait_for_url(re.compile(r"bench_rail_search"), timeout=15000)
    wait_rail_ready(page)
    pause(page)


def select_hotel_city(page, query: str = "Лион") -> None:
    dest = page.locator(".controlDestination input").first
    dest.click()
    dest.fill(query)
    page.locator(".opt").first.wait_for(state="visible", timeout=10000)
    page.locator(".opt").first.click()
    pause(page)


def select_hotel_dates(page) -> None:
    page.locator(".controlDates .cell.left, .controlDates button").first.click()
    days = page.locator(".dayBtn:not([disabled])")
    days.nth(10).click()
    days.nth(14).click()
    pause(page)


def select_hotel_guests(page) -> None:
    page.locator(".controlGuests").first.click()
    page.locator(".doneBtn, button:has-text('Готово')").first.click()
    pause(page)


def open_shop_login(page) -> None:
    dismiss_shop_popup(page)
    page.locator(".bench-market-header .ctrl-label", has_text="Войти").click()
    page.locator(".bench-market-login-dialog").wait_for(state="visible", timeout=10000)


def open_books_login(page, track_id: str) -> None:
    page.goto(hub_url(track_id), wait_until="networkidle")
    nav_top_link(page, "Книги")
    wait_books_ready(page)
    page.locator(".searchbar .menu-btn").filter(has_text="Войти").first.click()
    page.locator(".v-dialog").first.wait_for(state="visible", timeout=10000)


def add_first_shop_item_to_basket(page, track_id: str) -> None:
    goto_shop_via_hub(page, track_id)
    page.locator(".cards .card").first.click()
    page.wait_for_url(re.compile(r"bench_catalog_item"), timeout=15000)
    page.locator("button.buy, button:has-text('Добавить в корзину')").first.click()
    pause(page)


def open_first_book_item(page, track_id: str) -> None:
    page.goto(hub_url(track_id), wait_until="networkidle")
    nav_top_link(page, "Книги")
    wait_books_ready(page)
    page.locator(".product-card").first.wait_for(state="visible", timeout=20000)
    page.locator(".product-card").first.click()
    page.wait_for_url(re.compile(r"bench_books_item"), timeout=15000)
    pause(page)


def open_rail_tariff_page(page, track_id: str) -> None:
    seed_booking_session(page, track_id)
    page.goto(rail_url(track_id, "bench_rail_tarif_selection"), wait_until="networkidle")
    wait_rail_ready(page)


def open_rail_seat_page(page, track_id: str) -> None:
    seed_booking_session(page, track_id)
    page.goto(rail_url(track_id, "bench_rail_seat_selection"), wait_until="networkidle")
    wait_rail_ready(page)


def open_rail_payment_page(page, track_id: str) -> None:
    seed_checkout_ticket(page, track_id)
    page.goto(rail_url(track_id, "bench_rail_tickets_payment"), wait_until="networkidle")
    page.wait_for_selector(".payment-gateway", timeout=20000)


def submit_rail_payment(page) -> None:
    page.locator(".input-wrap.pan input").fill(CARD_DATA["number"])
    page.locator(".input-wrap.exp input").fill(CARD_DATA["date"])
    page.locator(".input-wrap.full-name input").fill("TEST USER")
    page.locator(".input-wrap.cvv input").fill(CARD_DATA["cvv"])
    page.locator(".pay-button").click()
    pause(page, 1500)


def open_files_collection(page, track_id: str, label: str = "Отчёты лаборатории") -> None:
    page.goto(files_cabinet_url(track_id), wait_until="networkidle")
    wait_files_ready(page)
    page.get_by_role("button", name=label).click()
    page.wait_for_url(re.compile(r"bench_files_collection"), timeout=15000)
    wait_files_ready(page)
    pause(page)


def select_files_year(page, year: str = "2024") -> None:
    chip = page.locator(".bench-files__year").filter(has_text=str(year))
    if chip.count() and chip.first.is_visible():
        chip.first.click()
        pause(page)
        return
    select = page.locator(".bench-files select")
    if select.count() and select.first.is_visible():
        select.first.select_option(str(year))
        pause(page)
        return
    if chip.count():
        chip.first.click()
    elif select.count():
        select.first.select_option(str(year))
    pause(page)
