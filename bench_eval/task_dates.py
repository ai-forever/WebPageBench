"""Roll booking dates in bench tasks so none are earlier than today.

Hotel and rail calendars disable past days. Task JSON keeps authored ISO dates
as templates; this module shifts a task's booking dates (and matching prompt
text) forward by one shared delta when the earliest date would otherwise be
in the past.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

DATE_EVENTS = frozenset(
    {
        "select_date",
        "bench_hotel_select_start_date",
        "bench_hotel_select_end_date",
    }
)

MONTHS_GENITIVE = (
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_OFFSET_RE = re.compile(r"^\+(\d+)d?$")
_RANGE_DASHES = ("–", "—", "-")


def iso_from_today(days: int = 0, *, today: date | None = None) -> str:
    """Return YYYY-MM-DD for today + days (never in the past when days >= 0)."""
    return ((today or date.today()) + timedelta(days=days)).isoformat()


def parse_iso_date(value: str) -> date | None:
    text = str(value).strip()
    if not _ISO_DATE_RE.match(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def resolve_date_token(value: str, *, today: date | None = None) -> date | None:
    text = str(value).strip()
    offset = _OFFSET_RE.fullmatch(text)
    if offset:
        return (today or date.today()) + timedelta(days=int(offset.group(1)))
    return parse_iso_date(text)


def format_dotted(value: date) -> str:
    return f"{value.day:02d}.{value.month:02d}.{value.year}"


def format_long(value: date, *, padded: bool = True) -> str:
    day = f"{value.day:02d}" if padded else str(value.day)
    return f"{day} {MONTHS_GENITIVE[value.month]} {value.year}"


def _day_tokens(value: date) -> tuple[str, ...]:
    padded = f"{value.day:02d}"
    raw = str(value.day)
    if padded == raw:
        return (padded,)
    return (padded, raw)


def _test_data(config: dict[str, Any]) -> dict[str, Any] | None:
    td = config.get("test_data")
    if isinstance(td, dict):
        return td
    if "conditions" in config or "task" in config:
        return config
    return None


def _date_params(td: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cond in td.get("conditions") or []:
        if not isinstance(cond, dict) or cond.get("event_name") not in DATE_EVENTS:
            continue
        params = cond.get("parameters")
        if isinstance(params, dict) and "date" in params:
            out.append(params)
    return out


def _shift_needed(parsed: list[date], today: date) -> int:
    earliest = min(parsed)
    return max(0, (today - earliest).days)


def _format_long_span(start: date, end: date, *, padded: bool) -> str:
    sa = f"{start.day:02d}" if padded else str(start.day)
    sb = f"{end.day:02d}" if padded else str(end.day)
    if start.year == end.year and start.month == end.month:
        return f"с {sa} по {sb} {MONTHS_GENITIVE[start.month]} {start.year}"
    if start.year == end.year:
        return (
            f"с {sa} {MONTHS_GENITIVE[start.month]} "
            f"по {sb} {MONTHS_GENITIVE[end.month]} {start.year}"
        )
    return f"с {format_long(start, padded=padded)} по {format_long(end, padded=padded)}"


def _format_dotted_span(start: date, end: date) -> str:
    if start.year == end.year and start.month == end.month:
        return f"{start.day:02d}–{end.day:02d}.{start.month:02d}.{start.year}"
    return f"{format_dotted(start)}–{format_dotted(end)}"


def _old_dotted_spans(start: date, end: date) -> list[str]:
    compact = f"{start.day:02d}–{end.day:02d}.{start.month:02d}.{start.year}"
    full = f"{format_dotted(start)}–{format_dotted(end)}"
    variants = [compact, full]
    for dash in _RANGE_DASHES:
        variants.append(compact.replace("–", dash))
        variants.append(full.replace("–", dash))
    return list(dict.fromkeys(variants))


def _old_long_spans(start: date, end: date) -> list[tuple[str, bool]]:
    found: list[tuple[str, bool]] = []
    if start.year != end.year or start.month != end.month:
        return found
    for da in _day_tokens(start):
        for db in _day_tokens(end):
            padded = da.startswith("0") or db.startswith("0")
            found.append(
                (
                    f"с {da} по {db} {MONTHS_GENITIVE[start.month]} {start.year}",
                    padded,
                )
            )
    return found


def _rewrite_prompt(text: str, mapping: list[tuple[date, date]]) -> str:
    if not text or not mapping:
        return text
    old_dates = [old for old, _ in mapping]
    new_by_old = {old: new for old, new in mapping}

    pairs: list[tuple[date, date, date, date]] = []
    if len(mapping) >= 2:
        old_start, new_start = mapping[0]
        old_end, new_end = mapping[-1]
        if old_end != old_start:
            pairs.append((old_start, old_end, new_start, new_end))

    for old_a, old_b, new_a, new_b in pairs:
        new_span = _format_dotted_span(new_a, new_b)
        for needle in _old_dotted_spans(old_a, old_b):
            if needle in text:
                text = text.replace(needle, new_span)
        for needle, padded in _old_long_spans(old_a, old_b):
            if needle in text:
                text = text.replace(needle, _format_long_span(new_a, new_b, padded=padded))

    # Longer textual forms first so "04 октября 2026" wins over a later dotted replace.
    for old in sorted(old_dates, reverse=True):
        new = new_by_old[old]
        for day in _day_tokens(old):
            needle = f"{day} {MONTHS_GENITIVE[old.month]} {old.year}"
            if needle in text:
                text = text.replace(
                    needle,
                    format_long(new, padded=day.startswith("0")),
                )
        dotted_old = format_dotted(old)
        if dotted_old in text:
            text = text.replace(dotted_old, format_dotted(new))
        iso_old = old.isoformat()
        if iso_old in text:
            text = text.replace(iso_old, new.isoformat())

    return text


def apply_booking_dates(config: dict[str, Any], *, today: date | None = None) -> dict[str, Any]:
    """Mutate task/config so booking dates are not before today. Returns config."""
    today = today or date.today()
    td = _test_data(config)
    if not td:
        return config

    params_list = _date_params(td)
    if not params_list:
        return config

    parsed: list[date] = []
    resolved: list[date | None] = []
    for params in params_list:
        value = resolve_date_token(str(params.get("date") or ""), today=today)
        resolved.append(value)
        if value is not None:
            parsed.append(value)

    if not parsed:
        return config

    has_offset = any(
        _OFFSET_RE.fullmatch(str(params.get("date") or "").strip()) for params in params_list
    )
    shift = 0 if has_offset else _shift_needed(parsed, today)

    mapping: list[tuple[date, date]] = []
    seen_old: set[date] = set()
    for params, value in zip(params_list, resolved):
        if value is None:
            continue
        raw = str(params.get("date") or "").strip()
        old = parse_iso_date(raw) or value
        new = value + timedelta(days=shift)
        params["date"] = new.isoformat()
        if old not in seen_old:
            mapping.append((old, new))
            seen_old.add(old)

    task_text = td.get("task")
    if isinstance(task_text, str) and mapping:
        td["task"] = _rewrite_prompt(task_text, mapping)

    return config


def booking_iso_pair(
    start_days: int = 14,
    nights: int = 5,
    *,
    today: date | None = None,
) -> tuple[str, str]:
    """Check-in / check-out ISO dates starting start_days from today."""
    start = (today or date.today()) + timedelta(days=start_days)
    end = start + timedelta(days=nights)
    return start.isoformat(), end.isoformat()
