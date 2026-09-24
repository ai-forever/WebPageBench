"""Playwright UI tests for unified bench rail (Поезда / bench_rail_*)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BENCH_DIR = Path(__file__).resolve().parent
if str(_BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(_BENCH_DIR))

from rail_ui_helpers import (
    RAIL_PAGES,
    assert_layout_stable,
    capture_layout,
    complete_booking_to_checkout,
    hub_url,
    navigate_search_with_params,
    rail_url,
    read_tickets_store,
    seed_booking_session,
    seed_checkout_ticket,
    wait_rail_ready,
)

pytestmark = pytest.mark.ui


class TestRailPagesLoad:
    @pytest.mark.parametrize("view_type,label,needs_session,layout_kind", RAIL_PAGES)
    def test_page_loads_without_error(
        self,
        page,
        rail_track: str,
        view_type: str,
        label: str,
        needs_session: bool,
        layout_kind: str,
    ):
        if needs_session:
            seed_booking_session(page, rail_track)

        page.goto(rail_url(rail_track, view_type), wait_until="networkidle")
        if layout_kind == "rail":
            wait_rail_ready(page)
            assert page.locator(".bench-rail").count() == 1
            assert page.locator(".bench-top-nav").count() == 1
            assert page.locator(".rail-header").count() == 1
        else:
            page.wait_for_selector(".payment-gateway", timeout=20000)
            assert page.locator(".payment-gateway").count() == 1

        assert view_type in page.url


class TestRailLayoutStability:
    def test_top_nav_and_header_stable_on_reload(self, page, rail_track: str):
        page.goto(rail_url(rail_track, "bench_rail_main"), wait_until="networkidle")
        wait_rail_ready(page)

        before = capture_layout(page)
        page.reload(wait_until="networkidle")
        wait_rail_ready(page)
        after = capture_layout(page)
        assert_layout_stable(before, after)

    def test_layout_stable_main_to_search_and_back(self, page, rail_track: str):
        page.goto(rail_url(rail_track, "bench_rail_main"), wait_until="networkidle")
        wait_rail_ready(page)
        main_layout = capture_layout(page)

        navigate_search_with_params(page, rail_track)
        search_layout = capture_layout(page)
        assert_layout_stable(main_layout, search_layout)

        page.go_back(wait_until="networkidle")
        wait_rail_ready(page)
        back_layout = capture_layout(page)
        assert_layout_stable(main_layout, back_layout)

    @pytest.mark.parametrize(
        "view_type,_,needs_session,layout_kind",
        [item for item in RAIL_PAGES if item[0] != "bench_rail_main" and item[3] == "rail"],
    )
    def test_rail_tab_stays_active_on_subpages(
        self,
        page,
        rail_track: str,
        view_type: str,
        _,
        needs_session: bool,
        layout_kind: str,
    ):
        if needs_session:
            seed_booking_session(page, rail_track)

        page.goto(rail_url(rail_track, view_type), wait_until="networkidle")
        wait_rail_ready(page)
        layout = capture_layout(page)
        assert layout.bench_nav_active == "Поезда", layout.as_dict()


class TestRailNavigation:
    def test_hub_to_rail_main(self, page, rail_track: str):
        page.goto(hub_url(rail_track), wait_until="networkidle")
        page.locator(".bench-top-nav__link", has_text="Поезда").click()
        page.wait_for_url("**/bench_rail_main**")
        wait_rail_ready(page)
        assert capture_layout(page).bench_nav_active == "Поезда"

    def test_profile_survives_reload_when_logged_in(self, page, rail_track: str):
        page.goto(rail_url(rail_track, "bench_rail_profile"), wait_until="networkidle")
        wait_rail_ready(page)
        assert "bench_rail_profile" in page.url
        page.reload(wait_until="networkidle")
        wait_rail_ready(page)
        assert "bench_rail_profile" in page.url
        assert page.locator(".profile-hero-title").count() == 1


class TestRailTheme:
    def test_primary_buttons_use_bench_palette(self, page, rail_track: str):
        page.goto(rail_url(rail_track, "bench_rail_main"), wait_until="networkidle")
        wait_rail_ready(page)

        btn_bg = page.locator(".rail-search-widget .search-btn").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        header_bg = page.locator(".rail-header").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        page_bg = page.locator(".bench-rail").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        assert btn_bg == "rgb(74, 111, 165)"
        assert header_bg == "rgb(255, 255, 255)"
        assert page_bg == "rgb(240, 243, 247)"


class TestRailHeaderConsistency:
    def test_flow_pages_use_search_header(self, page, rail_track: str):
        navigate_search_with_params(page, rail_track)
        assert page.locator(".rail-search-header").count() == 1
        assert page.locator(".rail-header .main-nav").count() == 0

    def test_main_uses_full_header_menu(self, page, rail_track: str):
        page.goto(rail_url(rail_track, "bench_rail_main"), wait_until="networkidle")
        wait_rail_ready(page)
        assert page.locator(".rail-header .main-nav").count() == 1
        assert page.locator(".rail-search-header").count() == 0


class TestRailBookingCart:
    def test_booking_flow_reaches_checkout(self, page, rail_track: str):
        complete_booking_to_checkout(page, rail_track)
        assert "bench_rail_tickets_checkout" in page.url
        assert page.locator(".checkout-title", has_text="Заказ готов к оплате").count() == 1

    def test_ticket_saved_to_cart_storage(self, page, rail_track: str):
        complete_booking_to_checkout(page, rail_track)
        store = read_tickets_store(page, rail_track)
        assert store, "ticket basket localStorage should not be empty"
        user_tickets = next(iter(store.values()))
        assert len(user_tickets) >= 1
        assert user_tickets[0]["train"]["name"]

    def test_checkout_cart_design_elements(self, page, rail_track: str):
        complete_booking_to_checkout(page, rail_track)

        before = capture_layout(page)
        assert page.locator(".checkout-title").count() == 1
        assert page.locator(".route-card").count() >= 1
        assert page.locator(".passenger-block").count() >= 1
        assert page.locator(".terms-section").count() == 1

        page.reload(wait_until="networkidle")
        wait_rail_ready(page)
        after = capture_layout(page)
        assert_layout_stable(before, after)
        assert page.locator(".checkout-title").count() == 1

    def test_checkout_to_payment_preserves_checkout_design(self, page, rail_track: str):
        complete_booking_to_checkout(page, rail_track)

        page.locator(".terms-checkbox").nth(0).click()
        page.locator(".terms-checkbox").nth(1).click()
        page.locator("button:has-text('Оплатить')").click()
        page.wait_for_url("**/bench_rail_tickets_payment**", timeout=15000)
        page.wait_for_selector(".payment-gateway", timeout=20000)
        assert page.locator(".payment-gateway .pg-header").count() == 1
        assert page.locator(".payment-form, .pg-main").count() >= 1
