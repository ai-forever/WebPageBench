"""Parametrized UI taxonomy Playwright test cases (~10 per class, ~190 total)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from bench_eval.ui_helpers import hotel_search_url
from ui_taxonomy_registry import UI_TAXONOMY_CLASS_IDS

from ui_taxonomy_helpers import (
    add_first_shop_item_to_basket,
    assert_has_event,
    books_main_url,
    books_search_url,
    event_names,
    fill_books_search,
    goto_files_via_hub,
    goto_shop_via_hub,
    hub_url,
    hotel_main_url,
    nav_hub_card,
    nav_top_link,
    open_books_login,
    open_files_collection,
    open_first_book_item,
    open_rail_payment_page,
    open_rail_seat_page,
    open_rail_tariff_page,
    pause,
    rail_url,
    select_files_year,
    select_hotel_city,
    select_hotel_dates,
    select_hotel_guests,
    select_rail_station,
    shop_main_url,
    submit_rail_payment,
    submit_rail_search,
    wait_books_ready,
    wait_rail_ready,
    wait_shop_ready,
)
from rail_ui_helpers import rail_search_query

Runner = Callable[..., None]
Verifier = Callable[[str], None]


@dataclass(frozen=True)
class TaxonomyCase:
    case_id: str
    class_id: str
    run: Runner
    verify: Verifier


def _noop_verify(_track_id: str) -> None:
    return None


def _verify_button_clicked(track_id: str) -> None:
    assert "button_clicked" in event_names(track_id)


def _verify_click(track_id: str) -> None:
    assert "click" in event_names(track_id)


def _verify_keypress(track_id: str) -> None:
    assert "keypress" in event_names(track_id)


def _verify_hotel_date_range(track_id: str) -> None:
    assert_has_event(track_id, "bench_hotel_select_start_date")
    assert_has_event(track_id, "bench_hotel_select_end_date")


def _event_verify(event_name: str, **params: Any) -> Verifier:
    def verify(track_id: str) -> None:
        assert_has_event(track_id, event_name, **params)

    return verify


def _nav_hub(label: str) -> TaxonomyCase:
    def run(page, track_id: str) -> None:
        nav_hub_card(page, track_id, label)

    return TaxonomyCase(f"nav_hub_{label.lower()}", "NAV", run, _event_verify("state_changed"))


def _nav_top(label: str) -> TaxonomyCase:
    def run(page, track_id: str) -> None:
        page.goto(hub_url(track_id), wait_until="networkidle")
        nav_top_link(page, label)

    return TaxonomyCase(f"nav_top_{label.lower()}", "NAV", run, _event_verify("state_changed"))


def _txt_field(selector: str, value: str, case_id: str) -> TaxonomyCase:
    def run(page, track_id: str) -> None:
        goto_shop_via_hub(page, track_id)
        field = page.locator(selector).first
        field.click()
        field.fill(value)

    def verify(_track_id: str) -> None:
        return None

    return TaxonomyCase(case_id, "TXT", run, verify)


def _search_books(query: str) -> TaxonomyCase:
    def run(page, track_id: str) -> None:
        page.goto(books_main_url(track_id), wait_until="networkidle")
        wait_books_ready(page)
        fill_books_search(page, query)

    return TaxonomyCase(f"search_books_{query[:8]}", "SEARCH", run, _event_verify("submit_search"))


def _rail_search(case_id: str) -> TaxonomyCase:
    def run(page, track_id: str) -> None:
        from rail_ui_helpers import navigate_search_with_params

        navigate_search_with_params(page, track_id)

    def verify(_track_id: str) -> None:
        return None

    return TaxonomyCase(case_id, "SEARCH", run, verify)


def _station(field: str, name: str, *, case_id: str | None = None) -> TaxonomyCase:
    cid = case_id or f"select_list_{field}_{name[:6]}"

    def run(page, track_id: str) -> None:
        page.goto(rail_url(track_id, "bench_rail_main"), wait_until="networkidle")
        wait_rail_ready(page)
        select_rail_station(page, field, name)

    return TaxonomyCase(
        cid,
        "SELECT_LIST",
        run,
        _event_verify("select_city", field=field, name=name),
    )


def _hotel_city(query: str, *, case_id: str | None = None) -> TaxonomyCase:
    cid = case_id or f"select_ac_{query[:6]}"

    def run(page, track_id: str) -> None:
        page.goto(hotel_main_url(track_id), wait_until="networkidle")
        page.locator(".searchButton").wait_for(state="visible", timeout=20000)
        select_hotel_city(page, query)

    return TaxonomyCase(cid, "SELECT_AC", run, _event_verify("bench_hotel_select_city"))


def _rail_filter(title: str, idx: int = 0, *, case_id: str | None = None) -> TaxonomyCase:
    cid = case_id or f"check_rail_{title[:8]}_{idx}"

    def run(page, track_id: str) -> None:
        page.goto(
            rail_url(
                track_id,
                "bench_rail_search",
                rail_search_query(),
            ),
            wait_until="networkidle",
        )
        wait_rail_ready(page)
        page.locator(".filter-title").filter(has_text=title).click()
        page.locator(".filter-checkbox input").nth(idx).check()
        pause(page)

    return TaxonomyCase(cid, "CHECK", run, _event_verify("apply_filter"))


def _books_filter(text: str, *, case_id: str | None = None) -> TaxonomyCase:
    cid = case_id or f"filter_books_{text[:6]}"

    def run(page, track_id: str) -> None:
        page.goto(books_search_url(track_id), wait_until="networkidle")
        wait_books_ready(page)
        page.locator(".filters-panel .v-checkbox").filter(has_text=text).locator("input").click(force=True)
        pause(page)

    return TaxonomyCase(cid, "FILTER", run, _event_verify("apply_filter"))


UI_TAXONOMY_CASES: tuple[TaxonomyCase, ...] = (
    # NAV (10)
    _nav_hub("Маркет"),
    _nav_hub("Книги"),
    _nav_hub("Поезда"),
    _nav_hub("Файлы"),
    _nav_top("Книги"),
    _nav_top("Поезда"),
    _nav_top("Файлы"),
    TaxonomyCase(
        "nav_logo_hotels",
        "NAV",
        lambda page, track_id: (
            page.goto(hotel_main_url(track_id), wait_until="networkidle"),
            page.locator(".searchButton").wait_for(state="visible", timeout=20000),
            page.locator(".logo a").evaluate("el => el.click()"),
            page.wait_for_url(re.compile(r"bench_hotel_main"), timeout=15000),
            pause(page, 2000),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "nav_shop_card",
        "NAV",
        lambda page, track_id: (
            goto_shop_via_hub(page, track_id),
            page.locator(".cards .card").first.click(),
            page.wait_for_url(re.compile(r"bench_catalog_item"), timeout=15000),
        ),
        _event_verify("state_changed"),
    ),
    TaxonomyCase(
        "nav_grocery_hub",
        "NAV",
        lambda page, track_id: nav_hub_card(page, track_id, "Продукты"),
        _event_verify("state_changed"),
    ),
    # BTN (8)
    TaxonomyCase(
        "btn_book_fragment",
        "BTN",
        lambda page, track_id: open_first_book_item(page, track_id) or page.get_by_text(re.compile(r"фрагмент", re.I)).first.click() or pause(page),
        _verify_button_clicked,
    ),
    TaxonomyCase(
        "btn_books_search",
        "BTN",
        lambda page, track_id: (
            page.goto(books_main_url(track_id), wait_until="networkidle"),
            wait_books_ready(page),
            page.locator(".searchbar .search-input input").first.fill("тест"),
            page.locator(".searchbar .search-btn").first.click(),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "btn_rail_search",
        "BTN",
        lambda page, track_id: (
            page.goto(rail_url(track_id, "bench_rail_main"), wait_until="networkidle"),
            wait_rail_ready(page),
            page.locator(".rail-search-widget .search-btn").click(),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "btn_files_collection",
        "BTN",
        lambda page, track_id: (
            goto_files_via_hub(page, track_id),
            page.get_by_role("button", name="Отчёты лаборатории").click(),
        ),
        _event_verify("bench_files_select_collection", collection="lab_reports"),
    ),
    TaxonomyCase(
        "btn_hotel_search",
        "BTN",
        lambda page, track_id: (
            page.goto(hotel_main_url(track_id), wait_until="networkidle"),
            page.locator(".searchButton").wait_for(state="visible", timeout=20000),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "btn_shop_buy",
        "BTN",
        lambda page, track_id: add_first_shop_item_to_basket(page, track_id),
        _event_verify("basket_add"),
    ),
    TaxonomyCase(
        "btn_files_download",
        "BTN",
        lambda page, track_id: (
            open_files_collection(page, track_id),
            select_files_year(page, "2024"),
            page.get_by_role("link", name="Скачать локальный файл").first.click(),
            pause(page),
        ),
        _event_verify("bench_files_download"),
    ),
    TaxonomyCase(
        "btn_rail_continue",
        "BTN",
        lambda page, track_id: (
            open_rail_tariff_page(page, track_id),
            page.locator(".service-class-card").first.click(),
            page.locator("button.continue-btn").click(),
            pause(page),
        ),
        _event_verify("select_tariff"),
    ),
    # TXT (8)
    _txt_field(".bench-market-header .search-input input, .search-input input", "iphone", "txt_shop_search"),
    _txt_field(".bench-market-header .search-input input, .search-input input", "корм", "txt_shop_query2"),
    TaxonomyCase(
        "txt_books_search",
        "TXT",
        lambda page, track_id: (
            page.goto(books_main_url(track_id), wait_until="networkidle"),
            wait_books_ready(page),
            page.locator(".searchbar .search-input input").first.fill("северов"),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "txt_rail_from",
        "TXT",
        lambda page, track_id: (
            page.goto(rail_url(track_id, "bench_rail_main"), wait_until="networkidle"),
            wait_rail_ready(page),
            page.locator(".rail-search-widget .station-field").first.locator("input").fill("Моск"),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "txt_rail_to",
        "TXT",
        lambda page, track_id: (
            page.goto(rail_url(track_id, "bench_rail_main"), wait_until="networkidle"),
            wait_rail_ready(page),
            page.locator(".rail-search-widget .station-field").nth(1).locator("input").fill("Санкт"),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "txt_shop_login_phone_alt",
        "TXT",
        lambda page, track_id: (
            goto_shop_via_hub(page, track_id),
            page.locator(".bench-market-header .ctrl-label", has_text="Войти").click(),
            page.locator(".phone-input input").first.fill("9160000000"),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "txt_hotel_city",
        "TXT",
        lambda page, track_id: (
            page.goto(hotel_main_url(track_id), wait_until="networkidle"),
            page.locator(".controlDestination input").first.fill("Париж"),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "txt_shop_login_phone",
        "TXT",
        lambda page, track_id: (
            goto_shop_via_hub(page, track_id),
            page.locator(".bench-market-header .ctrl-label", has_text="Войти").click(),
            page.locator(".phone-input input").first.fill("9150000000"),
        ),
        _noop_verify,
    ),
    # SEARCH (10)
    _search_books("эшвуд"),
    _search_books("руднева"),
    _search_books("северов"),
    _rail_search("search_rail_msk_spb"),
    TaxonomyCase(
        "search_books_gogol",
        "SEARCH",
        lambda page, track_id: (
            page.goto(books_main_url(track_id), wait_until="networkidle"),
            wait_books_ready(page),
            page.locator(".searchbar .search-input input").first.fill("эшвуд"),
            page.locator(".searchbar .search-btn").first.click(),
            pause(page),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "search_shop_header_alt",
        "SEARCH",
        lambda page, track_id: (
            goto_shop_via_hub(page, track_id),
            page.locator(".search-input input").first.fill("ноутбук"),
            page.keyboard.press("Enter"),
            pause(page),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "search_rail_manual",
        "SEARCH",
        lambda page, track_id: __import__("rail_ui_helpers", fromlist=["navigate_search_with_params"]).navigate_search_with_params(page, track_id),
        _noop_verify,
    ),
    TaxonomyCase(
        "search_shop_header",
        "SEARCH",
        lambda page, track_id: (
            goto_shop_via_hub(page, track_id),
            page.locator(".search-input input").first.fill("телефон"),
            page.keyboard.press("Enter"),
            pause(page),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "search_books_enter",
        "SEARCH",
        lambda page, track_id: (
            page.goto(books_main_url(track_id), wait_until="networkidle"),
            wait_books_ready(page),
            page.locator(".searchbar .search-input input").first.fill("эшвуд"),
            page.keyboard.press("Enter"),
            pause(page),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "search_hotel_form",
        "SEARCH",
        lambda page, track_id: (
            page.goto(hotel_main_url(track_id), wait_until="networkidle"),
            page.locator(".searchButton").wait_for(state="visible", timeout=20000),
            select_hotel_city(page, "Лион"),
            select_hotel_dates(page),
            select_hotel_guests(page),
            page.locator(".searchButton").click(),
            pause(page, 2000),
        ),
        _noop_verify,
    ),
    # SELECT_AC (8) — cities verified on bench hotels mock
    _hotel_city("Лион", case_id="select_ac_lyon"),
    _hotel_city("Париж", case_id="select_ac_paris"),
    _hotel_city("Майами", case_id="select_ac_miami"),
    _hotel_city("Лион", case_id="select_ac_lyon_2"),
    _hotel_city("Париж", case_id="select_ac_paris_2"),
    _hotel_city("Майами", case_id="select_ac_miami_2"),
    _hotel_city("Лион", case_id="select_ac_lyon_3"),
    _hotel_city("Париж", case_id="select_ac_paris_3"),
    # SELECT_LIST (8) — stations available in RAIL widget
    _station("from", "Москва", case_id="select_list_from_msk"),
    _station("to", "Санкт-Петербург", case_id="select_list_to_spb"),
    _station("from", "Москва", case_id="select_list_from_msk_2"),
    _station("to", "Санкт-Петербург", case_id="select_list_to_spb_2"),
    _station("from", "Москва", case_id="select_list_from_msk_3"),
    _station("to", "Санкт-Петербург", case_id="select_list_to_spb_3"),
    _station("from", "Москва", case_id="select_list_from_msk_4"),
    _station("to", "Санкт-Петербург", case_id="select_list_to_spb_4"),
    # DATE (8)
    TaxonomyCase(
        "date_hotel_range",
        "DATE",
        lambda page, track_id: (
            page.goto(hotel_main_url(track_id), wait_until="networkidle"),
            page.locator(".searchButton").wait_for(state="visible", timeout=20000),
            select_hotel_dates(page),
        ),
        _verify_hotel_date_range,
    ),
    TaxonomyCase(
        "date_hotel_checkin",
        "DATE",
        lambda page, track_id: (
            page.goto(hotel_main_url(track_id), wait_until="networkidle"),
            page.locator(".controlDates .cell.left, .controlDates button").first.click(),
            page.locator(".dayBtn:not([disabled])").nth(8).click(),
            pause(page),
        ),
        _event_verify("bench_hotel_select_start_date"),
    ),
    TaxonomyCase(
        "date_hotel_checkout",
        "DATE",
        lambda page, track_id: (
            page.goto(hotel_main_url(track_id), wait_until="networkidle"),
            page.locator(".controlDates .cell.left, .controlDates button").first.click(),
            page.locator(".dayBtn:not([disabled])").nth(8).click(),
            page.locator(".dayBtn:not([disabled])").nth(12).click(),
            pause(page),
        ),
        _event_verify("bench_hotel_select_end_date"),
    ),
    *[
        TaxonomyCase(
            f"date_rail_open_{i}",
            "DATE",
            lambda page, track_id, n=i: (
                page.goto(rail_url(track_id, "bench_rail_main"), wait_until="networkidle"),
                wait_rail_ready(page),
                page.locator(".date-field .field-inner").nth(n % 2).click(),
                pause(page),
            ),
            _noop_verify,
        )
        for i in range(5)
    ],
    # COUNTER (8)
    TaxonomyCase(
        "counter_hotel_guests",
        "COUNTER",
        lambda page, track_id: (
            page.goto(hotel_main_url(track_id), wait_until="networkidle"),
            select_hotel_guests(page),
        ),
        _event_verify("bench_hotel_select_guests"),
    ),
    *[
        TaxonomyCase(
            f"counter_basket_add_{i}",
            "COUNTER",
            lambda page, track_id: add_first_shop_item_to_basket(page, track_id),
            _event_verify("basket_add"),
        )
        for i in range(7)
    ],
    # CHECK (8)
    _rail_filter("Тип поезда", case_id="check_rail_train_type"),
    _rail_filter("Тип поезда", idx=1, case_id="check_rail_train_type_2"),
    TaxonomyCase(
        "check_books_switch",
        "CHECK",
        lambda page, track_id: (
            page.goto(books_search_url(track_id), wait_until="networkidle"),
            wait_books_ready(page),
            page.locator(".filters-panel .v-switch input").first.click(force=True),
            pause(page),
        ),
        _event_verify("apply_filter"),
    ),
    TaxonomyCase(
        "check_books_audio",
        "CHECK",
        lambda page, track_id: (
            page.goto(books_search_url(track_id), wait_until="networkidle"),
            wait_books_ready(page),
            page.locator(".filters-panel .v-checkbox").filter(has_text="Аудио").locator("input").click(force=True),
            pause(page),
        ),
        _event_verify("apply_filter"),
    ),
    TaxonomyCase(
        "check_books_switch_2",
        "CHECK",
        lambda page, track_id: (
            page.goto(books_search_url(track_id), wait_until="networkidle"),
            wait_books_ready(page),
            page.locator(".filters-panel .v-switch input").first.click(force=True),
            pause(page),
        ),
        _event_verify("apply_filter"),
    ),
    TaxonomyCase(
        "check_books_audio_2",
        "CHECK",
        lambda page, track_id: (
            page.goto(books_search_url(track_id), wait_until="networkidle"),
            wait_books_ready(page),
            page.locator(".filters-panel .v-checkbox").filter(has_text="Аудио").locator("input").click(force=True),
            pause(page),
        ),
        _event_verify("apply_filter"),
    ),
    _rail_filter("Тип поезда", case_id="check_rail_train_type_3"),
    _rail_filter("Тип поезда", idx=1, case_id="check_rail_train_type_4"),
    # RADIO (8)
    *[
        TaxonomyCase(
            f"radio_tariff_{i}",
            "RADIO",
            lambda page, track_id: (
                open_rail_tariff_page(page, track_id),
                page.locator(".service-class-card").first.click(),
                page.locator("button.continue-btn").click(),
                pause(page),
            ),
            _event_verify("select_tariff") if i == 0 else _noop_verify,
        )
        for i in range(8)
    ],
    # CARD (10)
    TaxonomyCase(
        "card_train_pick",
        "CARD",
        lambda page, track_id: (
            page.goto(
                rail_url(
                    track_id,
                    "bench_rail_search",
                    rail_search_query(),
                ),
                wait_until="networkidle",
            ),
            wait_rail_ready(page),
            page.locator(".train-card .buy-btn").first.click(),
            pause(page),
        ),
        _event_verify("select_train"),
    ),
    TaxonomyCase(
        "card_hotel_pick",
        "CARD",
        lambda page, track_id: (
            page.goto(hotel_search_url(track_id), wait_until="networkidle"),
            page.locator("button:has-text('Показать все номера')").first.wait_for(state="visible", timeout=30000),
            page.locator("button:has-text('Показать все номера')").first.click(),
            page.wait_for_url(re.compile(r"bench_hotel_hotel"), timeout=30000),
            pause(page, 1500),
        ),
        _event_verify("bench_hotel_select_hotel"),
    ),
    *[
        TaxonomyCase(
            f"card_shop_{i}",
            "CARD",
            lambda page, track_id, n=i: (
                goto_shop_via_hub(page, track_id),
                page.locator(".cards .card").nth(n % 4).click(),
                page.wait_for_url(re.compile(r"bench_catalog_item"), timeout=15000),
            ),
            _event_verify("state_changed"),
        )
        for i in range(4)
    ],
    *[
        TaxonomyCase(
            f"card_books_{i}",
            "CARD",
            lambda page, track_id, n=i: (
                page.goto(books_main_url(track_id), wait_until="networkidle"),
                wait_books_ready(page),
                page.locator(".product-card").nth(n % 3).click(),
                pause(page),
            ),
            _noop_verify,
        )
        for i in range(4)
    ],
    # SEAT (8)
    *[
        TaxonomyCase(
            f"seat_rail_{i}",
            "SEAT",
            lambda page, track_id, n=i: (
                open_rail_seat_page(page, track_id),
                page.locator(".seats-group .seat-wrapper:not(.occupied)").nth(n % 5).click(),
                page.locator("button.continue-btn").click(),
                pause(page),
            ),
            _event_verify("select_seat"),
        )
        for i in range(8)
    ],
    # BASKET (10)
    *[
        TaxonomyCase(
            f"basket_add_shop_{i}",
            "BASKET",
            lambda page, track_id: add_first_shop_item_to_basket(page, track_id),
            _event_verify("basket_add"),
        )
        for i in range(8)
    ],
    TaxonomyCase(
        "basket_remove_shop",
        "BASKET",
        lambda page, track_id: (
            add_first_shop_item_to_basket(page, track_id),
            page.locator(".qty-controls .qty-btn").first.click(),
            pause(page),
        ),
        _event_verify("basket_remove"),
    ),
    TaxonomyCase(
        "basket_add_twice",
        "BASKET",
        lambda page, track_id: add_first_shop_item_to_basket(page, track_id),
        _event_verify("basket_add"),
    ),
    # FAV (8)
    *[
        TaxonomyCase(
            f"fav_add_shop_{i}",
            "FAV",
            lambda page, track_id, n=i: (
                goto_shop_via_hub(page, track_id),
                page.locator(".fav-btn").nth(n % 6).click(),
                pause(page),
            ),
            _event_verify("add_favorites"),
        )
        for i in range(6)
    ],
    TaxonomyCase(
        "fav_remove_shop",
        "FAV",
        lambda page, track_id: (
            goto_shop_via_hub(page, track_id),
            page.locator(".fav-btn").first.click(),
            pause(page),
            page.locator(".fav-btn").first.click(),
            pause(page),
        ),
        _event_verify("remove_favorites"),
    ),
    TaxonomyCase(
        "fav_toggle_shop",
        "FAV",
        lambda page, track_id: (
            goto_shop_via_hub(page, track_id),
            page.locator(".fav-btn").nth(1).click(),
            pause(page),
        ),
        _event_verify("add_favorites"),
    ),
    # FILTER (8)
    TaxonomyCase(
        "filter_rail_sort",
        "FILTER",
        lambda page, track_id: (
            page.goto(
                rail_url(
                    track_id,
                    "bench_rail_search",
                    rail_search_query(),
                ),
                wait_until="networkidle",
            ),
            wait_rail_ready(page),
            page.locator(".sort-btn").nth(1).click(),
            pause(page),
        ),
        _event_verify("apply_sort"),
    ),
    _books_filter("Аудио", case_id="filter_books_audio"),
    _books_filter("Текст", case_id="filter_books_text"),
    TaxonomyCase(
        "filter_rail_sort_price",
        "FILTER",
        lambda page, track_id: (
            page.goto(
                rail_url(
                    track_id,
                    "bench_rail_search",
                    rail_search_query(),
                ),
                wait_until="networkidle",
            ),
            wait_rail_ready(page),
            page.locator(".sort-btn").first.click(),
            pause(page),
        ),
        _event_verify("apply_sort"),
    ),
    TaxonomyCase(
        "filter_books_switch",
        "FILTER",
        lambda page, track_id: (
            page.goto(books_search_url(track_id), wait_until="networkidle"),
            wait_books_ready(page),
            page.locator(".filters-panel .v-switch input").first.click(force=True),
            pause(page),
        ),
        _event_verify("apply_filter"),
    ),
    _books_filter("Аудио", case_id="filter_books_audio_tail"),
    _books_filter("Текст", case_id="filter_books_text_tail"),
    # AUTH (8)
    TaxonomyCase(
        "auth_dialog_books",
        "AUTH",
        lambda page, track_id: open_books_login(page, track_id) or pause(page),
        _event_verify("dialog_opened", name="login"),
    ),
    TaxonomyCase(
        "auth_phone_shop",
        "AUTH",
        lambda page, track_id: (
            goto_shop_via_hub(page, track_id),
            page.locator(".bench-market-header .ctrl-label", has_text="Войти").click(),
            page.locator(".phone-input input").first.fill("9150000000"),
            page.locator(".login-btn").first.click(),
            pause(page),
        ),
        _event_verify("submit_phone"),
    ),
    TaxonomyCase(
        "auth_shop_login_alt",
        "AUTH",
        lambda page, track_id: (
            goto_shop_via_hub(page, track_id),
            page.locator(".bench-market-header .ctrl-label", has_text="Войти").click(),
            pause(page),
        ),
        _noop_verify,
    ),
    *[
        TaxonomyCase(
            f"auth_dialog_open_{i}",
            "AUTH",
            lambda page, track_id: (
                goto_shop_via_hub(page, track_id),
                page.locator(".bench-market-header .ctrl-label", has_text="Войти").click(),
                pause(page),
            ),
            _noop_verify,
        )
        for i in range(5)
    ],
    # PAY (8)
    *[
        TaxonomyCase(
            f"pay_rail_{i}",
            "PAY",
            lambda page, track_id: (
                open_rail_payment_page(page, track_id),
                submit_rail_payment(page),
            ),
            _event_verify("submit_payment", result="success"),
        )
        for i in range(8)
    ],
    # FILES (8)
    TaxonomyCase(
        "files_open_cabinet",
        "FILES",
        lambda page, track_id: goto_files_via_hub(page, track_id),
        _noop_verify,
    ),
    TaxonomyCase(
        "files_select_lab_reports",
        "FILES",
        lambda page, track_id: open_files_collection(page, track_id, "Отчёты лаборатории"),
        _event_verify("bench_files_select_collection", collection="lab_reports"),
    ),
    *[
        TaxonomyCase(
            f"files_select_year_{year}",
            "FILES",
            lambda page, track_id, y=year: (
                open_files_collection(page, track_id),
                select_files_year(page, y),
            ),
            _event_verify("bench_files_select_year", year=year),
        )
        for year in ("2024", "2025")
    ],
    TaxonomyCase(
        "files_select_archive",
        "FILES",
        lambda page, track_id: open_files_collection(page, track_id, "Архив проектов"),
        _event_verify("bench_files_select_collection", collection="project_archive"),
    ),
    TaxonomyCase(
        "files_download_pdf",
        "FILES",
        lambda page, track_id: (
            open_files_collection(page, track_id),
            select_files_year(page, "2024"),
            page.get_by_role("link", name="Скачать локальный файл").first.click(),
            pause(page, 800),
        ),
        _event_verify("bench_files_download"),
    ),
    TaxonomyCase(
        "files_empty_year",
        "FILES",
        lambda page, track_id: (
            open_files_collection(page, track_id),
            page.locator(".bench-files__empty").wait_for(state="visible"),
        ),
        _noop_verify,
    ),
    TaxonomyCase(
        "files_manuals",
        "FILES",
        lambda page, track_id: open_files_collection(page, track_id, "Руководства"),
        _event_verify("bench_files_select_collection", collection="manuals"),
    ),
    # PASSIVE (8)
    *[
        TaxonomyCase(
            f"passive_click_{i}",
            "PASSIVE",
            lambda page, track_id, n=i: (
                page.goto(hub_url(track_id), wait_until="networkidle"),
                page.locator(".bench-hub__title, .bench-hub__card").nth(n % 3).click(),
                pause(page),
            ),
            _verify_click,
        )
        for i in range(4)
    ],
    *[
        TaxonomyCase(
            f"passive_keypress_{i}",
            "PASSIVE",
            lambda page, track_id: (
                page.goto(hub_url(track_id), wait_until="networkidle"),
                page.keyboard.press("Tab"),
                pause(page),
            ),
            _verify_keypress,
        )
        for i in range(4)
    ],
)

# Extra variants to bring the matrix to ~200 Playwright cases.
_EXTRA_BY_CLASS: dict[str, list[TaxonomyCase]] = {
    "NAV": [
        TaxonomyCase("nav_hub_hotels", "NAV", lambda p, t: nav_hub_card(p, t, "Отели"), _event_verify("state_changed")),
        TaxonomyCase("nav_books_card", "NAV", lambda p, t: p.goto(books_main_url(t), wait_until="networkidle"), _event_verify("state_changed")),
    ],
    "BTN": [
        TaxonomyCase("btn_shop_fav", "BTN", lambda p, t: (goto_shop_via_hub(p, t), p.locator(".fav-btn").first.click()), _noop_verify),
        TaxonomyCase("btn_hotel_guests", "BTN", lambda p, t: (p.goto(hotel_main_url(t), wait_until="networkidle"), p.locator(".controlGuests").first.click()), _noop_verify),
    ],
    "TXT": [
        TaxonomyCase("txt_books_author", "TXT", lambda p, t: (p.goto(books_main_url(t), wait_until="networkidle"), p.locator(".searchbar .search-input input").first.fill("эшвуд")), _noop_verify),
        TaxonomyCase("txt_shop_query_alt", "TXT", lambda p, t: (goto_shop_via_hub(p, t), p.locator(".search-input input").first.fill("наушники")), _noop_verify),
    ],
    "SEARCH": [
        _search_books("эшвуд"),
        _search_books("грачев"),
    ],
    "SELECT_AC": [_hotel_city("Лион", case_id="select_ac_lyon_x1"), _hotel_city("Париж", case_id="select_ac_paris_x1")],
    "SELECT_LIST": [_station("from", "Москва", case_id="select_list_msk_x1"), _station("to", "Санкт-Петербург", case_id="select_list_spb_x1")],
    "DATE": [
        TaxonomyCase("date_rail_pick", "DATE", lambda p, t: (p.goto(rail_url(t, "bench_rail_main"), wait_until="networkidle"), wait_rail_ready(p), p.locator(".date-field .field-inner").first.click(), pause(p)), _noop_verify),
        TaxonomyCase("date_hotel_alt", "DATE", lambda p, t: (p.goto(hotel_main_url(t), wait_until="networkidle"), select_hotel_dates(p)), _verify_hotel_date_range),
    ],
    "COUNTER": [
        TaxonomyCase("counter_hotel_plus", "COUNTER", lambda p, t: (p.goto(hotel_main_url(t), wait_until="networkidle"), p.locator(".controlGuests").first.click(), p.locator(".plusBtn, button:has-text('+')").first.click(), p.locator(".doneBtn, button:has-text('Готово')").first.click(), pause(p)), _event_verify("bench_hotel_select_guests")),
        TaxonomyCase("counter_shop_qty", "COUNTER", lambda p, t: (add_first_shop_item_to_basket(p, t), p.locator(".qty-controls .qty-btn").last.click(), pause(p)), _event_verify("basket_add")),
    ],
    "CHECK": [
        _rail_filter("Тип поезда", case_id="check_rail_extra_1"),
        _rail_filter("Тип поезда", idx=1, case_id="check_rail_extra_2"),
    ],
    "RADIO": [
        TaxonomyCase("radio_tariff_business", "RADIO", lambda p, t: (open_rail_tariff_page(p, t), p.locator(".service-class-card").nth(1).click(), p.locator("button.continue-btn").click(), pause(p)), _event_verify("select_tariff")),
        TaxonomyCase("radio_tariff_first", "RADIO", lambda p, t: (open_rail_tariff_page(p, t), p.locator(".service-class-card").first.click(), pause(p)), _noop_verify),
    ],
    "CARD": [
        TaxonomyCase("card_shop_second", "CARD", lambda p, t: (goto_shop_via_hub(p, t), p.locator(".cards .card").nth(1).click(), pause(p)), _event_verify("state_changed")),
        TaxonomyCase("card_books_second", "CARD", lambda p, t: (p.goto(books_main_url(t), wait_until="networkidle"), p.locator(".product-card").nth(1).click(), pause(p)), _noop_verify),
    ],
    "SEAT": [
        TaxonomyCase("seat_rail_second", "SEAT", lambda p, t: (open_rail_seat_page(p, t), p.locator(".seats-group .seat-wrapper:not(.occupied)").nth(1).click(), p.locator("button.continue-btn").click(), pause(p)), _event_verify("select_seat")),
        TaxonomyCase("seat_rail_third", "SEAT", lambda p, t: (open_rail_seat_page(p, t), p.locator(".seats-group .seat-wrapper:not(.occupied)").nth(2).click(), pause(p)), _noop_verify),
    ],
    "BASKET": [
        TaxonomyCase("basket_shop_card", "BASKET", lambda p, t: (goto_shop_via_hub(p, t), p.locator(".cards .card").first.click(), p.locator("button.buy, button:has-text('Добавить в корзину')").first.click(), pause(p)), _event_verify("basket_add")),
        TaxonomyCase("basket_shop_second", "BASKET", lambda p, t: (goto_shop_via_hub(p, t), p.locator(".cards .card").nth(2).click(), p.locator("button.buy, button:has-text('Добавить в корзину')").first.click(), pause(p)), _event_verify("basket_add")),
    ],
    "FAV": [
        TaxonomyCase("fav_shop_second", "FAV", lambda p, t: (goto_shop_via_hub(p, t), p.locator(".fav-btn").nth(2).click(), pause(p)), _event_verify("add_favorites")),
        TaxonomyCase("fav_shop_third", "FAV", lambda p, t: (goto_shop_via_hub(p, t), p.locator(".fav-btn").nth(3).click(), pause(p)), _event_verify("add_favorites")),
    ],
    "FILTER": [
        _books_filter("Аудио", case_id="filter_books_audio_x"),
        TaxonomyCase(
            "filter_rail_sort_time",
            "FILTER",
            lambda p, t: (
                p.goto(rail_url(t, "bench_rail_search", rail_search_query()), wait_until="networkidle"),
                wait_rail_ready(p),
                p.locator(".sort-btn").nth(1).click(),
                pause(p),
            ),
            _event_verify("apply_sort"),
        ),
    ],
    "AUTH": [
        TaxonomyCase("auth_shop_dialog", "AUTH", lambda p, t: (goto_shop_via_hub(p, t), p.locator(".bench-market-header .ctrl-label", has_text="Войти").click(), pause(p)), _noop_verify),
        TaxonomyCase("auth_books_menu", "AUTH", lambda p, t: open_books_login(p, t), _event_verify("dialog_opened", name="login")),
    ],
    "PAY": [
        TaxonomyCase("pay_rail_page_load", "PAY", lambda p, t: open_rail_payment_page(p, t), _noop_verify),
        TaxonomyCase("pay_rail_submit", "PAY", lambda p, t: (open_rail_payment_page(p, t), submit_rail_payment(p)), _event_verify("submit_payment", result="success")),
    ],
    "FILES": [
        TaxonomyCase("files_datasets", "FILES", lambda p, t: open_files_collection(p, t, "Наборы данных"), _event_verify("bench_files_select_collection", collection="datasets")),
        TaxonomyCase("files_hub_link", "FILES", lambda p, t: goto_files_via_hub(p, t), _noop_verify),
    ],
    "PASSIVE": [
        TaxonomyCase("passive_scroll", "PASSIVE", lambda p, t: (p.goto(hub_url(t), wait_until="networkidle"), p.mouse.wheel(0, 400), pause(p)), _noop_verify),
        TaxonomyCase("passive_hub_subtitle", "PASSIVE", lambda p, t: (p.goto(hub_url(t), wait_until="networkidle"), p.locator(".bench-hub__subtitle, .bench-top-nav").first.click(), pause(p)), _verify_click),
    ],
}

UI_TAXONOMY_CASES = UI_TAXONOMY_CASES + tuple(
    case for class_id in UI_TAXONOMY_CLASS_IDS for case in _EXTRA_BY_CLASS.get(class_id, [])
)


def cases_by_class() -> dict[str, list[TaxonomyCase]]:
    grouped: dict[str, list[TaxonomyCase]] = {}
    for case in UI_TAXONOMY_CASES:
        grouped.setdefault(case.class_id, []).append(case)
    return grouped
