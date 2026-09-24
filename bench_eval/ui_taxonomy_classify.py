"""Map bench task conditions to UI taxonomy classes (docs/UI_TAXONOMY.md)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bench_eval.ui_taxonomy_registry import UI_TAXONOMY_CLASS_IDS

BENCH_TASKS_DIR = Path(__file__).resolve().parents[1] / "tests" / "bench" / "tasks"

# Event name → UI taxonomy class IDs (may map to multiple classes).
EVENT_TO_CLASSES: dict[str, tuple[str, ...]] = {
    "button_clicked": ("BTN",),
    "submit_search": ("SEARCH",),
    "bench_hotel_select_city": ("SELECT_AC",),
    "select_city": ("SELECT_LIST",),
    "select_date": ("DATE",),
    "bench_hotel_select_start_date": ("DATE",),
    "bench_hotel_select_end_date": ("DATE",),
    "bench_hotel_select_guests": ("COUNTER",),
    "apply_filter": ("FILTER", "CHECK"),
    "apply_sort": ("FILTER",),
    "select_tariff": ("RADIO",),
    "select_pay_method": ("RADIO", "PAY"),
    "select_train": ("CARD",),
    "bench_hotel_select_hotel": ("CARD",),
    "bench_hotel_select_room": ("CARD",),
    "select_seat": ("SEAT",),
    "select_passenger": ("SELECT_LIST",),
    "basket_add": ("BASKET",),
    "basket_remove": ("BASKET",),
    "add_favorites": ("FAV",),
    "remove_favorites": ("FAV",),
    "dialog_opened": ("AUTH",),
    "submit_phone": ("AUTH",),
    "submit_login": ("AUTH",),
    "submit_pass": ("AUTH",),
    "submit_payment": ("PAY",),
    "bench_files_select_collection": ("CARD", "FILES"),
    "bench_files_select_year": ("SELECT_LIST", "FILES"),
    "bench_files_download": ("FILES",),
}

# Higher index → more likely to be the task goal (primary class).
PRIMARY_PRIORITY: tuple[str, ...] = (
    "PAY",
    "FILES",
    "BASKET",
    "FAV",
    "AUTH",
    "SEAT",
    "RADIO",
    "CARD",
    "COUNTER",
    "DATE",
    "SELECT_AC",
    "SELECT_LIST",
    "SEARCH",
    "FILTER",
    "CHECK",
    "BTN",
    "NAV",
    "TXT",
    "PASSIVE",
)

# Task stem patterns → subtype hints from UI_TAXONOMY.md §3.
TASK_SUBTYPE_HINTS: dict[str, tuple[str, ...]] = {
    "bench_hub_navigation": ("nav_hub_tab",),
    "bench_grocery_navigation": ("nav_menu_item", "nav_product_card"),
    "ecommerce_basket": ("nav_product_card",),
    "ecommerce_favorites": ("nav_product_card",),
    "grocery_basket": ("nav_product_card",),
    "digital_books": ("nav_product_card", "search_books"),
    "rail_atomic_select_city": ("station_from_to",),
    "rail_atomic_select_date": ("date_departure",),
    "rail_atomic_submit_search": ("search_trains",),
    "rail_book": ("search_trains",),
    "hotel_atomic_select_city": ("destination_city",),
    "hotel_atomic_select_start_date": ("date_checkin",),
    "hotel_atomic_select_end_date": ("date_checkout",),
    "hotel_atomic_select_guests": ("guests_counter",),
    "hotel_search_scenario": ("search_hotels",),
    "files": ("files_cabinet",),
}


def classes_for_event(event_name: str, parameters: dict[str, Any] | None = None) -> tuple[str, ...]:
    if event_name == "state_changed":
        new_state = (parameters or {}).get("new_state", "")
        if isinstance(new_state, str) and (
            new_state.endswith("_item")
            or new_state in ("bench_hotel_hotel", "bench_hotel_room", "bench_hotel_checkout")
        ):
            return ("CARD", "NAV")
        return ("NAV",)
    return EVENT_TO_CLASSES.get(event_name, ())


def classes_for_events(conditions: list[dict[str, Any]]) -> list[str]:
    found: list[str] = []
    for cond in conditions:
        name = cond.get("event_name", "")
        if not name:
            continue
        params = cond.get("parameters")
        for class_id in classes_for_event(name, params if isinstance(params, dict) else None):
            if class_id not in found:
                found.append(class_id)
    return found


def infer_primary(classes: list[str]) -> str:
    if not classes:
        return "NAV"
    priority = {class_id: idx for idx, class_id in enumerate(PRIMARY_PRIORITY)}
    return min(classes, key=lambda c: priority.get(c, 999))


def infer_subtypes(task_stem: str, classes: list[str]) -> list[str]:
    subtypes: list[str] = []
    for prefix, hints in TASK_SUBTYPE_HINTS.items():
        if task_stem.startswith(prefix):
            for hint in hints:
                if hint not in subtypes:
                    subtypes.append(hint)
    if "FILES" in classes and "files_cabinet" not in subtypes:
        subtypes.append("files_cabinet")
    if "SEARCH" in classes and task_stem.startswith("digital_books"):
        if "search_books" not in subtypes:
            subtypes.append("search_books")
    return subtypes


def classify_task(task_data: dict[str, Any], *, task_stem: str = "") -> dict[str, Any]:
    """Build ui_taxonomy block from task test_data conditions."""
    conditions = task_data.get("conditions") or []
    classes = classes_for_events(conditions)
    primary = infer_primary(classes)
    block: dict[str, Any] = {"primary": primary, "classes": classes}
    subtypes = infer_subtypes(task_stem, classes)
    if subtypes:
        block["subtypes"] = subtypes
    return block


def load_task_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_task_taxonomy(task: dict[str, Any], *, task_stem: str = "") -> list[str]:
    """Return validation errors for ui_taxonomy vs conditions."""
    errors: list[str] = []
    td = task.get("test_data", task)
    ui = td.get("ui_taxonomy") or task.get("ui_taxonomy")
    if not ui:
        errors.append(f"{task_stem}: missing ui_taxonomy")
        return errors

    primary = ui.get("primary")
    classes = ui.get("classes") or []
    if primary not in UI_TAXONOMY_CLASS_IDS:
        errors.append(f"{task_stem}: invalid primary {primary!r}")
    for class_id in classes:
        if class_id not in UI_TAXONOMY_CLASS_IDS:
            errors.append(f"{task_stem}: invalid class {class_id!r}")
    if primary and primary not in classes:
        errors.append(f"{task_stem}: primary {primary!r} not in classes {classes}")

    conditions = td.get("conditions") or []
    expected = set(classes_for_events(conditions))
    actual = set(classes)
    missing = expected - actual
    extra = actual - expected
    if missing:
        errors.append(f"{task_stem}: classes missing inferred {sorted(missing)} from events")
    if extra:
        errors.append(f"{task_stem}: classes {sorted(extra)} not inferred from events")

    return errors


def annotate_task(task: dict[str, Any], *, task_stem: str = "") -> dict[str, Any]:
    """Return task dict with ui_taxonomy in test_data."""
    out = json.loads(json.dumps(task, ensure_ascii=False))
    td = out.setdefault("test_data", {})
    td["ui_taxonomy"] = classify_task(td, task_stem=task_stem)
    return out
