"""Playwright helpers for unified bench rail (Поезда) UI tests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from bench_eval.bench_verify import BENCH_TESTS_DIR
from bench_eval.task_dates import iso_from_today
from bench_eval.ui_helpers import FRONTEND_URL as FRONTEND_BASE
STATE_ID = "state_rail_main"


RAIL_SEARCH_DATE = iso_from_today(7)


def rail_search_query(**overrides: str) -> dict[str, str]:
    query = {
        "from": "Москва",
        "to": "Санкт-Петербург",
        "date": RAIL_SEARCH_DATE,
        "adults": "1",
    }
    query.update(overrides)
    return query


def account_owner_name() -> str:
    """Name the rail passenger dropdown shows for the logged-in bench user.

    Read from the committed tests/bench/config.json persona instead of hardcoding
    it so the UI and test contract cannot drift.
    """
    config = json.loads((BENCH_TESTS_DIR / "config.json").read_text(encoding="utf-8"))
    user_data = config["domain_configs"]["rail"]["test_data"].get("user_data") or []
    first = user_data[0] if isinstance(user_data, list) and user_data else user_data
    name = (first or {}).get("name")
    if not name:
        raise AssertionError(
            "rail user_data[0] has no 'name': the account owner would be missing "
            "from the passenger dropdown"
        )
    return name

RAIL_PAGES: list[tuple[str, str, bool, str]] = [
    ("bench_rail_main", "main", False, "rail"),
    ("bench_rail_search", "search", False, "rail"),
    ("bench_rail_profile", "profile", False, "rail"),
    ("bench_rail_tarif_selection", "tariff", True, "rail"),
    ("bench_rail_seat_selection", "seat", True, "rail"),
    ("bench_rail_passenger_selection", "passenger", True, "rail"),
    ("bench_rail_tickets_checkout", "checkout", False, "rail"),
    ("bench_rail_tickets_payment", "payment", False, "payment"),
]


@dataclass
class LayoutSnapshot:
    top_nav: dict[str, float] | None
    header: dict[str, float] | None
    bench_nav_active: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "top_nav": self.top_nav,
            "header": self.header,
            "bench_nav_active": self.bench_nav_active,
        }


def hub_url(track_id: str) -> str:
    return f"{FRONTEND_BASE}/{track_id}/state_hub/bench_hub"


def rail_url(track_id: str, view_type: str, query: dict | None = None) -> str:
    base = f"{FRONTEND_BASE}/{track_id}/{STATE_ID}/{view_type}"
    if query:
        return f"{base}?{urlencode(query)}"
    return base


def capture_layout(page) -> LayoutSnapshot:
    page.evaluate("window.scrollTo(0, 0)")
    data = page.evaluate(
        """() => {
            const rect = (el) => {
              if (!el) return null;
              const r = el.getBoundingClientRect();
              return { x: r.x, y: r.y, w: r.width, h: r.height };
            };
            const active = document.querySelector('.bench-top-nav__link--active');
            return {
              top_nav: rect(document.querySelector('.bench-top-nav__inner')),
              header: rect(document.querySelector('.rail-header')),
              bench_nav_active: active ? active.textContent.trim() : null,
            };
        }"""
    )
    return LayoutSnapshot(
        top_nav=data.get("top_nav"),
        header=data.get("header"),
        bench_nav_active=data.get("bench_nav_active"),
    )


def assert_layout_stable(before: LayoutSnapshot, after: LayoutSnapshot, *, tolerance: float = 2.0) -> None:
    for label, a, b in (
        ("top_nav", before.top_nav, after.top_nav),
        ("header", before.header, after.header),
    ):
        if not a or not b:
            continue
        assert abs(a["x"] - b["x"]) <= tolerance, f"{label} x shifted: {a} -> {b}"
        assert abs(a["y"] - b["y"]) <= tolerance, f"{label} y shifted: {a} -> {b}"
        assert abs(a["w"] - b["w"]) <= tolerance, f"{label} width shifted: {a} -> {b}"


def _ensure_page_origin(page, track_id: str) -> None:
    if page.url.startswith("about:") or page.url == "about:blank":
        page.goto(rail_url(track_id, "bench_rail_main"), wait_until="domcontentloaded")


def seed_booking_session(page, track_id: str, *, adults: int = 1) -> None:
    _ensure_page_origin(page, track_id)
    payload = {
        "train": {
            "id": "train_sapsan",
            "number": "022",
            "name": "«экспресс»",
            "fromStation": "Москва",
            "toStation": "Санкт-Петербург",
            "fromStationType": "вокзал",
            "toStationType": "вокзал",
            "departureTime": "06:00",
            "arrivalTime": "10:05",
            "duration": "4 ч 5 мин",
            "durationMinutes": 245,
            "tickets": [
                {"type": "Эконом", "seats": 120, "price": 3500, "calculatedPrice": 3500},
                {"type": "Бизнес", "seats": 40, "price": 7500, "calculatedPrice": 7500},
            ],
            "amenities": ["mdi-wifi"],
            "isBranded": True,
        },
        "from": "Москва",
        "to": "Санкт-Петербург",
        "departureDate": RAIL_SEARCH_DATE,
        "adults": adults,
        "children": 0,
        "isReturnTrip": False,
        "selectedClass": {"type": "Эконом", "name": "Эконом", "price": 3500},
        "selectedSeats": [
            {
                "carriageId": "car_03",
                "carriageNumber": 3,
                "number": 12,
                "seatNumber": 12,
                "price": 3500,
            }
        ],
        "totalPrice": 3500 * adults,
    }
    page.evaluate(
        """([trackId, session]) => {
            const key = trackId ? `bench:${trackId}:bench_rail_booking_session` : 'bench_rail_booking_session';
            localStorage.setItem(key, JSON.stringify(session));
        }""",
        [track_id, payload],
    )


def seed_checkout_ticket(page, track_id: str, *, user: str = "bench@example.com") -> None:
    _ensure_page_origin(page, track_id)
    ticket = {
        "train": {
            "number": "022",
            "name": "«экспресс»",
            "fromStation": "Москва",
            "toStation": "Санкт-Петербург",
            "departureTime": "06:00",
            "arrivalTime": "10:05",
            "duration": "4 ч 5 мин",
        },
        "departureDate": RAIL_SEARCH_DATE,
        "selectedClass": {"name": "Эконом", "options": [{"code": "2Л"}]},
        "selectedSeats": [{"carriageNumber": 3, "seatNumber": 12, "price": 3500}],
        "passengers": [
            {
                "name": account_owner_name(),
                "documentType": "passport_rf",
                "documentNumber": "1234567890",
                "birthDate": "1990-01-01",
                "tariff": "full",
            }
        ],
        "totalPrice": 3500,
        "createdAt": f"{RAIL_SEARCH_DATE}T10:00:00.000Z",
    }
    page.evaluate(
        """([trackId, user, ticket]) => {
            const prefix = trackId ? `bench:${trackId}:` : '';
            const store = {};
            store[user] = [ticket];
            localStorage.setItem(prefix + 'bench_rail_tickets', JSON.stringify(store));
            localStorage.setItem(prefix + 'bench_rail_current_user', user);
            localStorage.setItem(prefix + 'bench_rail_ticket_current_user', user);
            localStorage.setItem(prefix + 'bench_rail_logged_in', 'true');
            localStorage.setItem(prefix + 'bench_rail_ticket_logged_in', 'true');
        }""",
        [track_id, user, ticket],
    )


def wait_rail_ready(page, *, timeout: int = 20000) -> None:
    page.wait_for_selector(".bench-rail", timeout=timeout)
    page.wait_for_function(
        "() => !document.querySelector('.loading-box')",
        timeout=timeout,
    )


def navigate_search_with_params(page, track_id: str) -> None:
    page.goto(
        rail_url(
            track_id,
            "bench_rail_search",
            rail_search_query(),
        ),
        wait_until="networkidle",
    )
    wait_rail_ready(page)


def complete_booking_to_checkout(page, track_id: str) -> None:
    navigate_search_with_params(page, track_id)
    page.locator(".train-card .buy-btn").first.click()
    page.wait_for_url("**/bench_rail_tarif_selection**")
    wait_rail_ready(page)

    economy = page.locator(".service-class-card", has_text="Эконом")
    (economy.first if economy.count() else page.locator(".service-class-card").first).click()
    page.locator("button.continue-btn").click()
    page.wait_for_url("**/bench_rail_seat_selection**")
    wait_rail_ready(page)

    seat = page.locator(".seats-group .seat-wrapper:not(.occupied)").first
    seat.click()
    page.locator("button.continue-btn").click()
    page.wait_for_url("**/bench_rail_passenger_selection**")
    wait_rail_ready(page)

    owner = account_owner_name()
    page.locator(".v-field").first.click()
    page.locator(".v-overlay-container .v-list-item", has_text=owner).first.click()

    tariff_fields = page.locator(".passenger-tariff .v-field, .tariff-select .v-field")
    for i in range(tariff_fields.count()):
        tariff_fields.nth(i).click()
        page.locator(".v-overlay-container .v-list-item").first.click()

    page.locator(".submit-order-btn").click()
    page.wait_for_url("**/bench_rail_tickets_checkout**")
    wait_rail_ready(page)


def read_tickets_store(page, track_id: str | None = None) -> dict:
    raw = page.evaluate(
        """(trackId) => {
            const keys = trackId
              ? [`bench:${trackId}:bench_rail_tickets`, 'bench_rail_tickets']
              : ['bench_rail_tickets'];
            for (const k of keys) {
              const v = localStorage.getItem(k);
              if (v) return v;
            }
            return null;
        }""",
        track_id,
    )
    return json.loads(raw) if raw else {}
