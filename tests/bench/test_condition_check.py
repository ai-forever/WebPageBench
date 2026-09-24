"""Unit tests for condition matching: exact final quantity, not intermediate clicks."""

from __future__ import annotations

from lib.src.agent_bench.client import condition_matches_events


def _ev(name: str, **data) -> dict:
    return {"event_name": name, "event_data": data}


def test_basket_amount_fails_when_final_qty_is_higher():
    condition = {
        "event_name": "basket_add",
        "parameters": {"item_id": "item_647371114", "amount": 2},
    }
    events = [
        _ev("basket_add", item_id="item_647371114", amount=1),
        _ev("basket_add", item_id="item_647371114", amount=2),
        _ev("basket_add", item_id="item_647371114", amount=3),
    ]
    assert condition_matches_events(condition, events) is False


def test_basket_amount_passes_on_exact_final_qty():
    condition = {
        "event_name": "basket_add",
        "parameters": {"item_id": "item_647371114", "amount": 2},
    }
    events = [
        _ev("basket_add", item_id="item_647371114", amount=1),
        _ev("basket_add", item_id="item_647371114", amount=2),
    ]
    assert condition_matches_events(condition, events) is True


def test_basket_amount_uses_last_remove_as_final_qty():
    condition = {
        "event_name": "basket_add",
        "parameters": {"item_id": "item_x", "amount": 2},
    }
    events = [
        _ev("basket_add", item_id="item_x", amount=3),
        _ev("basket_remove", item_id="item_x", amount=2),
    ]
    assert condition_matches_events(condition, events) is True


def test_basket_amount_one_fails_after_extra_add():
    condition = {
        "event_name": "basket_add",
        "parameters": {"item_id": "item_named", "amount": 1},
    }
    events = [
        _ev("basket_add", item_id="item_named", amount=1),
        _ev("basket_add", item_id="item_named", amount=2),
    ]
    assert condition_matches_events(condition, events) is False


def test_basket_without_amount_still_matches_any_add():
    condition = {
        "event_name": "basket_add",
        "parameters": {"item_id": "item_any"},
    }
    events = [
        _ev("basket_add", item_id="item_any", amount=1),
        _ev("basket_add", item_id="item_any", amount=5),
    ]
    assert condition_matches_events(condition, events) is True


def test_other_item_qty_does_not_override_target_item():
    condition = {
        "event_name": "basket_add",
        "parameters": {"item_id": "item_a", "amount": 2},
    }
    events = [
        _ev("basket_add", item_id="item_a", amount=2),
        _ev("basket_add", item_id="item_b", amount=9),
    ]
    assert condition_matches_events(condition, events) is True


def test_state_changed_still_matches_historical_visit():
    condition = {
        "event_name": "state_changed",
        "parameters": {"new_state": "bench_catalog_item"},
    }
    events = [
        _ev("state_changed", new_state="bench_catalog_item"),
        _ev("state_changed", new_state="bench_catalog_main"),
    ]
    assert condition_matches_events(condition, events) is True


def test_select_seat_uses_final_seats_amount():
    condition = {
        "event_name": "select_seat",
        "parameters": {"seats_amount": 1},
    }
    events = [
        _ev("select_seat", seats_amount=1),
        _ev("select_seat", seats_amount=2),
    ]
    assert condition_matches_events(condition, events) is False
    assert condition_matches_events(
        {"event_name": "select_seat", "parameters": {"seats_amount": 2}},
        events,
    )


def test_hotel_guests_uses_final_count():
    condition = {
        "event_name": "bench_hotel_select_guests",
        "parameters": {"guestsCount": 2, "roomsCount": 1},
    }
    events = [
        _ev("bench_hotel_select_guests", guestsCount=2, roomsCount=1),
        _ev("bench_hotel_select_guests", guestsCount=3, roomsCount=1),
    ]
    assert condition_matches_events(condition, events) is False


def test_match_any_keeps_intermediate_basket_qty():
    condition = {
        "event_name": "basket_add",
        "match": "any",
        "parameters": {"item_id": "item_647371114", "amount": 2},
    }
    events = [
        _ev("basket_add", item_id="item_647371114", amount=2),
        _ev("basket_add", item_id="item_647371114", amount=3),
    ]
    assert condition_matches_events(condition, events) is True
