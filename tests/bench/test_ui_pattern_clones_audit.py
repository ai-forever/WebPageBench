"""Playwright audit of unique UI-pattern clones (click/type, overflow, screenshots)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

_BENCH_DIR = Path(__file__).resolve().parent
if str(_BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(_BENCH_DIR))

from bench_eval.page_audit import (
    assert_click_target_not_covered,
    assert_no_horizontal_overflow,
    assert_pairs_do_not_overlap,
    attach_network_listeners,
    screenshot,
)
from bench_eval.task_dates import booking_iso_pair, iso_from_today
from bench_eval.ui_helpers import (
    collect_js_errors,
    create_track,
    files_cabinet_url,
    grocery_main_url,
    hotel_main_url,
)
from golden_path_runners import (
    _fill_hotel_dates,
    _pick_rail_date,
    _select_hotel_city_variant,
    _select_rail_station_variant,
    _set_hotel_guests,
    run_task,
)
from rail_ui_helpers import rail_url, wait_rail_ready
from ui_taxonomy_helpers import (
    BOOKS_SEARCH_QUERY,
    books_main_url,
    dismiss_shop_popup,
    fill_books_search,
    open_files_collection,
    pause,
    select_files_year,
    shop_main_url,
    wait_books_ready,
    wait_files_ready,
    wait_shop_ready,
)

pytestmark = pytest.mark.ui

NAV_HEADER_PAIRS = [
    (".bench-top-nav", ".bench-market-header, .rail-header, .searchbar, .bench-hotels .widgets"),
]


@dataclass(frozen=True)
class AuditCase:
    pattern: str
    stem: str
    domain: str
    widget: str
    cta: str | None = None
    golden: bool = True
    render_only: bool = False


WIDGET_CASES: tuple[AuditCase, ...] = (
    AuditCase("date:inline_calendar", "hotel_search_scenario__date_inline_calendar", "hotels", ".dayBtn", ".searchButton"),
    AuditCase("date:text_input", "hotel_search_scenario__date_text_input", "hotels", ".date-text-input", ".searchButton"),
    AuditCase("date:single_popup", "hotel_search_scenario__date_single_popup", "hotels", ".singleCell, .singlePopup button", ".searchButton"),
    AuditCase("select_city:native_select", "hotel_search_scenario__select_city_native_select", "hotels", "select.native-select", ".searchButton"),
    AuditCase("counter_guests:inline_stepper", "hotel_search_scenario__counter_guests_inline_stepper", "hotels", ".step-btn", ".searchButton"),
    AuditCase("counter_guests:compact_select", "hotel_search_scenario__counter_guests_compact_select", "hotels", "select.compact-select", ".searchButton"),
    AuditCase("counter_guests:pill_buttons", "hotel_search_scenario__counter_guests_pill_buttons", "hotels", ".pill", ".searchButton"),
    AuditCase("date:native_input", "rail_book_to_cart__date_native_input", "rail", ".native-date-input, input[type='date']", ".rail-search-widget .search-btn"),
    AuditCase("date:text_input", "rail_book_to_cart__date_text_input", "rail", ".text-date-input", ".rail-search-widget .search-btn"),
    AuditCase("select_station:native_select", "rail_book_to_cart__select_station_native_select", "rail", ".bench-rail-station-native .native-select, select.native-select", ".rail-search-widget .search-btn"),
    AuditCase(
        "files:list+years:buttons+buttons:icon",
        "files_download_pdf__files_list_buttons_icon",
        "files",
        ".bench-files__layout--list",
        ".bench-files__nav-btn",
    ),
    AuditCase("text_search:outlined", "ecommerce_basket_named_product_02__text_search_outlined", "shop", ".bench-search--outlined", None),
    AuditCase("text_search:filled", "ecommerce_basket_named_product_02__text_search_filled", "shop", ".bench-search--filled", None),
    AuditCase("text_search:underlined", "ecommerce_basket_named_product_02__text_search_underlined", "shop", ".bench-search--underlined", None),
    AuditCase("text_search:pill", "ecommerce_basket_named_product_02__text_search_pill", "shop", ".bench-search--pill", None),
    AuditCase("text_search:pill", "digital_books_named_product_basket__text_search_pill", "books", ".bench-search--pill", ".searchbar .search-btn"),
    AuditCase(
        "counter_guests:pill_buttons",
        "hotel_search_scenario_family__counter_guests_pill_buttons",
        "hotels",
        ".pill",
        ".searchButton",
        golden=False,
        render_only=True,
    ),
    AuditCase(
        "counter_guests:pill_buttons",
        "hotel_search_scenario_two_rooms__counter_guests_pill_buttons",
        "hotels",
        ".pill",
        ".searchButton",
        golden=False,
        render_only=True,
    ),
)

THEME_CASES: tuple[AuditCase, ...] = (
    AuditCase("theme:dark", "ecommerce_basket_named_product_02__theme_dark", "shop", "html[data-bench-theme='dark']"),
    AuditCase("theme:dark", "digital_books_named_product_basket__theme_dark", "books", "html[data-bench-theme='dark']"),
    AuditCase("theme:dark", "grocery_basket_named_product__theme_dark", "grocery", "html[data-bench-theme='dark']", ".grocery-card .add-button"),
    AuditCase("theme:dark", "rail_book_to_cart__theme_dark", "rail", "html[data-bench-theme='dark']", ".rail-search-widget .search-btn"),
    AuditCase("theme:dark", "hotel_search_scenario__theme_dark", "hotels", "html[data-bench-theme='dark']", ".searchButton"),
    AuditCase("theme:dark", "files_download_pdf__theme_dark", "files", "html[data-bench-theme='dark']", ".bench-files__nav-btn"),
)

ALL_CASES = WIDGET_CASES + THEME_CASES
GOLDEN_STEMS = tuple(case.stem for case in ALL_CASES if case.golden)


def _url_for(domain: str, track_id: str) -> str:
    if domain == "hotels":
        return hotel_main_url(track_id)
    if domain == "rail":
        return rail_url(track_id, "bench_rail_main")
    if domain == "files":
        return files_cabinet_url(track_id)
    if domain == "shop":
        return shop_main_url(track_id)
    if domain == "books":
        return books_main_url(track_id)
    if domain == "grocery":
        return grocery_main_url(track_id)
    raise KeyError(domain)


def _wait_ready(page, domain: str) -> None:
    if domain == "hotels":
        page.locator(".searchButton").wait_for(state="visible", timeout=20000)
    elif domain == "rail":
        wait_rail_ready(page)
    elif domain == "files":
        wait_files_ready(page)
    elif domain == "shop":
        wait_shop_ready(page)
        dismiss_shop_popup(page)
    elif domain == "books":
        wait_books_ready(page)
    elif domain == "grocery":
        page.locator(".grocery-card").first.wait_for(state="visible", timeout=20000)


def _audit_layout(page, name: str, *, cta: str | None) -> None:
    screenshot(page, f"{name}-fold")
    assert_no_horizontal_overflow(page, label=name)
    assert_pairs_do_not_overlap(page, NAV_HEADER_PAIRS, label=name)
    if page.locator(".bench-date-inline").count():
        assert_pairs_do_not_overlap(
            page,
            [(".bench-date-inline", ".homepageMainWrapper")],
            label=name,
        )
    if cta:
        loc = page.locator(cta).first
        if loc.count():
            loc.scroll_into_view_if_needed()
            pause(page, 200)
        try:
            assert_click_target_not_covered(page, cta, label=name)
        except Exception:
            screenshot(page, f"{name}-covered")
            raise


def _interact_widget(page, case: AuditCase, track_id: str) -> None:
    if case.render_only:
        return
    if case.domain == "hotels" and case.pattern.startswith("date:"):
        start, end = booking_iso_pair(14, 5)
        variant = case.pattern.split(":", 1)[1]
        _fill_hotel_dates(page, start, end, date_variant=variant)
        return
    if case.pattern == "select_city:native_select":
        city = {"cityId": "ch-zrh", "label": "Цюрих, Швейцария", "cityName": "Цюрих"}
        _select_hotel_city_variant(page, city)
        return
    if case.pattern.startswith("counter_guests:"):
        variant = case.pattern.split(":", 1)[1]
        _set_hotel_guests(page, {"rooms": [{"adults": 2, "kids": []}]}, counter_variant=variant)
        return
    if case.domain == "rail" and case.pattern.startswith("date:"):
        _pick_rail_date(page, iso_from_today(7))
        return
    if case.pattern == "select_station:native_select":
        _select_rail_station_variant(page, "from", "Москва")
        _select_rail_station_variant(page, "to", "Санкт-Петербург")
        return
    if case.domain == "files":
        open_files_collection(page, track_id, "Отчёты лаборатории")
        page.locator(".bench-files__year").filter(has_text="2024").first.wait_for(state="visible", timeout=10000)
        select_files_year(page, "2024")
        icon = page.locator(".bench-files__btn--icon, a.icon-button").first
        icon.wait_for(state="visible", timeout=10000)
        with page.expect_download(timeout=15000):
            icon.click()
        return
    if case.domain == "shop":
        search = page.locator(".bench-market-header .search-input input, .search-input input").first
        search.click()
        search.fill("whiskas")
        search.press("Enter")
        pause(page, 800)
        return
    if case.domain == "books":
        fill_books_search(page, BOOKS_SEARCH_QUERY)
        return


def _parse_css_rgb(value: str) -> tuple[int, int, int] | None:
    raw = (value or "").strip().lower()
    if raw.startswith("#") and len(raw) == 7:
        return int(raw[1:3], 16), int(raw[3:5], 16), int(raw[5:7], 16)
    if raw.startswith("rgb"):
        nums = [int(part) for part in raw.replace("rgba", "rgb").strip("rgb() ").split(",")[:3]]
        if len(nums) == 3:
            return nums[0], nums[1], nums[2]
    return None


def _is_dark_rgb(rgb: tuple[int, int, int] | None) -> bool:
    if not rgb:
        return False
    r, g, b = rgb
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) < 140


def _assert_theme_dark(page, label: str) -> None:
    info = page.evaluate(
        """() => {
          const html = document.documentElement;
          const root = document.querySelector('.v-main.bench-anonymized, .bench-anonymized') || html;
          const cs = getComputedStyle(root);
          return {
            theme: html.getAttribute('data-bench-theme'),
            surface: cs.getPropertyValue('--bench-surface').trim(),
            bg: cs.backgroundColor,
          };
        }"""
    )
    assert info["theme"] == "dark", f"{label}: expected data-bench-theme=dark, got {info['theme']!r}"
    surface_rgb = _parse_css_rgb(info["surface"]) or _parse_css_rgb(info["bg"])
    assert _is_dark_rgb(surface_rgb), (
        f"{label}: --bench-surface is still light ({info['surface']!r}, bg={info['bg']!r})"
    )


def _assert_text_search_style(page, case: AuditCase) -> None:
    variant = case.pattern.split(":", 1)[1]
    info = page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return null;
          const cs = getComputedStyle(el);
          const radius = parseFloat(cs.borderRadius) || 0;
          const bottom = parseFloat(cs.borderBottomWidth) || 0;
          const minH = parseFloat(cs.minHeight) || el.getBoundingClientRect().height;
          const border = parseFloat(cs.borderTopWidth) || 0;
          return { radius, bottom, minH, bg: cs.backgroundColor, border };
        }""",
        case.widget,
    )
    assert info, f"{case.stem}: {case.widget} not in DOM for style check"
    if variant == "pill":
        assert info["radius"] >= 20, f"{case.stem}: pill radius {info['radius']} < 20"
    elif variant == "underlined":
        assert info["bottom"] >= 2, f"{case.stem}: underlined bottom border {info['bottom']}"
        assert info["radius"] == 0, f"{case.stem}: underlined should be square, radius={info['radius']}"
    elif variant == "outlined":
        assert info["border"] >= 1, f"{case.stem}: outlined missing border {info}"


def _goto_case(page, case: AuditCase, track_id: str) -> None:
    page.goto(_url_for(case.domain, track_id), wait_until="networkidle", timeout=30000)
    _wait_ready(page, case.domain)


@pytest.mark.parametrize("case", ALL_CASES, ids=[f"{c.pattern}__{c.stem}" for c in ALL_CASES])
def test_ui_pattern_clone_widget(page, require_services, case: AuditCase):
    js_errors = collect_js_errors(page)
    bag = attach_network_listeners(page)
    track_id = create_track(f"aud_{case.stem}"[:80], task_stem=case.stem)
    _goto_case(page, case, track_id)

    widget = page.locator(case.widget).first
    widget.wait_for(state="visible", timeout=15000)
    assert widget.is_visible(), f"{case.stem}: widget {case.widget} not visible"
    if case.pattern.startswith("text_search:"):
        _assert_text_search_style(page, case)

    slug = case.stem.replace("__", "-")
    _audit_layout(page, slug, cta=case.cta)

    if case.pattern == "theme:dark":
        _assert_theme_dark(page, case.stem)
        screenshot(page, f"{slug}-theme")
    else:
        _interact_widget(page, case, track_id)
        screenshot(page, f"{slug}-after")
        assert_no_horizontal_overflow(page, label=f"{case.stem}-after")

    page_errors = [err for err in js_errors if "ResizeObserver" not in err]
    assert not page_errors, f"{case.stem} pageerror: {page_errors}"
    failed = bag.get("failed") or []
    http_error = bag.get("http_error") or []
    assert not failed, f"{case.stem} failed assets: {failed[:5]}"
    assert not http_error, f"{case.stem} http asset errors: {http_error[:5]}"


@pytest.mark.parametrize("stem", GOLDEN_STEMS)
def test_ui_pattern_clone_golden_path(page, require_services, stem: str):
    track_id = create_track(f"gp_{stem}"[:80], task_stem=stem)
    run_task(page, track_id, stem)


