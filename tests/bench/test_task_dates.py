"""Booking dates in hotel/rail tasks roll forward so they are never before today."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from bench_eval.bench_verify import BENCH_TESTS_DIR
from bench_eval.task_dates import (
    apply_booking_dates,
    format_dotted,
    iso_from_today,
)


def _cond_dates(task: dict) -> list[str]:
    out = []
    for cond in task.get("test_data", {}).get("conditions") or []:
        params = cond.get("parameters") if isinstance(cond.get("parameters"), dict) else {}
        if "date" in params:
            out.append(params["date"])
    return out


def test_iso_from_today_never_before_today():
    today = date(2026, 8, 28)
    assert iso_from_today(0, today=today) == "2026-08-28"
    assert iso_from_today(7, today=today) == "2026-09-04"


def test_future_iso_dates_stay_put():
    task = {
        "test_data": {
            "task": "заезд 15.09.2026, выезд 20.09.2026",
            "conditions": [
                {"event_name": "bench_hotel_select_start_date", "parameters": {"date": "2026-09-15"}},
                {"event_name": "bench_hotel_select_end_date", "parameters": {"date": "2026-09-20"}},
            ],
        }
    }
    apply_booking_dates(task, today=date(2026, 8, 28))
    assert _cond_dates(task) == ["2026-09-15", "2026-09-20"]
    assert task["test_data"]["task"] == "заезд 15.09.2026, выезд 20.09.2026"


def test_past_iso_dates_shift_with_gap():
    task = {
        "test_data": {
            "task": "заезд 15.09.2026, выезд 20.09.2026",
            "conditions": [
                {"event_name": "bench_hotel_select_start_date", "parameters": {"date": "2026-09-15"}},
                {"event_name": "bench_hotel_select_end_date", "parameters": {"date": "2026-09-20"}},
            ],
        }
    }
    apply_booking_dates(task, today=date(2026, 10, 1))
    assert _cond_dates(task) == ["2026-10-01", "2026-10-06"]
    assert task["test_data"]["task"] == "заезд 01.10.2026, выезд 06.10.2026"


def test_long_form_and_padded_day():
    task = {
        "test_data": {
            "task": "выбери дату отправления 04 октября 2026.",
            "conditions": [
                {"event_name": "select_date", "parameters": {"date": "2026-10-04"}},
            ],
        }
    }
    apply_booking_dates(task, today=date(2026, 11, 2))
    assert _cond_dates(task) == ["2026-11-02"]
    assert "02 ноября 2026" in task["test_data"]["task"]


def test_long_span_unpadded():
    task = {
        "test_data": {
            "task": "с 15 по 20 сентября 2026 для 2 взрослых",
            "conditions": [
                {"event_name": "bench_hotel_select_start_date", "parameters": {"date": "2026-09-15"}},
                {"event_name": "bench_hotel_select_end_date", "parameters": {"date": "2026-09-20"}},
            ],
        }
    }
    apply_booking_dates(task, today=date(2026, 10, 1))
    assert "с 1 по 6 октября 2026" in task["test_data"]["task"]


def test_long_span_padded():
    task = {
        "test_data": {
            "task": "с 01 по 05 октября 2026 для 2 гостей",
            "conditions": [
                {"event_name": "bench_hotel_select_start_date", "parameters": {"date": "2026-10-01"}},
                {"event_name": "bench_hotel_select_end_date", "parameters": {"date": "2026-10-05"}},
            ],
        }
    }
    apply_booking_dates(task, today=date(2026, 11, 8))
    assert "с 08 по 12 ноября 2026" in task["test_data"]["task"]


def test_dotted_range_en_dash():
    task = {
        "test_data": {
            "task": "на 12–16.09.2026: два номера",
            "conditions": [
                {"event_name": "bench_hotel_select_start_date", "parameters": {"date": "2026-09-12"}},
                {"event_name": "bench_hotel_select_end_date", "parameters": {"date": "2026-09-16"}},
            ],
        }
    }
    apply_booking_dates(task, today=date(2026, 10, 1))
    assert "01–05.10.2026" in task["test_data"]["task"]
    assert _cond_dates(task) == ["2026-10-01", "2026-10-05"]


def test_offset_token_resolves_from_today():
    task = {
        "test_data": {
            "task": "на поезд",
            "conditions": [
                {"event_name": "select_date", "parameters": {"date": "+14d"}},
            ],
        }
    }
    apply_booking_dates(task, today=date(2026, 8, 28))
    assert _cond_dates(task) == ["2026-09-11"]


def test_files_dates_are_not_shifted():
    task = {
        "test_data": {
            "task": "скачай project-archive-2024-03-31.pdf",
            "conditions": [
                {
                    "event_name": "bench_files_download",
                    "parameters": {"file": "project-archive-2024-03-31.pdf", "year": "2024"},
                }
            ],
        }
    }
    apply_booking_dates(task, today=date(2026, 10, 1))
    assert "2024-03-31" in task["test_data"]["task"]
    assert task["test_data"]["conditions"][0]["parameters"]["file"] == "project-archive-2024-03-31.pdf"


def test_real_hotel_and_rail_tasks_roll_when_past():
    today = date(2026, 12, 1)
    samples = {
        "hotel_search_scenario.json": ("2026-12-01", "2026-12-06"),
        "rail_book_to_cart.json": ("2026-12-01",),
        "rail_atomic_select_date.json": ("2026-12-01",),
        "hotel_atomic_select_start_date.json": ("2026-12-01",),
        "hotel_search_scenario_dubai.json": ("2027-03-05", "2027-03-09"),
    }
    tasks_dir = BENCH_TESTS_DIR / "tasks"
    for name, expected in samples.items():
        raw = json.loads((tasks_dir / name).read_text(encoding="utf-8"))
        apply_booking_dates(raw, today=today)
        got = tuple(_cond_dates(raw))
        assert got == expected, f"{name}: {got} != {expected}"
        for iso in expected:
            dotted = format_dotted(date.fromisoformat(iso))
            assert iso >= today.isoformat()
            # Prompt mentions at least the first rolled date in dotted or long form.
        first = date.fromisoformat(expected[0])
        prompt = raw["test_data"]["task"]
        assert format_dotted(first) in prompt or str(first.day) in prompt


def test_all_bench_tasks_bookable_after_apply():
    today = date.today()
    tasks_dir = Path(BENCH_TESTS_DIR) / "tasks"
    bad = []
    for path in tasks_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        apply_booking_dates(data, today=today)
        for value in _cond_dates(data):
            if value < today.isoformat():
                bad.append(f"{path.name}: {value}")
    assert not bad, bad
