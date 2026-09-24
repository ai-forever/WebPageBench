"""Human-readable labels for UI taxonomy classes and widget patterns."""

from __future__ import annotations

from bench_eval.ui_taxonomy_registry import UI_TAXONOMY_CLASSES
from bench_eval.ui_variants import WIDGET_TAXONOMY_CLASS

WIDGET_LABELS: dict[str, str] = {
    "date": "Выбор даты",
    "select_city": "Город (autocomplete)",
    "select_station": "Станция / список",
    "counter_guests": "Счётчик гостей",
    "text_search": "Поисковая строка",
}

VARIANT_LABELS: dict[str, str] = {
    "split_popup": "два поля + popup-календарь",
    "inline_calendar": "календарь всегда на странице",
    "text_input": "ввод дат текстом ДД.ММ.ГГГГ",
    "single_popup": "одно поле диапазона + popup",
    "popup_grid": "поля туда/обратно + сетка-календаря",
    "native_input": "HTML input type=date",
    "autocomplete": "input + dropdown подсказок",
    "native_select": "HTML select",
    "typeahead": "input + dropdown (typeahead)",
    "rooms_popup": "popup с комнатами и stepper",
    "inline_stepper": "кнопки +/− в строке",
    "compact_select": "select с числом гостей",
    "pill_buttons": "горизонтальные pill-кнопки",
    "standard": "стандартный вид поля",
    "outlined": "outlined-поле",
    "filled": "поле с заливкой",
    "underlined": "поле с нижней границей",
    "pill": "скруглённая «капсула»",
    "large": "увеличенное поле",
}

_CLASS_NAMES: dict[str, str] = {item.class_id: item.name for item in UI_TAXONOMY_CLASSES}


def taxonomy_class_label(class_id: str) -> str:
    return _CLASS_NAMES.get(class_id, class_id)


def taxonomy_class_description(class_id: str) -> str:
    for item in UI_TAXONOMY_CLASSES:
        if item.class_id == class_id:
            events = ", ".join(item.primary_events[:3])
            if len(item.primary_events) > 3:
                events += ", …"
            domains = ", ".join(item.bench_domains[:4])
            if len(item.bench_domains) > 4:
                domains += ", …"
            return f"{item.name}; события: {events or '—'}; домены: {domains}"
    return "Неизвестный класс UI-таксономии"


def ui_pattern_description(pattern_key: str) -> str:
    if ":" not in pattern_key:
        return pattern_key
    widget, variant = pattern_key.split(":", 1)
    class_id = WIDGET_TAXONOMY_CLASS.get(widget, "")
    class_name = taxonomy_class_label(class_id) if class_id else "Виджет"
    widget_name = WIDGET_LABELS.get(widget, widget)
    variant_name = VARIANT_LABELS.get(variant, variant)
    if class_id:
        return f"{class_id} ({class_name}) — {widget_name}: {variant_name}"
    return f"{widget_name}: {variant_name}"
