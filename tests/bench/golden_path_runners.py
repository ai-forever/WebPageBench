"""Golden-path runners: drive each tests/bench/tasks/*.json to satisfy conditions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

_BENCH_DIR = Path(__file__).resolve().parent
if str(_BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(_BENCH_DIR))
if str(_BENCH_DIR.parents[1]) not in sys.path:
    sys.path.insert(0, str(_BENCH_DIR.parents[1]))


from bench_eval.bench_verify import BENCH_TESTS_DIR
from bench_eval.task_dates import apply_booking_dates, iso_from_today
from bench_eval.ui_helpers import (
    FRONTEND_URL,
    grocery_main_url,
    hotel_main_url,
    page_url,
)
from lib.src.agent_bench import client as dab_client
from rail_ui_helpers import (
    rail_url,
    wait_rail_ready,
)
from ui_taxonomy_helpers import (
    API_ADDRESS,
    BOOKS_SEARCH_QUERY,
    books_item_url,
    books_main_url,
    close_rail_passengers_if_open,
    dismiss_shop_popup,
    fill_books_search,
    goto_shop_via_hub,
    nav_top_link,
    open_files_collection,
    pause,
    select_files_year,
    select_hotel_city,
    select_rail_station,
    shop_main_url,
    submit_rail_payment,
    wait_books_ready,
    wait_shop_ready,
)

MONTHS_RU = (
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)

def load_task(stem: str) -> dict[str, Any]:
    path = BENCH_TESTS_DIR / "tasks" / f"{stem}.json"
    task = json.loads(path.read_text(encoding="utf-8"))
    apply_booking_dates(task)
    return task


def conditions(task: dict[str, Any]) -> list[dict[str, Any]]:
    return list(task.get("test_data", {}).get("conditions") or [])


def cond_params(task: dict[str, Any], event_name: str) -> dict[str, Any]:
    for cond in conditions(task):
        if cond.get("event_name") == event_name:
            params = cond.get("parameters") or {}
            return params if isinstance(params, dict) else {}
    return {}


def all_params(task: dict[str, Any], event_name: str) -> list[dict[str, Any]]:
    out = []
    for cond in conditions(task):
        if cond.get("event_name") == event_name:
            params = cond.get("parameters") or {}
            out.append(params if isinstance(params, dict) else {})
    return out


def task_ui_variants(task: dict[str, Any]) -> dict[str, str]:
    raw = (task.get("test_data") or {}).get("ui_variants") or {}
    return {str(key): str(value) for key, value in raw.items()}


def _iso_to_ru(iso_date: str) -> str:
    year, month, day = iso_date.split("-")
    return f"{day}.{month}.{year}"


def _select_rail_station_variant(page, field: str, name: str) -> None:
    native = page.locator(".bench-rail-station-native .native-select")
    if native.count() and native.first.is_visible():
        index = 0 if field == "from" else 1
        native.nth(index).select_option(label=name)
        pause(page)
        return
    select_rail_station(page, field, name)


def assert_check_passed(track_id: str, stem: str) -> None:
    results = dab_client.check(track_id, API_ADDRESS)
    assert results is not None, f"{stem}: check() returned None"
    failed = []
    for row in results:
        if row.get("group"):
            if not row.get("group_success"):
                failed.append(row)
            continue
        if not row.get("success"):
            failed.append(row)
    assert not failed, f"{stem}: unmet conditions {failed}"


def _goto(page, url: str) -> None:
    page.goto(url, wait_until="networkidle", timeout=60000)


def _shop_item_url(track_id: str, item_id: str) -> str:
    return page_url(track_id, item_id, "bench_catalog_item")


def _open_shop_item(page, track_id: str, item_id: str) -> None:
    _goto(page, _shop_item_url(track_id, item_id))
    page.locator(".bench-market").first.wait_for(state="visible", timeout=30000)
    dismiss_shop_popup(page)
    page.locator("button.buy, button:has-text('Добавить в корзину')").first.wait_for(
        state="visible", timeout=20000
    )


def _shop_add_amount(page, amount: int) -> None:
    buy = page.locator("button.buy").first
    if buy.count():
        buy.click()
        pause(page, 400)
    else:
        page.locator("button:has-text('Добавить в корзину')").first.click()
        pause(page, 400)
    if amount <= 1:
        return
    page.locator(".qty-controls").first.wait_for(state="visible", timeout=10000)
    plus = page.locator(".qty-controls .qty-btn").last
    plus.wait_for(state="visible", timeout=10000)
    for _ in range(amount - 1):
        plus.click()
        pause(page, 250)
    qty = page.locator(".qty-value").first
    if qty.count():
        assert int(qty.inner_text().strip() or "0") >= amount, f"shop qty stayed at {qty.inner_text()!r}"


def has_cond(task: dict[str, Any], event_name: str) -> bool:
    return any(cond.get("event_name") == event_name for cond in conditions(task))


def run_shop(page, track_id: str, stem: str, task: dict[str, Any]) -> None:
    basket_rows = all_params(task, "basket_add")
    basket = basket_rows[0] if basket_rows else {}
    fav = cond_params(task, "add_favorites")
    want_fav = has_cond(task, "add_favorites")
    want_basket = has_cond(task, "basket_add")
    named_baskets = [row for row in basket_rows if row.get("item_id")]
    if want_basket and len(named_baskets) > 1:
        for row in named_baskets:
            _open_shop_item(page, track_id, str(row["item_id"]))
            _shop_add_amount(page, int(row.get("amount") or 1))
        return
    item_id = basket.get("item_id") or fav.get("item_id")
    if not item_id:
        if want_fav:
            goto_shop_via_hub(page, track_id)
            heart = page.locator(".cards .card .fav-btn").first
            heart.wait_for(state="visible", timeout=15000)
            heart.click()
            pause(page)
            return
        _goto(page, shop_main_url(track_id))
        wait_shop_ready(page)
        dismiss_shop_popup(page)
        if want_basket:
            page.locator(".cards .card").first.click()
            page.wait_for_url(re.compile(r"bench_catalog_item"), timeout=20000)
            page.locator("button.buy").first.click()
            pause(page)
        return
    _open_shop_item(page, track_id, str(item_id))
    if want_fav:
        fav_btn = page.locator(".fav-btn-static, .heart-btn, button[aria-label*='избранн']").first
        fav_btn.click()
        pause(page, 400)
    if want_basket:
        amount = int(basket.get("amount") or 1)
        _shop_add_amount(page, amount)


def run_grocery(page, track_id: str, stem: str, task: dict[str, Any]) -> None:
    _goto(page, grocery_main_url(track_id))
    page.locator(".grocery-card").first.wait_for(state="visible", timeout=20000)
    if cond_params(task, "state_changed").get("new_state") == "bench_grocery_category" or stem.startswith(
        "grocery_basket_category"
    ):
        page.locator(".menu-bar .menu-item").nth(1).click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        page.locator(".grocery-card").first.wait_for(state="visible", timeout=20000)
    item_id = cond_params(task, "basket_add").get("item_id")
    amount = int(cond_params(task, "basket_add").get("amount") or 1)
    if item_id:
        found = False
        menus = page.locator(".menu-bar .menu-item")
        for i in range(menus.count()):
            card = page.locator(f".grocery-card[data-item-id='{item_id}']")
            if card.count():
                add = card.locator(".add-button").first
                for _ in range(amount):
                    add.click()
                    pause(page, 250)
                found = True
                break
            if i + 1 < menus.count():
                menus.nth(i + 1).click()
                page.wait_for_load_state("networkidle")
                pause(page, 500)
        assert found, f"{stem}: grocery item {item_id} not found in menu categories"
    else:
        page.locator(".grocery-card .add-button").first.click()
        for _ in range(max(0, amount - 1)):
            page.locator(".grocery-card .add-button").first.click()
            pause(page, 250)
    pause(page, 400)


def _vue_push(page, *, name: str, state_id: str, track_id: str) -> bool:
    return bool(
        page.evaluate(
            """({name, stateId, trackId}) => {
              const app = document.querySelector('#app');
              const vueApp = app && app.__vue_app__;
              const router = vueApp && vueApp.config.globalProperties.$router;
              if (!router) return false;
              router.push({ name, params: { track_id: trackId, state_id: stateId } });
              return true;
            }""",
            {"name": name, "stateId": state_id, "trackId": track_id},
        )
    )


def run_books(page, track_id: str, stem: str, task: dict[str, Any]) -> None:
    item_id = (
        cond_params(task, "basket_add").get("item_id")
        or cond_params(task, "add_favorites").get("item_id")
        or cond_params(task, "state_changed").get("state_id")
    )
    if item_id:
        _goto(page, books_main_url(track_id))
        wait_books_ready(page)
        if not _vue_push(page, name="bench_books_item", state_id=str(item_id), track_id=track_id):
            _goto(page, books_item_url(track_id, str(item_id)))
        page.wait_for_url(re.compile(r"bench_books_item"), timeout=20000)
        page.locator(".buy-card").first.wait_for(state="visible", timeout=20000)
    else:
        _goto(page, books_main_url(track_id))
        wait_books_ready(page)
        fill_books_search(page, BOOKS_SEARCH_QUERY)
        page.locator(".product-card .name, .book-card .name").first.click()
        page.wait_for_url(re.compile(r"bench_books_item"), timeout=15000)
    pause(page, 400)
    if has_cond(task, "add_favorites"):
        page.locator("a.action", has_text="Отложить").first.click()
        pause(page, 400)
    if has_cond(task, "basket_add"):
        page.locator(".buy-card .secondary").first.click()
        pause(page, 400)


def _pick_rail_date(page, iso_or_dotted: str) -> None:
    iso = iso_or_dotted
    if re.match(r"\d{2}\.\d{2}\.\d{4}", iso_or_dotted):
        d, m, y = iso_or_dotted.split(".")
        iso = f"{y}-{m}-{d}"
    text_date = page.locator(".text-date-input").first
    if text_date.count() and text_date.is_visible():
        text_date.fill(_iso_to_ru(iso))
        text_date.blur()
        pause(page, 300)
        return
    native = page.locator(".native-date-input, input[type='date']").first
    if native.count() and native.is_visible():
        native.fill(iso)
        pause(page, 300)
        return
    year, month, day = iso.split("-")
    title = f"{MONTHS_RU[int(month) - 1]} {year}"
    close_rail_passengers_if_open(page)
    field = page.locator(".rail-search-widget .date-field:not(.return-date-field) .field-inner").first
    picker = page.locator(".datepicker-container")
    if not picker.count() or not picker.first.is_visible():
        field.click(force=True)
        pause(page, 300)
    if not picker.count() or not picker.first.is_visible():
        page.evaluate(
            """() => {
                const el = document.querySelector('.rail-search-widget .date-field:not(.return-date-field) .field-inner');
                if (el) el.click();
            }"""
        )
    page.locator(".datepicker-container .day-number").first.wait_for(state="visible", timeout=15000)
    for _ in range(16):
        if page.locator(".month-title").filter(has_text=title).count():
            break
        page.locator(".datepicker-header .nav-btn").last.click()
        pause(page, 200)
    month_block = page.locator(".month-block").filter(has_text=title).first
    day_num = str(int(day))
    cell = month_block.locator(".day-cell:not(.disabled):not(.empty)").filter(
        has=page.locator(".day-number").filter(has_text=re.compile(rf"^{day_num}$"))
    )
    assert cell.count(), f"rail date {iso} is missing or disabled"
    cell.first.click()
    pause(page, 400)
    no_return = page.locator(".no-return-btn")
    if no_return.count() and no_return.first.is_visible():
        no_return.first.click()
        pause(page, 300)


def _set_rail_adults(page, adults: int) -> None:
    if adults <= 1:
        return
    dropdown = page.locator(".rail-passengers-dropdown")
    if not dropdown.count() or not dropdown.first.is_visible():
        page.locator(".passengers-toggle").first.click()
        dropdown.wait_for(state="visible", timeout=8000)
    row = page.locator(".passenger-row").filter(has_text="Взрослый").first
    plus = row.locator(".counter-btn").last
    for _ in range(adults - 1):
        plus.click()
        pause(page, 150)
    close_rail_passengers_if_open(page)
    pause(page, 200)


def run_rail(page, track_id: str, stem: str, task: dict[str, Any]) -> None:
    _goto(page, rail_url(track_id, "bench_rail_main"))
    wait_rail_ready(page)
    events = [c.get("event_name") for c in conditions(task)]
    city_params = all_params(task, "select_city")
    for params in city_params:
        field = params.get("field") or params.get("direction") or "from"
        name = params.get("name") or ""
        if name:
            _select_rail_station_variant(page, str(field), str(name))
    if "select_date" in events:
        date = cond_params(task, "select_date").get("date") or iso_from_today(7)
        _pick_rail_date(page, str(date))
    seats_amount = int(cond_params(task, "select_seat").get("seats_amount") or 1)
    passenger_n = len(all_params(task, "select_passenger")) or seats_amount
    extra_passengers = re.search(r"(\d+)_passengers", stem)
    if extra_passengers:
        passenger_n = max(passenger_n, int(extra_passengers.group(1)))
        seats_amount = max(seats_amount, passenger_n)
    if passenger_n > 1:
        _set_rail_adults(page, passenger_n)
    needs_booking = any(
        name in events
        for name in (
            "select_train",
            "select_tariff",
            "select_seat",
            "select_passenger",
            "basket_add",
            "submit_payment",
        )
    )
    if "submit_search" in events or needs_booking:
        if "bench_rail_search" not in page.url:
            close_rail_passengers_if_open(page)
            if page.locator(".rail-search-widget .search-btn").count():
                page.locator(".rail-search-widget .search-btn").click()
                page.wait_for_url(re.compile(r"bench_rail_search"), timeout=20000)
                wait_rail_ready(page)
                page.locator(".train-card .buy-btn").first.wait_for(state="visible", timeout=20000)
        if needs_booking:
            tarif = cond_params(task, "select_tariff").get("tarif_name") or "Эконом"
            exact = re.compile(rf"^{re.escape(str(tarif))}$")
            if "bench_rail_search" in page.url:
                train = page.locator(".train-card").filter(
                    has=page.locator(".ticket-type", has_text=exact)
                )
                (train.first if train.count() else page.locator(".train-card").first).locator(
                    ".buy-btn"
                ).click()
                page.wait_for_url(re.compile(r"bench_rail_tarif_selection"), timeout=20000)
                wait_rail_ready(page)
            card = page.locator(".service-class-card").filter(
                has=page.locator(".class-name", has_text=exact)
            )
            (card.first if card.count() else page.locator(".service-class-card").first).click()
            pause(page, 300)
            if "select_seat" in events or "select_passenger" in events or "basket_add" in events:
                page.locator("button.continue-btn").click()
                page.wait_for_url(re.compile(r"bench_rail_seat_selection"), timeout=20000)
                wait_rail_ready(page)
                seats = page.locator(".seats-group .seat-wrapper:not(.occupied)")
                for i in range(seats_amount):
                    seats.nth(i).click()
                    pause(page, 200)
                page.locator("button.continue-btn").click()
                page.wait_for_url(re.compile(r"bench_rail_passenger_selection"), timeout=20000)
                wait_rail_ready(page)
                from rail_ui_helpers import account_owner_name

                owner = account_owner_name()
                cards = page.locator(".passenger-card")
                n_cards = max(cards.count(), 1)
                for i in range(n_cards):
                    cards.nth(i).locator(".passenger-select").click()
                    page.locator(".v-overlay-container .v-list-item", has_text=owner).first.click()
                    pause(page, 200)
                tariff_fields = page.locator(".tariff-select .v-field")
                tariff_fields.first.wait_for(state="visible", timeout=10000)
                for i in range(tariff_fields.count()):
                    tariff_fields.nth(i).click()
                    page.locator(".v-overlay-container .v-list-item").first.click()
                    pause(page, 200)
                submit = page.locator(".submit-order-btn")
                page.wait_for_function(
                    "() => { const b = document.querySelector('.submit-order-btn'); return b && !b.disabled; }",
                    timeout=10000,
                )
                submit.click()
                page.wait_for_url(re.compile(r"bench_rail_tickets_checkout"), timeout=20000)
                wait_rail_ready(page)
        if "submit_payment" in events:
            terms = page.locator(".terms-checkbox")
            for i in range(min(2, terms.count())):
                terms.nth(i).click()
                pause(page, 150)
            pay = page.locator("button, a").filter(has_text=re.compile("Оплат"))
            if pay.count():
                pay.first.click()
                page.wait_for_url(re.compile(r"bench_rail_tickets_payment"), timeout=20000)
            else:
                _goto(page, rail_url(track_id, "bench_rail_tickets_payment"))
            page.wait_for_selector(".payment-gateway", timeout=20000)
            submit_rail_payment(page)


def _pick_hotel_iso_date(page, iso_date: str) -> None:
    year, month, day = [int(part) for part in iso_date.split("-")]
    title = f"{MONTHS_RU[month - 1]} {year}"
    day_re = re.compile(rf"^{day}$")
    jumped = page.evaluate(
        """({ year, monthName }) => {
            const items = [...document.querySelectorAll('.monthItem')];
            let currentYear = null;
            for (const item of items) {
                const yearEl = item.querySelector('.mYear');
                if (yearEl && yearEl.textContent.trim()) {
                    const parsed = parseInt(yearEl.textContent.trim(), 10);
                    if (!Number.isNaN(parsed)) currentYear = parsed;
                }
                const label = (item.querySelector('.mTitle')?.textContent || '').trim();
                if (label === monthName && currentYear === year) {
                    item.click();
                    return true;
                }
            }
            return false;
        }""",
        {"year": year, "monthName": MONTHS_RU[month - 1]},
    )
    pause(page, 250)
    blocks = page.locator(".monthBlock").filter(has_text=title)
    if not blocks.count() and not jumped:
        scroller = page.locator(".gridScroll")
        for _ in range(24):
            if page.locator(".monthBlock").filter(has_text=title).count():
                break
            if scroller.count():
                scroller.evaluate("el => { el.scrollTop += 320; }")
            pause(page, 120)
        blocks = page.locator(".monthBlock").filter(has_text=title)
    assert blocks.count(), f"hotel date {iso_date} not found in calendar"
    btn = blocks.first.locator(".dayBtn:not([disabled])").filter(has_text=day_re)
    assert btn.count(), f"hotel day {iso_date} is missing or disabled"
    btn.first.click()
    pause(page, 250)


def _set_hotel_guests(page, guests: dict[str, Any], *, counter_variant: str = "rooms_popup") -> None:
    rooms = guests.get("rooms") or [{"adults": 2, "kids": []}]
    adults_total = sum(int(room.get("adults") or 2) for room in rooms)
    if counter_variant == "pill_buttons":
        n = min(max(adults_total, 1), 6)
        page.locator(".pill").filter(has_text=re.compile(rf"^{n}$")).first.click()
        pause(page, 400)
        return
    if counter_variant == "compact_select":
        n = min(max(adults_total, 1), 6)
        select = page.locator("select.compact-select").first
        select.select_option(str(1 if n != 1 else 2))
        pause(page, 120)
        select.select_option(str(n))
        pause(page, 400)
        return
    if counter_variant == "inline_stepper":
        n = min(max(adults_total, 1), 6)
        plus = page.locator(".step-btn").nth(1)
        minus = page.locator(".step-btn").nth(0)
        count_el = page.locator(".count").first
        current = int((count_el.inner_text() or "1").strip() or "1")
        while current < n:
            plus.click()
            current += 1
            pause(page, 120)
        while current > n:
            minus.click()
            current -= 1
            pause(page, 120)
        if n == 1:
            plus.click()
            pause(page, 120)
            minus.click()
            pause(page, 120)
        pause(page, 400)
        return
    page.locator(".controlGuests, .guestsField").first.click()
    page.locator(".doneBtn").first.wait_for(state="visible", timeout=8000)
    rooms = guests.get("rooms") or [{"adults": 2, "kids": []}]
    add_room = page.locator(".addRoomBtn")
    while page.locator(".room-form").count() < len(rooms):
        assert add_room.count(), "hotel guest picker has no add-room control"
        add_room.first.click()
        pause(page, 200)
    for idx, room in enumerate(rooms):
        form = page.locator(".room-form").nth(idx)
        adults = int(room.get("adults") or 2)
        adult_count = form.locator(".adult-count")
        if adult_count.count():
            current = int(adult_count.inner_text().strip() or "1")
            plus = form.locator(".adult-selector-box .counter").nth(1)
            minus = form.locator(".adult-selector-box .counter").nth(0)
            while current < adults:
                plus.click()
                current += 1
                pause(page, 120)
            while current > adults:
                minus.click()
                current -= 1
                pause(page, 120)
        kids = list(room.get("kids") or [])
        for age in kids:
            sel = form.locator(".kidSelect").first
            if sel.count():
                sel.select_option(str(age))
                pause(page, 150)
    page.locator(".doneBtn").first.click()
    pause(page, 400)


def _select_hotel_city_variant(page, city: dict[str, Any]) -> None:
    native = page.locator("select.native-select").first
    if native.count() and native.is_visible():
        city_id = city.get("cityId")
        if city_id:
            native.select_option(value=str(city_id))
        else:
            native.select_option(label=str(city.get("label") or city.get("cityName")))
        pause(page)
        return
    query = city.get("cityName") or (city.get("label") or "Цюрих").split(",")[0]
    select_hotel_city(page, str(query))


def _fill_hotel_dates(page, start: str | None, end: str | None, *, date_variant: str) -> None:
    if date_variant == "text_input":
        fields = page.locator(".date-text-input")
        fields.first.wait_for(state="visible", timeout=10000)
        if start:
            fields.nth(0).fill(_iso_to_ru(str(start)))
            fields.nth(0).blur()
            pause(page, 200)
        if end:
            fields.nth(1).fill(_iso_to_ru(str(end)))
            fields.nth(1).blur()
            pause(page, 200)
        return
    if date_variant == "inline_calendar":
        page.locator(".dayBtn").first.wait_for(state="visible", timeout=10000)
    elif date_variant == "single_popup":
        page.locator(".singleCell, .singlePopup button").first.click()
        page.locator(".dayBtn").first.wait_for(state="visible", timeout=10000)
    else:
        page.locator(".controlDates .cell.left, .controlDates button").first.click()
        page.locator(".dayBtn").first.wait_for(state="visible", timeout=10000)
    if start:
        _pick_hotel_iso_date(page, str(start))
    elif end:
        page.locator(".dayBtn:not([disabled])").first.click()
        pause(page, 200)
    if end:
        _pick_hotel_iso_date(page, str(end))


def run_hotels(page, track_id: str, stem: str, task: dict[str, Any]) -> None:
    variants = task_ui_variants(task)
    _goto(page, hotel_main_url(track_id))
    page.locator(".searchButton").wait_for(state="visible", timeout=20000)
    city = cond_params(task, "bench_hotel_select_city")
    if city:
        _select_hotel_city_variant(page, city)
    start = cond_params(task, "bench_hotel_select_start_date").get("date")
    end = cond_params(task, "bench_hotel_select_end_date").get("date")
    if start or end:
        _fill_hotel_dates(page, start, end, date_variant=variants.get("date", "split_popup"))
    guests = cond_params(task, "bench_hotel_select_guests")
    counter_variant = variants.get("counter_guests", "rooms_popup")
    if guests:
        rooms = guests.get("rooms") or []
        has_kids = any(room.get("kids") for room in rooms)
        if counter_variant != "rooms_popup" and (len(rooms) > 1 or has_kids):
            pytest.skip(f"{stem}: alt guest widget cannot encode rooms/kids")
        _set_hotel_guests(page, guests, counter_variant=counter_variant)
    elif stem.startswith("hotel_atomic_select_guests"):
        _set_hotel_guests(page, {"rooms": [{"adults": 2, "kids": []}]}, counter_variant=counter_variant)
    if cond_params(task, "state_changed").get("new_state") == "bench_hotel_search" or cond_params(
        task, "bench_hotel_select_hotel"
    ):
        page.locator(".searchButton").click()
        page.wait_for_url(re.compile(r"bench_hotel_search"), timeout=20000)
        page.locator(".cards .card, article.card").first.wait_for(state="visible", timeout=20000)
    hotel = cond_params(task, "bench_hotel_select_hotel")
    if hotel:
        name = hotel.get("hotelName")
        card = page.locator("article.card, .card").filter(has_text=str(name)) if name else page.locator("article.card, .card")
        btn = card.first.locator("button:has-text('Показать все номера')")
        (btn.first if btn.count() else page.locator("button:has-text('Показать все номера')").first).click()
        page.wait_for_url(re.compile(r"bench_hotel_hotel"), timeout=20000)
    if cond_params(task, "bench_hotel_select_room"):
        page.locator(".bookBtn").first.click()
        pause(page, 600)


FILES_COLLECTION_LABELS = {
    "lab_reports": "Отчёты лаборатории",
    "project_archive": "Архив проектов",
    "manuals": "Руководства",
    "datasets": "Наборы данных",
}


def run_files(page, track_id: str, stem: str, task: dict[str, Any]) -> None:
    collection = (
        cond_params(task, "bench_files_select_collection").get("collection")
        or cond_params(task, "bench_files_download").get("collection")
        or "lab_reports"
    )
    year = cond_params(task, "bench_files_select_year").get("year") or cond_params(
        task, "bench_files_download"
    ).get("year")
    download = cond_params(task, "bench_files_download")
    label = FILES_COLLECTION_LABELS.get(str(collection), str(collection))
    open_files_collection(page, track_id, label)
    if not year:
        return
    select_files_year(page, str(year))
    if not download:
        return
    link = page.get_by_role("link", name="Скачать локальный файл")
    link.first.wait_for(state="visible", timeout=10000)
    with page.expect_download(timeout=15000) as dl_info:
        link.first.click()
    download_obj = dl_info.value
    assert download_obj.suggested_filename, f"{stem}: empty download filename"


RUNNERS: list[tuple[str, Callable]] = [
    ("ecommerce_", run_shop),
    ("grocery_", run_grocery),
    ("bench_grocery_navigation", run_grocery),
    ("digital_books_", run_books),
    ("rail_", run_rail),
    ("hotel_", run_hotels),
    ("files_", run_files),
]


def runner_for(stem: str) -> Callable:
    for prefix, fn in RUNNERS:
        if stem.startswith(prefix):
            return fn
    raise KeyError(f"No golden-path runner for {stem}")


def run_task(page, track_id: str, stem: str) -> None:
    task = load_task(stem)
    runner_for(stem)(page, track_id, stem, task)
    pause(page, 800)
    assert_check_passed(track_id, stem)
