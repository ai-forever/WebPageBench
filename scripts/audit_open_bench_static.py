"""Static contract audit for tests/bench tasks vs frontend events and taxonomy docs."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tests" / "bench" / "tasks"
FRONTEND = ROOT / "site" / "frontend" / "src"
OUT = ROOT / "tests" / "bench" / "build"
OUT.mkdir(parents=True, exist_ok=True)

PASSIVE = {"click", "keypress", "scroll", "input", "visibility", "mousemove"}


def _task_events() -> Counter:
    counts: Counter = Counter()
    for path in sorted(TASKS.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for cond in data.get("test_data", {}).get("conditions") or []:
            name = cond.get("event_name")
            if name:
                counts[name] += 1
    return counts


def _frontend_event_types() -> set[str]:
    found: set[str] = set()
    patterns = [
        re.compile(r"type:\s*['\"]([a-zA-Z0-9_]+)['\"]"),
        re.compile(r"HOTEL_EVENTS\.\w+|selectCity|selectHotel|selectStartDate|selectEndDate|selectGuests|selectRoom"),
    ]
    for path in FRONTEND.rglob("*"):
        if path.suffix not in {".vue", ".js", ".ts"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r"type:\s*['\"]([a-zA-Z0-9_]+)['\"]", text):
            found.add(match.group(1))
    found.update(
        {
            "bench_hotel_select_city",
            "bench_hotel_select_hotel",
            "bench_hotel_select_start_date",
            "bench_hotel_select_end_date",
            "bench_hotel_select_guests",
            "bench_hotel_select_room",
        }
    )
    return found


def main() -> int:
    from bench_eval.ui_taxonomy_classify import EVENT_TO_CLASSES, classes_for_event

    task_files = sorted(TASKS.glob("*.json"))
    events = _task_events()
    frontend = _frontend_event_types()
    mapped = set(EVENT_TO_CLASSES) | {"state_changed"}
    unmapped_conditions = sorted(name for name in events if not classes_for_event(name, {}))
    missing_frontend = sorted(name for name in events if name not in frontend and name != "state_changed")
    extra_frontend = sorted(
        name for name in frontend if name not in mapped and name not in PASSIVE and not name.startswith("econom")
    )

    taxonomy = (ROOT / "docs" / "TAXONOMY.md").read_text(encoding="utf-8")
    stale_hub = "### Главная (3)" in taxonomy

    lines = [
        "# Static contract snapshot",
        "",
        f"Task files: {len(task_files)}",
        f"Unique condition events: {len(events)}",
        "",
        "## Event frequencies (conditions)",
        "",
    ]
    for name, count in events.most_common():
        lines.append(f"- `{name}`: {count}")
    lines += [
        "",
        f"Unmapped condition events: {unmapped_conditions or 'none'}",
        f"Condition events not found in frontend grep: {missing_frontend or 'none'}",
        f"TAXONOMY.md still has stale hub heading 'Главная (3)': {stale_hub}",
        "",
        "## Frontend event types not in EVENT_TO_CLASSES (sample)",
        "",
    ]
    for name in extra_frontend[:40]:
        lines.append(f"- `{name}`")
    report = OUT / "static_contract.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
