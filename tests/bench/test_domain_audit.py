"""Playwright domain audit: widgets, layout, assets, events for all 6 hub sections."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_BENCH_DIR = Path(__file__).resolve().parent
if str(_BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(_BENCH_DIR))


from bench_eval.page_audit import (
    SCREENSHOT_DIR,
    assert_assets_ok,
    assert_click_target_not_covered,
    assert_no_horizontal_overflow,
    assert_pairs_do_not_overlap,
    attach_network_listeners,
    css_background_urls,
    screenshot,
    scroll_page_to_bottom,
)
from bench_eval.ui_helpers import (
    create_base_track,
    event_names,
    grocery_main_url,
    hotel_main_url,
    hotel_search_url,
    files_cabinet_url,
    page_url,
)
from rail_ui_helpers import rail_url, wait_rail_ready
from ui_taxonomy_helpers import (
    BOOKS_SEARCH_QUERY,
    books_main_url,
    dismiss_shop_popup,
    fill_books_search,
    hub_url,
    pause,
    select_hotel_city,
    shop_main_url,
    wait_books_ready,
    wait_files_ready,
    wait_shop_ready,
)

pytestmark = pytest.mark.ui

NAV_HEADER_PAIRS = [
    (".bench-top-nav", ".bench-market-header, .rail-header, .searchbar, .bench-hotels .widgets"),
]


@pytest.fixture(scope="session")
def audit_track(require_services) -> str:
    return create_base_track("webpagebench_domain_audit")


def _audit_page(page, bag, name: str, *, cta: str | None = None) -> None:
    screenshot(page, f"{name}-fold")
    assert_no_horizontal_overflow(page, label=name)
    assert_pairs_do_not_overlap(page, NAV_HEADER_PAIRS, label=name)
    if cta:
        try:
            assert_click_target_not_covered(page, cta, label=name)
        except Exception:
            screenshot(page, f"{name}-covered")
            raise
    scroll_page_to_bottom(page)
    pause(page, 400)
    assert_assets_ok(page, bag, label=name)


class TestHubAudit:
    def test_hub_cards_and_layout(self, page, audit_track):
        bag = attach_network_listeners(page)
        page.goto(hub_url(audit_track), wait_until="networkidle")
        page.locator(".bench-hub__card").first.wait_for(state="visible")
        assert page.locator(".bench-hub__card").count() >= 6
        _audit_page(page, bag, "hub", cta=".bench-hub__card")
        page.locator('.bench-hub__card[data-section="shop"]').first.click()
        page.wait_for_url(re.compile(r"bench_catalog_main"), timeout=20000)
        assert "state_changed" in event_names(audit_track) or "bench_catalog_main" in page.url


class TestShopAudit:
    def test_shop_search_basket_fav(self, page, audit_track):
        bag = attach_network_listeners(page)
        page.goto(shop_main_url(audit_track), wait_until="networkidle")
        wait_shop_ready(page)
        dismiss_shop_popup(page)
        _audit_page(page, bag, "shop-main", cta=".cards .card")
        search = page.locator("input[placeholder*='Искать'], .bench-market-header input, input[type='search']").first
        search.click()
        search.fill("whiskas")
        search.press("Enter")
        pause(page, 1200)
        screenshot(page, "shop-search")
        page.goto(shop_main_url(audit_track), wait_until="networkidle")
        wait_shop_ready(page)
        dismiss_shop_popup(page)
        page.locator(".cards .card").first.click()
        page.wait_for_url(re.compile(r"bench_catalog_item"), timeout=20000)
        page.locator("button.buy").first.click()
        pause(page, 500)
        page.locator(".fav-btn-static, .heart-btn").first.click()
        pause(page, 400)
        names = event_names(audit_track)
        assert "basket_add" in names
        assert "add_favorites" in names

    def test_shop_checkout_local_payment_icons(self, page, audit_track):
        bag = attach_network_listeners(page)
        page.goto(
            page_url(audit_track, "state_purchase", "bench_catalog_purchase"),
            wait_until="networkidle",
        )
        page.locator(".pay-options, .purchase-page").first.wait_for(state="visible", timeout=20000)
        screenshot(page, "shop-checkout")
        assert_assets_ok(page, bag, label="shop-checkout")
        network = " ".join((bag.get("failed") or []) + (bag.get("http_error") or []))
        backgrounds = css_background_urls(page)
        assert "ir.ozone.ru" not in network, network
        assert not any("ir.ozone.ru" in u for u in backgrounds), backgrounds
        assert any("/shop/pay-" in u for u in backgrounds), backgrounds


class TestGroceryAudit:
    def test_grocery_menu_search_basket(self, page, audit_track):
        bag = attach_network_listeners(page)
        page.goto(grocery_main_url(audit_track), wait_until="networkidle")
        page.locator(".grocery-card").first.wait_for(state="visible", timeout=20000)
        _audit_page(page, bag, "grocery-main", cta=".grocery-card .add-button")
        page.locator(".grocery-card .add-button").first.click()
        pause(page, 400)
        page.locator(".menu-bar .menu-item").nth(1).click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        page.locator(".grocery-card").first.wait_for(state="visible")
        search = page.locator(".searchbar input, input[placeholder]").first
        if search.count():
            search.fill("молоко")
            pause(page, 800)
        screenshot(page, "grocery-category")
        assert "basket_add" in event_names(audit_track)


class TestBooksAudit:
    def test_books_search_filters_basket(self, page, audit_track):
        bag = attach_network_listeners(page)
        page.goto(books_main_url(audit_track), wait_until="networkidle")
        wait_books_ready(page)
        _audit_page(page, bag, "books-main", cta=".searchbar .search-btn")
        fill_books_search(page, BOOKS_SEARCH_QUERY)
        page.wait_for_url(re.compile(r"bench_books_search"), timeout=20000)
        screenshot(page, "books-search")
        page.locator(".product-card, .book-card").first.wait_for(state="visible", timeout=20000)
        page.locator(".product-card .name, .book-card .name").first.click()
        page.wait_for_url(re.compile(r"bench_books_item"), timeout=15000)
        page.locator(".buy-card .secondary").first.click()
        pause(page, 500)
        names = event_names(audit_track)
        assert "submit_search" in names
        assert "basket_add" in names


class TestRailAudit:
    def test_rail_search_form_and_layout(self, page, audit_track):
        bag = attach_network_listeners(page)
        page.goto(rail_url(audit_track, "bench_rail_main"), wait_until="networkidle")
        wait_rail_ready(page)
        _audit_page(page, bag, "rail-main", cta=".rail-search-widget .search-btn")
        from ui_taxonomy_helpers import select_rail_station, submit_rail_search

        select_rail_station(page, "from", "Москва")
        select_rail_station(page, "to", "Санкт-Петербург")
        page.locator(".date-field .field-inner").first.click()
        enabled = page.locator(".datepicker-container .day-cell:not(.disabled):not(.empty) .day-number")
        enabled.first.wait_for(state="visible")
        screenshot(page, "rail-datepicker")
        enabled.first.click()
        pause(page, 400)
        no_return = page.locator(".no-return-btn")
        if no_return.count():
            no_return.first.click()
        submit_rail_search(page)
        screenshot(page, "rail-search")
        names = event_names(audit_track)
        assert "select_city" in names
        assert "submit_search" in names


class TestHotelsAudit:
    def test_hotels_widgets_layout(self, page, audit_track):
        bag = attach_network_listeners(page)
        page.goto(hotel_main_url(audit_track), wait_until="networkidle")
        page.locator(".searchButton").wait_for(state="visible")
        _audit_page(page, bag, "hotels-main", cta=".searchButton")
        select_hotel_city(page, "Цюрих")
        page.locator(".controlDates .cell.left, .controlDates button").first.click()
        page.locator(".dayBtn").first.wait_for(state="visible", timeout=10000)
        screenshot(page, "hotels-calendar")
        page.locator(".dayBtn:not([disabled])").nth(10).click()
        page.locator(".dayBtn:not([disabled])").nth(14).click()
        page.locator(".controlGuests").first.click()
        page.locator(".doneBtn").first.click()
        page.locator(".searchButton").click()
        page.wait_for_url(re.compile(r"bench_hotel_search"), timeout=20000)
        screenshot(page, "hotels-search")
        names = event_names(audit_track)
        assert "bench_hotel_select_city" in names
        assert "bench_hotel_select_start_date" in names


class TestFilesAudit:
    def test_files_cabinet_and_download(self, page, audit_track):
        bag = attach_network_listeners(page)
        page.goto(files_cabinet_url(audit_track), wait_until="networkidle")
        wait_files_ready(page)
        _audit_page(page, bag, "files-main", cta=".bench-files__nav-btn")
        page.get_by_role("button", name="Отчёты лаборатории").click()
        page.wait_for_url(re.compile(r"bench_files_collection"), timeout=15000)
        wait_files_ready(page)
        page.locator(".bench-files select").first.select_option("2024")
        screenshot(page, "files-collection-year")
        names = event_names(audit_track)
        assert "bench_files_select_collection" in names
        assert "bench_files_select_year" in names


class TestViewportSmoke:
    @pytest.mark.parametrize("width,height", [(1280, 720), (1920, 1080)])
    def test_hub_no_overflow_alt_viewport(self, browser, audit_track, width, height):
        context = browser.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        page.goto(hub_url(audit_track), wait_until="networkidle")
        page.locator(".bench-hub__card").first.wait_for(state="visible")
        assert_no_horizontal_overflow(page, label=f"hub-{width}")
        screenshot(page, f"hub-{width}x{height}")
        context.close()
