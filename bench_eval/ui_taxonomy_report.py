"""Build per-test UI taxonomy and UI pattern reports for eval runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bench_eval.ui_taxonomy_classify import (
    classes_for_event,
    classes_for_events,
    classify_task,
)
from bench_eval.ui_variants import pattern_keys, resolve_ui_variants


def _load_config(config_path: str | None) -> dict[str, Any]:
    if not config_path:
        return {}
    path = Path(config_path)
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _event_parameters(event: dict[str, Any]) -> dict[str, Any] | None:
    raw = event.get("event_data")
    if isinstance(raw, dict):
        params = raw.get("parameters")
        return params if isinstance(params, dict) else raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            params = parsed.get("parameters")
            return params if isinstance(params, dict) else parsed
    return None


def classes_from_dab_events(events: list[dict[str, Any]]) -> list[str]:
    found: list[str] = []
    for event in events:
        event_name = event.get("event_name")
        if not event_name:
            continue
        params = _event_parameters(event)
        for class_id in classes_for_event(event_name, params):
            if class_id not in found:
                found.append(class_id)
    return found


def checked_conditions(test_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for condition in test_data.get("conditions") or []:
        event_name = condition.get("event_name")
        if not event_name:
            continue
        params = condition.get("parameters")
        params_dict = params if isinstance(params, dict) else None
        rows.append(
            {
                "event_name": event_name,
                "parameters": params_dict or {},
                "classes": list(classes_for_event(event_name, params_dict)),
            }
        )
    return rows


def build_ui_taxonomy_report(
    *,
    config_path: str | None,
    test_name: str,
    dab_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    config = _load_config(config_path)
    test_data = config.get("test_data") or {}
    declared = test_data.get("ui_taxonomy")
    if not declared and test_data.get("conditions"):
        declared = classify_task(test_data, task_stem=test_name)

    checked = checked_conditions(test_data)
    checked_classes = list(declared.get("classes") if declared else classes_for_events(test_data.get("conditions") or []))
    used_classes = classes_from_dab_events(dab_events or [])
    domain = test_data.get("bench_first_domain")
    variants = resolve_ui_variants(config, domain=domain)

    return {
        "domain": domain,
        "declared": declared or {},
        "checked_conditions": checked,
        "checked_classes": checked_classes,
        "used_classes": used_classes,
        "used_but_not_checked": sorted(set(used_classes) - set(checked_classes)),
        "checked_but_not_used": sorted(set(checked_classes) - set(used_classes)),
        "ui_patterns": {
            "domain": domain,
            "profile_id": test_data.get("ui_variant_profile"),
            "variants": variants,
            "pattern_keys": pattern_keys(variants),
        },
    }


def _increment_bucket(
    buckets: dict[str, dict[str, Any]],
    key: str,
    *,
    success: bool,
    test_name: str,
) -> None:
    row = buckets.setdefault(
        key,
        {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "success_rate": 0.0,
            "tests": [],
        },
    )
    row["total"] += 1
    if success:
        row["passed"] += 1
    else:
        row["failed"] += 1
    row["success_rate"] = row["passed"] / row["total"] if row["total"] else 0.0
    if test_name not in row["tests"]:
        row["tests"].append(test_name)


def aggregate_ui_stats(tests: list[dict[str, Any]]) -> dict[str, Any]:
    by_checked_class: dict[str, dict[str, Any]] = {}
    by_used_class: dict[str, dict[str, Any]] = {}
    by_primary: dict[str, dict[str, Any]] = {}
    by_ui_pattern: dict[str, dict[str, Any]] = {}

    for row in tests:
        ui = row.get("ui_taxonomy") or {}
        success = bool(row.get("success"))
        test_name = row.get("test_name") or "unknown"

        primary = (ui.get("declared") or {}).get("primary")
        if primary:
            _increment_bucket(by_primary, primary, success=success, test_name=test_name)

        for class_id in ui.get("checked_classes") or []:
            _increment_bucket(by_checked_class, class_id, success=success, test_name=test_name)

        for class_id in ui.get("used_classes") or []:
            _increment_bucket(by_used_class, class_id, success=success, test_name=test_name)

        patterns = (ui.get("ui_patterns") or {}).get("pattern_keys") or []
        for pattern in patterns:
            _increment_bucket(by_ui_pattern, pattern, success=success, test_name=test_name)

    return {
        "by_checked_class": by_checked_class,
        "by_used_class": by_used_class,
        "by_primary": by_primary,
        "by_ui_pattern": by_ui_pattern,
    }
