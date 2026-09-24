"""Static contract: bench tasks, taxonomy mapping, docs drift."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from bench_eval.ui_taxonomy_classify import classes_for_event

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "tests" / "bench" / "tasks"
TAXONOMY = ROOT / "docs" / "TAXONOMY.md"
BOOKS_KV = ROOT / "site" / "backend" / "static" / "kv" / "books" / "books_kv.json"
CONFIG = ROOT / "tests" / "bench" / "config.json"

_SCRIPTS = ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from ui_pattern_task_map import canonical_task_count


def test_task_count_matches_canonical():
    assert len(list(TASKS.glob("*.json"))) == canonical_task_count()


def test_every_condition_event_maps_to_taxonomy():
    missing = []
    for path in TASKS.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for cond in data.get("test_data", {}).get("conditions") or []:
            name = cond.get("event_name")
            if not name:
                continue
            params = cond.get("parameters") if isinstance(cond.get("parameters"), dict) else None
            if not classes_for_event(name, params):
                missing.append(f"{path.stem}:{name}")
    assert not missing, missing


def test_taxonomy_doc_matches_canonical_count():
    text = TAXONOMY.read_text(encoding="utf-8")
    assert "### Главная (3)" not in text
    assert f"**{canonical_task_count()}**" in text or f"| **{canonical_task_count()}** |" in text
    assert "**65**" in text
    assert "YYYY-MM" in text


def test_hotel_and_rail_condition_dates_are_bookable():
    """Calendars disable past days; apply_booking_dates keeps task dates >= today."""
    from datetime import date as date_cls

    from bench_eval.task_dates import DATE_EVENTS, apply_booking_dates

    today = date_cls.today().isoformat()
    bad = []
    for path in TASKS.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        apply_booking_dates(data)
        for cond in data.get("test_data", {}).get("conditions") or []:
            if cond.get("event_name") not in DATE_EVENTS:
                continue
            value = str((cond.get("parameters") or {}).get("date") or "")
            if value and value < today:
                bad.append(f"{path.name}: {value}")
    assert not bad, bad


def test_rail_select_date_uses_iso():
    bad = []
    for path in TASKS.glob("rail_*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for cond in data.get("test_data", {}).get("conditions") or []:
            if cond.get("event_name") != "select_date":
                continue
            date = (cond.get("parameters") or {}).get("date", "")
            if date and "." in str(date):
                bad.append(f"{path.name}: {date}")
    assert not bad, bad


def test_books_tasks_match_catalog():
    kv = json.loads(BOOKS_KV.read_text(encoding="utf-8"))
    items = {key: value for key, value in kv.items() if isinstance(value, dict)}
    names = {value.get("name") for value in items.values() if value.get("name")}

    missing_ids: list[str] = []
    missing_titles: list[str] = []
    task_item_ids: set[str] = set()
    for path in TASKS.glob("digital_books_*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        td = data.get("test_data") or {}
        for cond in td.get("conditions") or []:
            params = cond.get("parameters") if isinstance(cond.get("parameters"), dict) else {}
            for key in ("item_id", "state_id"):
                val = params.get(key)
                if isinstance(val, str) and val.startswith("item_") and val not in items:
                    missing_ids.append(f"{path.name}:{val}")
                elif isinstance(val, str) and val.startswith("item_"):
                    task_item_ids.add(val)
        for title in re.findall(r"«([^»]+)»", td.get("task") or ""):
            if title == "Книги":
                continue
            if title not in names:
                missing_titles.append(f"{path.name}:{title}")
    assert not missing_ids, missing_ids
    assert not missing_titles, missing_titles

    books = json.loads(CONFIG.read_text(encoding="utf-8"))["domain_configs"]["books"]["common_elements"]
    for carousel in ("item_carousel", "item_carousel2", "item_carousel3"):
        for row in books[carousel]["items"]:
            assert row["kv_id"] in items, f"{carousel}: missing {row['kv_id']}"

    haystack = [
        f"{item.get('name') or ''} {item.get('author') or ''}".lower()
        for item in items.values()
    ]
    for suggestion in books["search_bar"]["suggestionsList"]:
        needle = suggestion.lower()
        assert any(needle in text for text in haystack), f"search suggestion {suggestion!r} matches no book"

    missing_format: list[str] = []
    for tid in sorted(task_item_ids):
        item = items.get(tid)
        if not isinstance(item, dict):
            missing_format.append(f"{tid}: missing")
            continue
        formats = {
            bool(other.get("is_audiobook"))
            for other in items.values()
            if other.get("name") == item.get("name") and other.get("author") == item.get("author")
        }
        if formats != {False, True}:
            missing_format.append(f"{tid}:{item.get('name')}:{sorted(formats)}")
    assert not missing_format, missing_format


def test_basket_amount_conditions_are_exact_ints():
    """Quantity checks must name a concrete final count, not a range operator."""
    bad = []
    for path in TASKS.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for cond in data.get("test_data", {}).get("conditions") or []:
            if cond.get("event_name") not in {"basket_add", "basket_remove"}:
                continue
            params = cond.get("parameters") if isinstance(cond.get("parameters"), dict) else {}
            if "amount" not in params:
                continue
            amount = params["amount"]
            if isinstance(amount, bool) or not isinstance(amount, int) or amount < 1:
                bad.append(f"{path.name}: amount={amount!r}")
    assert not bad, bad
