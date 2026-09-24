"""Playwright UI tests for the unified bench «Продукты» (grocery) section."""

from __future__ import annotations

import re

import pytest

from bench_eval.ui_helpers import (
    assert_position_stable,
    bbox,
    grocery_basket_url,
    grocery_catalog_url,
    grocery_main_url,
    menu_bar,
)

pytestmark = pytest.mark.ui

MENU_LABELS = [
    "Собрали для вас",
    "От доставки",
    "Готовая еда",
    "Овощи и фрукты",
    "Молоко, яйца и сыр",
]

MENU_CATEGORY_STATES = [
    "tantsuyut_vse",
    "produkty_11",
    "vsyo_goryachee_1",
    "seychas_sezon",
    "molochnoe_i_yaytsa",
]

IN_BASKET_BG = "rgb(74, 111, 165)"  # --bench-primary


def _color_close(actual: str, expected: str, tolerance: int = 8) -> bool:
    def parse(rgb: str) -> tuple[int, int, int]:
        parts = rgb.replace("rgb(", "").replace(")", "").split(",")
        return tuple(int(p.strip()) for p in parts)

    a, e = parse(actual), parse(expected)
    return all(abs(x - y) <= tolerance for x, y in zip(a, e, strict=True))


def _wait_content(page, timeout: int = 15000) -> None:
    wait_ms = timeout if timeout >= 5000 else 15000
    url = page.url or ""
    if "bench_grocery_basket" in url:
        page.locator(".basket-page .section-title, .basket-placeholder, .basket-main").first.wait_for(
            state="visible", timeout=wait_ms
        )
        return
    if "bench_grocery_purchase" in url:
        page.locator(".basket-page .section-title, .basket-placeholder, .basket-main").first.wait_for(
            state="visible", timeout=wait_ms
        )
        return
    if "bench_grocery_category" in url:
        page.locator(".bench-grocery.category-view").first.wait_for(state="visible", timeout=wait_ms)
        page.locator(".grocery-card").first.wait_for(state="visible", timeout=wait_ms)
        return
    page.locator(".grocery-card").first.wait_for(state="visible", timeout=wait_ms)


def _in_basket_bg(page, selector: str) -> str:
    loc = page.locator(selector).first
    page.mouse.move(0, 0)
    page.wait_for_timeout(100)
    return loc.evaluate("el => getComputedStyle(el).backgroundColor")


def _click_basket_nav(page) -> None:
    page.locator(".menu-btn").filter(has_text="Корзина").first.click()


def _add_first_main_product(page) -> None:
    page.locator(".grocery-card .add-button").first.click()
    page.locator(".grocery-card .product-actions.in-basket, .overlay-quantity").first.wait_for(
        state="visible", timeout=10000
    )


class TestGroceryMainPage:
    def test_main_page_renders(self, fresh_grocery_page):
        page = fresh_grocery_page
        assert "bench_grocery_main" in page.url
        assert page.locator(".bench-grocery").count() >= 1
        assert page.locator(".searchbar").count() == 1
        assert page.locator(".menu-bar").count() == 1
        assert page.locator(".grocery-card").count() >= 10
        assert page.locator(".section-title").first.is_visible()

    def test_menu_has_all_sections(self, fresh_grocery_page):
        page = fresh_grocery_page
        items = page.locator(".menu-bar .menu-item")
        assert items.count() == len(MENU_LABELS)
        texts = [items.nth(i).inner_text().strip() for i in range(items.count())]
        assert texts == MENU_LABELS

    def test_main_page_survives_refresh(self, fresh_grocery_page):
        page = fresh_grocery_page
        nav = menu_bar(page)
        before = bbox(nav)
        page.reload(wait_until="networkidle")
        _wait_content(page)
        assert page.locator(".grocery-card").count() >= 10
        assert_position_stable(before, bbox(nav), label="menu-bar")


class TestGroceryMenuNavigation:
    @pytest.mark.parametrize(
        "index,label,state_id",
        [(i, label, state) for i, (label, state) in enumerate(zip(MENU_LABELS, MENU_CATEGORY_STATES, strict=True))],
    )
    def test_menu_item_opens_category(self, fresh_grocery_page, index, label, state_id):
        page = fresh_grocery_page
        page.locator(".menu-bar .menu-item").nth(index).click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        _wait_content(page)
        assert state_id in page.url
        assert "bench_grocery_category" in page.url
        assert page.locator(".bench-grocery.category-view").count() == 1
        assert page.locator(".searchbar").count() == 1
        assert page.locator(".section-title").first.is_visible()
        assert page.locator(".grocery-card").count() >= 5

    def test_catalog_menu_item_opens_category(self, fresh_grocery_page, grocery_track):
        page = fresh_grocery_page
        page.goto(grocery_catalog_url(grocery_track), wait_until="networkidle")
        page.locator(".catalog-page .section-title").first.wait_for(state="visible", timeout=15000)
        page.locator(".menu-bar .menu-item").first.click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        _wait_content(page)
        assert MENU_CATEGORY_STATES[0] in page.url
        assert page.locator(".bench-grocery.category-view").count() == 1
        assert page.locator(".grocery-card").count() >= 5

    def test_menu_position_stable_after_roundtrip(self, fresh_grocery_page, grocery_track):
        page = fresh_grocery_page
        nav = menu_bar(page)
        initial = bbox(nav)
        page.locator(".menu-bar .menu-item").first.click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        _wait_content(page)
        page.goto(grocery_main_url(grocery_track), wait_until="networkidle")
        _wait_content(page)
        assert_position_stable(initial, bbox(nav), label="menu-bar")


class TestGroceryCategoryPages:
    def test_category_survives_refresh(self, fresh_grocery_page):
        page = fresh_grocery_page
        page.locator(".menu-bar .menu-item").nth(2).click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        _wait_content(page)
        title_before = page.locator(".section-title").first.inner_text()
        page.reload(wait_until="networkidle")
        _wait_content(page)
        assert page.locator(".grocery-card").count() >= 5
        assert page.locator(".section-title").first.inner_text() == title_before

    def test_bench_nav_returns_to_main_from_category(self, fresh_grocery_page):
        page = fresh_grocery_page
        page.locator(".menu-bar .menu-item").first.click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        _wait_content(page)
        page.locator(".bench-top-nav__link").filter(has_text="Продукты").click()
        page.wait_for_url(re.compile(r"bench_grocery_main"), timeout=15000)
        _wait_content(page)
        assert "bench_grocery_main" in page.url
        assert page.locator(".menu-bar").count() == 1

    def test_left_sidebar_highlights_active_category(self, fresh_grocery_page):
        page = fresh_grocery_page
        page.locator(".menu-bar .menu-item").nth(3).click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        _wait_content(page)
        assert page.locator(".menu-bar .menu-item.active").count() >= 1


class TestGroceryBasketOnMain:
    def test_add_product_shows_in_basket_state(self, fresh_grocery_page):
        page = fresh_grocery_page
        _add_first_main_product(page)
        in_basket = page.locator(".grocery-card .product-actions.in-basket")
        assert in_basket.count() >= 1
        assert _color_close(_in_basket_bg(page, ".grocery-card .product-actions.in-basket"), IN_BASKET_BG)

    def test_basket_badge_updates(self, fresh_grocery_page):
        page = fresh_grocery_page
        basket_btn = page.locator(".menu-btn").filter(has_text="Корзина")
        badge = basket_btn.locator(".v-badge__badge")
        _add_first_main_product(page)
        badge.wait_for(state="visible", timeout=10000)
        assert int(badge.inner_text()) >= 1

    def test_decrement_removes_from_basket(self, fresh_grocery_page):
        page = fresh_grocery_page
        _add_first_main_product(page)
        page.locator(".grocery-card .decrease-button").first.click()
        _wait_content(page, 400)
        assert page.locator(".grocery-card .product-actions.in-basket").count() == 0


class TestGroceryBasketOnCategory:
    def test_add_on_category_page(self, fresh_grocery_page):
        page = fresh_grocery_page
        page.locator(".menu-bar .menu-item").first.click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        _wait_content(page)
        page.locator(".grocery-card .add-button").first.click()
        _wait_content(page, 600)
        in_basket = page.locator(".grocery-card .product-actions.in-basket")
        assert in_basket.count() >= 1
        assert _color_close(_in_basket_bg(page, ".grocery-card .product-actions.in-basket"), IN_BASKET_BG)


class TestGroceryBasketPage:
    def test_navigate_to_basket(self, fresh_grocery_page):
        page = fresh_grocery_page
        _add_first_main_product(page)
        _click_basket_nav(page)
        page.wait_for_url(re.compile(r"bench_grocery_basket"), timeout=15000)
        _wait_content(page)
        assert page.locator(".section-title").filter(has_text="Корзина").count() == 1
        assert page.locator(".basket-main .basket-item").count() >= 1

    def test_checkout_opens_purchase_page(self, fresh_grocery_page, grocery_track):
        page = fresh_grocery_page
        _add_first_main_product(page)
        page.goto(grocery_basket_url(grocery_track), wait_until="networkidle")
        _wait_content(page, 3000)
        page.locator(".purchase-btn").filter(has_text="Перейти к оформлению").click()
        page.wait_for_url(re.compile(r"bench_grocery_purchase"), timeout=15000)
        assert page.locator(".section-title").filter(has_text="Оформление заказа").count() == 1
        assert page.locator(".checkout-drawer").count() == 0
        assert page.locator(".pay-option").count() >= 3
        assert page.locator(".purchase-btn").filter(has_text="Пополнить и оплатить").count() == 1

    def test_basket_shows_items_and_summary(self, fresh_grocery_page, grocery_track):
        page = fresh_grocery_page
        _add_first_main_product(page)
        page.goto(grocery_basket_url(grocery_track), wait_until="networkidle")
        _wait_content(page, 3000)
        assert page.locator(".basket-main .basket-item").count() >= 1
        assert page.locator(".purchase-btn").filter(has_text="Перейти к оформлению").count() == 1
        assert page.locator(".checkout-drawer.open").count() == 0

    def test_basket_persists_after_refresh(self, fresh_grocery_page, grocery_track):
        page = fresh_grocery_page
        _add_first_main_product(page)
        page.goto(grocery_basket_url(grocery_track), wait_until="networkidle")
        _wait_content(page, 3000)
        page.reload(wait_until="networkidle")
        _wait_content(page, 3000)
        assert "bench_grocery_basket" in page.url
        assert page.locator(".basket-main .basket-item").count() >= 1

    def test_empty_basket_message(self, fresh_grocery_page, grocery_track):
        page = fresh_grocery_page
        page.goto(grocery_basket_url(grocery_track), wait_until="networkidle")
        _wait_content(page)
        assert page.locator(".basket-placeholder").filter(has_text="Корзина пуста").count() == 1


class TestGroceryNavigationRoundtrip:
    def test_basket_survives_main_category_roundtrip(self, fresh_grocery_page, grocery_track):
        page = fresh_grocery_page
        _add_first_main_product(page)
        page.locator(".menu-bar .menu-item").first.click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        _wait_content(page)
        page.goto(grocery_main_url(grocery_track), wait_until="networkidle")
        _wait_content(page)
        assert page.locator(".grocery-card .product-actions.in-basket").count() >= 1
        _click_basket_nav(page)
        page.wait_for_url(re.compile(r"bench_grocery_basket"), timeout=15000)
        _wait_content(page, 3000)
        assert page.locator(".basket-main .basket-item").count() >= 1

    def test_bench_top_nav_grocery_tab_active(self, fresh_grocery_page):
        page = fresh_grocery_page
        active = page.locator(".bench-top-nav__link--active")
        assert active.count() == 1
        assert "Продукты" in active.first.inner_text()

    def test_switch_section_and_return(self, fresh_grocery_page, grocery_track):
        page = fresh_grocery_page
        nav = menu_bar(page)
        menu_before = bbox(nav)
        page.locator(".bench-top-nav__link").filter(has_text="Книги").click()
        page.wait_for_url(re.compile(r"bench_books"), timeout=15000)
        page.locator(".bench-top-nav__link").filter(has_text="Продукты").click()
        page.wait_for_url(re.compile(r"bench_grocery"), timeout=15000)
        page.locator(".grocery-card").first.wait_for(state="visible", timeout=20000)
        assert page.locator(".grocery-card").count() >= 10
        assert_position_stable(menu_before, bbox(nav), label="menu-bar")


class TestGroceryStyleConsistency:
    def test_main_product_card_styles(self, fresh_grocery_page):
        page = fresh_grocery_page
        card = page.locator(".grocery-card").first
        radius = card.evaluate("el => getComputedStyle(el).borderRadius")
        assert radius in ("16px", "16px 16px 16px 16px")

    def test_category_product_card_matches_main_actions(self, fresh_grocery_page):
        page = fresh_grocery_page
        page.locator(".menu-bar .menu-item").first.click()
        page.wait_for_url(re.compile(r"bench_grocery_category"), timeout=15000)
        _wait_content(page)
        page.locator(".grocery-card .add-button").first.click()
        _wait_content(page, 600)
        assert _color_close(_in_basket_bg(page, ".grocery-card .product-actions.in-basket"), IN_BASKET_BG)

    def test_menu_bar_style_on_main(self, fresh_grocery_page):
        """bench.css styles the grocery menu bar as an elevated surface with
        --bench-text items (not the dark header palette), so assert against the
        theme tokens rather than hardcoded colors."""
        page = fresh_grocery_page
        expected = page.evaluate(
            """() => {
              const s = getComputedStyle(document.documentElement);
              const toRgb = (value) => {
                const probe = document.createElement('span');
                probe.style.color = value.trim();
                document.body.appendChild(probe);
                const rgb = getComputedStyle(probe).color;
                probe.remove();
                return rgb;
              };
              return {
                surface: toRgb(s.getPropertyValue('--bench-surface-elevated')),
                text: toRgb(s.getPropertyValue('--bench-text')),
                header: toRgb(s.getPropertyValue('--bench-header-bg')),
                primary: toRgb(s.getPropertyValue('--bench-primary')),
              };
            }"""
        )
        menu = page.locator(".menu-bar").first
        bg = menu.evaluate("el => getComputedStyle(el).backgroundColor")
        assert bg == expected["surface"]
        assert bg != expected["header"], "menu bar must not reuse the header colour"

        plain = page.locator(".menu-bar .menu-item:not(.orange)").first
        assert plain.count() >= 1, "no plain menu item to check"
        assert (
            plain.evaluate("el => getComputedStyle(el).color") == expected["text"]
        )

        highlighted = page.locator(".menu-bar .menu-item.orange").first
        if highlighted.count():
            assert (
                highlighted.evaluate("el => getComputedStyle(el).color")
                == expected["primary"]
            )
