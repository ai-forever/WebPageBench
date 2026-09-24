"""WebPageBench API helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from lib.src.agent_bench import client


def create_track(
    *,
    test_name: str,
    track_id: str,
    config_path: str,
    api_address: str,
    https: bool = False,
) -> Optional[str]:
    return client.create_track(
        name=test_name,
        id=track_id,
        filepath=config_path,
        address=api_address,
        https=https,
        delete_existing=True,
    )


def check_track(
    track_id: str,
    api_address: str,
    *,
    https: bool = False,
) -> List[Dict[str, Any]]:
    results = client.check(track_id, api_address, https=https)
    return results or []


def summarize_checks(check_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate per-condition and grouped OR results."""
    if not check_results:
        return {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "score": 0.0,
            "all_passed": False,
            "failed_conditions": [],
            "check_results": [],
        }

    groups_seen: Dict[str, bool] = {}
    ungrouped_passed = 0
    ungrouped_failed = 0
    failed_conditions: List[str] = []

    for row in check_results:
        group = row.get("group")
        description = row.get("description") or row.get("event_name", "condition")

        if group:
            if group not in groups_seen:
                group_ok = row.get("group_success", False)
                groups_seen[group] = group_ok
                if not group_ok:
                    failed_conditions.append(f"group:{group}")
        else:
            if row.get("success"):
                ungrouped_passed += 1
            else:
                ungrouped_failed += 1
                failed_conditions.append(description)

    group_passed = sum(1 for ok in groups_seen.values() if ok)
    group_failed = sum(1 for ok in groups_seen.values() if not ok)
    passed = ungrouped_passed + group_passed
    failed = ungrouped_failed + group_failed
    total = passed + failed
    score = passed / total if total else 0.0

    return {
        "passed": passed,
        "failed": failed,
        "total": total,
        "score": score,
        "all_passed": failed == 0 and total > 0,
        "failed_conditions": failed_conditions,
        "check_results": check_results,
    }
