"""Playwright UI tests for the unified bench «Отели» section (bench_hotel_*)."""

from __future__ import annotations

import re

import pytest

from bench_eval.ui_helpers import (
    assert_position_stable,
    bbox,
    bench_nav,
    collect_js_errors,
    dismiss_shop_popup,
    event_names,
    get_track_events,
    hotel_detail_url,
    hotel_header_widgets,
    hotel_main_url,
    hotel_search_url,
    wait_event,
    wait_hotels_ready,
)

pytestmark = pytest.mark.ui


class TestHotelPagesLoad:
    """All three hotel view types render without errors."""

    def test_main_page(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        page.locator(".searchButton").wait_for(state="visible")
        assert "bench_hotel_main" in page.url
        assert "state_hotels_main" in page.url
        assert page.locator(".control-text").inner_text().strip() != "Войти"

    def test_search_page(self, page, hotel_track):
        page.goto(hotel_search_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        page.locator(".available-amount-text, .cards .card").first.wait_for(state="visible", timeout=20000)
        assert "bench_hotel_search" in page.url
        assert "state_hotels_search" in page.url
        assert page.locator("article.card, .card").count() >= 1

    def test_hotel_detail_page(self, page, hotel_track):
        page.goto(hotel_detail_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        page.locator(".roomOptions, .title").first.wait_for(state="visible", timeout=20000)
        assert "bench_hotel_hotel" in page.url
        assert "state_hotels_hotel" in page.url
        assert page.locator(".bookBtn").count() >= 1


class TestBenchNavAndHeaderStability:
    """Bench top nav and hotel header must not shift on reload or navigation."""

    @pytest.mark.parametrize(
        "url_fn,ready_selector",
        [
            (hotel_main_url, ".searchButton"),
            (hotel_search_url, ".available-amount-text, .cards .card"),
            (hotel_detail_url, ".roomOptions, .title"),
        ],
        ids=["main", "search", "hotel"],
    )
    def test_bench_nav_stable_on_reload(self, page, hotel_track, url_fn, ready_selector):
        page.goto(url_fn(hotel_track), wait_until="networkidle")
        page.locator(ready_selector).first.wait_for(state="visible", timeout=20000)
        nav = bench_nav(page)
        nav.wait_for(state="visible")
        before = bbox(nav)
        page.reload(wait_until="networkidle")
        page.locator(ready_selector).first.wait_for(state="visible", timeout=20000)
        assert_position_stable(before, bbox(nav), label="bench-top-nav")

    @pytest.mark.parametrize(
        "url_fn,ready_selector",
        [
            (hotel_main_url, ".searchButton"),
            (hotel_search_url, ".available-amount-text, .cards .card"),
            (hotel_detail_url, ".roomOptions, .title"),
        ],
        ids=["main", "search", "hotel"],
    )
    def test_hotel_header_widgets_stable_on_reload(self, page, hotel_track, url_fn, ready_selector):
        page.goto(url_fn(hotel_track), wait_until="networkidle")
        page.locator(ready_selector).first.wait_for(state="visible", timeout=20000)
        widgets = hotel_header_widgets(page)
        widgets.wait_for(state="visible")
        before = bbox(widgets)
        page.reload(wait_until="load")
        page.locator(ready_selector).first.wait_for(state="visible", timeout=20000)
        assert_position_stable(before, bbox(widgets), label="hotel-header-widgets")

    @pytest.mark.parametrize(
        "url_fn",
        [hotel_main_url, hotel_search_url, hotel_detail_url],
        ids=["main", "search", "hotel"],
    )
    def test_hotels_tab_active(self, page, hotel_track, url_fn):
        page.goto(url_fn(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        active = page.locator(".bench-top-nav__link--active")
        active.wait_for(state="visible")
        assert "Отели" in active.inner_text()


class TestConsistentStyle:
    """Visual consistency across hotel pages under bench anonymization."""

    BENCH_PRIMARY = "rgb(74, 111, 165)"
    BENCH_HEADER = "rgb(61, 90, 128)"
    BENCH_LIGHT = "rgb(228, 235, 244)"
    BENCH_SURFACE = "rgb(240, 243, 247)"
    BENCH_TEXT = "rgb(44, 62, 80)"
    LEGACY_BRAND_BLUE = "rgb(14, 65, 210)"

    def test_shell_uses_bench_surface_not_primary(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        bg = page.locator(".bench-hotels").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        assert bg == self.BENCH_SURFACE, f"bench-hotels background should be bench-surface, got {bg}"

    def test_inner_header_stays_white(self, page, hotel_track):
        page.goto(hotel_search_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        bg = page.locator(".bench-hotels > header > header").first.evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        assert bg == "rgb(255, 255, 255)"

    def test_search_button_uses_bench_primary(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        bg = page.locator(".searchButton").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        assert bg == self.BENCH_PRIMARY

    def test_header_icons_use_bench_primary_not_legacy_blue(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        color = page.locator(".widgets .icon-box").first.evaluate(
            "el => getComputedStyle(el).color"
        )
        assert color == self.BENCH_PRIMARY
        assert color != self.LEGACY_BRAND_BLUE

    def test_hero_uses_bench_gradient_not_brand_green(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        bg = page.locator(".promo.isRebranding").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        assert bg != "rgb(172, 239, 129)"

    def test_hero_title_matches_bench_header_tone(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        color = page.locator(".blockTitle").evaluate(
            "el => getComputedStyle(el).color"
        )
        assert color == self.BENCH_HEADER

    def test_search_cta_and_tabs_match_bench_palette(self, page, hotel_track):
        page.goto(hotel_search_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        btn_bg = page.locator(".btn").first.evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        tab_bg = page.locator(".tab-btn-active").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        assert btn_bg == self.BENCH_PRIMARY
        assert tab_bg == self.BENCH_LIGHT

    def test_book_button_uses_bench_primary(self, page, hotel_track):
        page.goto(hotel_detail_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        page.locator(".bookBtn").first.wait_for(state="visible", timeout=20000)
        bg = page.locator(".bookBtn").first.evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        assert bg == self.BENCH_PRIMARY

    def test_body_text_uses_bench_text_color(self, page, hotel_track):
        page.goto(hotel_search_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        color = page.locator(".available-amount-text").evaluate(
            "el => getComputedStyle(el).color"
        )
        assert color == self.BENCH_TEXT


class TestNavigationFlow:
    """Multi-step navigation: search → hotel → back, tab switching."""

    def test_search_from_main_uses_correct_state(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)

        dest = page.locator(".controlDestination input").first
        dest.click()
        dest.fill("Цюрих")
        page.locator(".opt").first.wait_for(state="visible", timeout=10000)
        page.locator(".opt").first.click()

        page.locator(".controlDates .cell.left, .controlDates button").first.click()
        days = page.locator(".dayBtn:not([disabled])")
        days.nth(10).wait_for(state="visible", timeout=10000)
        days.nth(10).click()
        days.nth(14).click()

        page.locator(".searchButton").click()
        page.wait_for_url(re.compile(r"bench_hotel_search"), timeout=15000)
        assert "state_hotels_search" in page.url
        page.locator(".available-amount-text, .cards .card").first.wait_for(state="visible", timeout=20000)

    def test_open_hotel_from_search(self, page, hotel_track):
        errors = collect_js_errors(page)
        page.goto(hotel_search_url(hotel_track), wait_until="networkidle")
        page.locator(".cards .card, article.card").first.wait_for(state="visible", timeout=20000)
        page.locator("button:has-text('Показать все номера')").first.click()
        page.wait_for_url(re.compile(r"bench_hotel_hotel"), timeout=15000)
        assert "state_hotels_hotel" in page.url
        page.locator(".roomOptions").wait_for(state="visible", timeout=15000)
        assert errors == [], f"JS errors: {errors}"

    def test_breadcrumb_back_to_search(self, page, hotel_track):
        page.goto(hotel_detail_url(hotel_track), wait_until="networkidle")
        page.locator(".roomOptions, .title").first.wait_for(state="visible", timeout=20000)
        page.locator("button.crumbLink").click()
        page.wait_for_url(re.compile(r"bench_hotel_search"), timeout=15000)
        assert "state_hotels_search" in page.url
        assert "hotelId" not in page.url

    def test_browser_back_forward(self, page, hotel_track):
        page.goto(hotel_search_url(hotel_track), wait_until="networkidle")
        page.locator(".cards .card, article.card").first.wait_for(state="visible", timeout=20000)
        page.locator("button:has-text('Показать все номера')").first.click()
        page.wait_for_url(re.compile(r"bench_hotel_hotel"), timeout=15000)
        page.go_back(wait_until="networkidle")
        page.locator(".available-amount-text, .cards .card").first.wait_for(state="visible", timeout=15000)
        page.go_forward(wait_until="networkidle")
        page.locator(".roomOptions, .title").first.wait_for(state="visible", timeout=15000)

    def test_logo_returns_to_main(self, page, hotel_track):
        page.goto(hotel_detail_url(hotel_track), wait_until="networkidle")
        page.locator(".roomOptions, .title").first.wait_for(state="visible", timeout=20000)
        link = page.locator(".logo a")
        href = link.get_attribute("href")
        assert href and "state_hotels_main" in href and "bench_hotel_main" in href
        link.evaluate("el => el.click()")
        page.wait_for_url(re.compile(r"bench_hotel_main"), timeout=15000)
        assert "state_hotels_main" in page.url


class TestRoomBooking:
    """Room selection (hotel booking) fires bench_hotel_select_room."""

    def test_book_room_sends_event(self, page, hotel_track):
        page.goto(hotel_detail_url(hotel_track), wait_until="networkidle")
        page.locator(".bookBtn").first.wait_for(state="visible", timeout=20000)
        page.locator(".bookBtn").first.click()
        wait_event(hotel_track, "bench_hotel_select_room")

    def test_book_room_opens_checkout(self, page, hotel_track):
        page.goto(hotel_detail_url(hotel_track), wait_until="networkidle")
        page.locator(".bookBtn").first.wait_for(state="visible", timeout=20000)
        page.locator(".bookBtn").first.click()
        page.wait_for_url(re.compile(r"bench_hotel_checkout"), timeout=15000)
        assert "orders/reserve" not in page.url
        page.locator(".hotel-checkout .checkout-title").wait_for(state="visible", timeout=15000)
        assert page.locator(".confirmBookBtn").count() >= 1

    def test_checkout_prefills_guest_info(self, page, hotel_track):
        page.goto(hotel_detail_url(hotel_track), wait_until="networkidle")
        page.locator(".bookBtn").first.wait_for(state="visible", timeout=20000)
        page.locator(".bookBtn").first.click()
        page.wait_for_url(re.compile(r"bench_hotel_checkout"), timeout=15000)
        page.locator(".guestInput").first.wait_for(state="visible", timeout=15000)
        name = page.locator('input[autocomplete="name"]').input_value()
        email = page.locator('input[autocomplete="email"]').input_value()
        phone = page.locator('input[autocomplete="tel"]').input_value()
        assert name.strip(), "guest name should be prefilled"
        assert "@" in email
        assert phone.strip(), "guest phone should be prefilled"

    def test_book_two_rooms_reaches_checkout(self, page, hotel_track):
        page.goto(hotel_detail_url(hotel_track), wait_until="networkidle")
        page.locator(".roomQtyPlus").first.wait_for(state="visible", timeout=20000)
        page.locator(".roomQtyPlus").first.click()
        assert "2" in page.locator(".roomQtyValue").first.inner_text()
        page.locator(".bookBtn").first.click()
        page.wait_for_url(re.compile(r"bench_hotel_checkout"), timeout=15000)
        page.locator(".roomQtySummary").first.wait_for(state="visible", timeout=15000)
        assert "2" in page.locator(".roomQtySummary").first.inner_text()
        page.locator(".confirmBookBtn").click()
        page.locator(".bookingSuccess").wait_for(state="visible", timeout=10000)

    def test_two_rooms_from_guest_picker_search(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)

        dest = page.locator(".controlDestination input").first
        dest.click()
        dest.fill("Милан")
        page.locator(".opt").first.wait_for(state="visible", timeout=10000)
        page.locator(".opt").first.click()

        page.locator(".controlDates .cell.left, .controlDates button").first.click()
        days = page.locator(".dayBtn:not([disabled])")
        days.nth(10).wait_for(state="visible", timeout=10000)
        days.nth(10).click()
        days.nth(14).click()

        page.locator(".controlGuests").first.click()
        page.locator(".addRoomBtn").first.wait_for(state="visible", timeout=5000)
        page.locator(".addRoomBtn").first.click()
        page.locator(".doneBtn").first.click()

        page.locator(".searchButton").click()
        page.wait_for_url(re.compile(r"bench_hotel_search"), timeout=15000)
        assert "rooms=2" in page.url
        assert "guests=4" in page.url

    def test_select_hotel_sends_event(self, page, hotel_track):
        page.goto(hotel_search_url(hotel_track), wait_until="networkidle")
        page.locator("button:has-text('Показать все номера')").first.wait_for(state="visible", timeout=20000)
        page.locator("button:has-text('Показать все номера')").first.click()
        page.wait_for_url(re.compile(r"bench_hotel_hotel"), timeout=15000)
        names = event_names(hotel_track)
        assert "bench_hotel_select_hotel" in names


class TestCrossDomainCart:
    """Switching to Маркет and back must preserve stable bench nav."""

    def test_shop_basket_from_hotels_and_back(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        nav_before = bbox(bench_nav(page))

        page.locator(".bench-top-nav__link:has-text('Маркет')").click()
        page.locator(".bench-market-header, .bench-market-header, .bench-top-nav").first.wait_for(
            state="visible", timeout=15000
        )
        # «Маркет» greets a guest with a full-screen address prompt whose backdrop
        # swallows clicks on the bench top nav — dismiss it before navigating.
        dismiss_shop_popup(page)

        basket_link = page.locator(
            "a[href*='bench_catalog_basket'], .controls a:has-text('Корзина')"
        ).first
        if basket_link.count():
            basket_link.click()
            page.locator(".bench-market, .bench-market").first.wait_for(state="visible", timeout=10000)
            dismiss_shop_popup(page)

        dismiss_shop_popup(page)
        page.locator(".bench-top-nav__link:has-text('Отели')").click()
        page.wait_for_url(re.compile(r"bench_hotel_main"), timeout=15000)
        wait_hotels_ready(page)
        assert_position_stable(nav_before, bbox(bench_nav(page)), label="bench-top-nav after domain switch")
        page.locator(".searchButton").wait_for(state="visible")


class TestAtomicInteractions:
    """Atomic UI steps matching tests/bench/tasks/hotel_atomic_*.json."""

    def test_select_city_event(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        dest = page.locator(".controlDestination input").first
        dest.click()
        dest.fill("Лион")
        page.locator(".opt").first.wait_for(state="visible", timeout=10000)
        page.locator(".opt").first.click()
        wait_event(hotel_track, "bench_hotel_select_city")

    def test_select_dates_events(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        page.locator(".controlDates .cell.left, .controlDates button").first.click()
        days = page.locator(".dayBtn:not([disabled])")
        days.nth(10).wait_for(state="visible", timeout=10000)
        days.nth(10).click()
        days.nth(14).click()
        wait_event(hotel_track, "bench_hotel_select_start_date")
        wait_event(hotel_track, "bench_hotel_select_end_date")

    def test_select_guests_event(self, page, hotel_track):
        page.goto(hotel_main_url(hotel_track), wait_until="networkidle")
        page.locator(".controlGuests").first.click()
        page.locator(".doneBtn, button:has-text('Готово')").first.wait_for(state="visible", timeout=5000)
        page.locator(".doneBtn, button:has-text('Готово')").first.click()
        wait_event(hotel_track, "bench_hotel_select_guests")


class TestNoJsErrors:
    """No uncaught JS exceptions on any hotel page."""

    @pytest.mark.parametrize(
        "url_fn",
        [hotel_main_url, hotel_search_url, hotel_detail_url],
        ids=["main", "search", "hotel"],
    )
    def test_no_page_errors(self, page, hotel_track, url_fn):
        errors = collect_js_errors(page)
        page.goto(url_fn(hotel_track), wait_until="networkidle")
        wait_hotels_ready(page)
        page.reload(wait_until="networkidle")
        wait_hotels_ready(page)
        assert errors == [], f"Uncaught errors: {errors}"
