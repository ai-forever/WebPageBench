"""Pytest fixtures for bench UI tests (Playwright + WebPageBench backend)."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, sync_playwright

from bench_eval.ui_helpers import FRONTEND_URL, create_track, services_reachable

pytestmark = pytest.mark.ui


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "ui: Playwright UI tests (frontend + backend must be running)",
    )


@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {"headless": True}


@pytest.fixture(scope="session")
def browser_context_args():
    # accept_downloads is required by files cabinet download tests.
    return {"viewport": {"width": 1400, "height": 900}, "accept_downloads": True}


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    launched = playwright_instance.chromium.launch(headless=True)
    yield launched
    launched.close()


@pytest.fixture
def page(browser) -> Page:
    context = browser.new_context(
        viewport={"width": 1400, "height": 900}, accept_downloads=True
    )
    pg = context.new_page()
    pg.set_default_timeout(30_000)
    pg.set_default_navigation_timeout(30_000)
    yield pg
    context.close()


@pytest.fixture(scope="session")
def require_services():
    if not services_reachable():
        pytest.skip("WebPageBench backend and frontend must be running for UI tests")


@pytest.fixture(scope="session")
def hotel_track(require_services) -> str:
    return create_track("ui_hotels_bench", task_stem="hotel_search_scenario")


@pytest.fixture(scope="session")
def grocery_track(require_services) -> str:
    return create_track("ui_grocery_bench", task_stem="grocery_basket_any_product")


@pytest.fixture
def rail_track(require_services) -> str:
    return create_track("bench_rail_ui", task_stem="rail_book_to_cart")


@pytest.fixture
def grocery_base_url(grocery_track) -> str:
    return f"{FRONTEND_URL.rstrip('/')}/{grocery_track}"


@pytest.fixture
def fresh_grocery_page(page, grocery_base_url):
    """Grocery main page with cleared local storage."""
    page.goto(f"{grocery_base_url}/state_grocery_main/bench_grocery_main", wait_until="networkidle", timeout=60000)
    page.locator(".grocery-card").first.wait_for(state="visible", timeout=20000)
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="networkidle")
    page.locator(".grocery-card").first.wait_for(state="visible", timeout=20000)
    return page


@pytest.fixture(scope="session")
def files_track(require_services) -> str:
    return create_track("bench_ui_files", task_stem="files_select_collection")


@pytest.fixture
def files_base_url(files_track) -> str:
    return f"{FRONTEND_URL.rstrip('/')}/{files_track}"


@pytest.fixture
def require_services_for_taxonomy(require_services):
    """Alias for taxonomy tests (same as require_services)."""
    return require_services


@pytest.fixture
def taxonomy_track(require_services_for_taxonomy) -> str:
    """Fresh bench track per taxonomy test to avoid event cross-contamination."""
    from ui_taxonomy_helpers import make_taxonomy_track

    return make_taxonomy_track()
