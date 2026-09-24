#!/usr/bin/env python3
"""Print harness dependency compatibility for the eval stack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from bench_eval.harness_compat import inspect_all_harnesses, inspect_harness
from bench_eval.harness_submodules import all_submodule_statuses


def _status_to_dict(status) -> dict:
    return {
        "harness": status.harness,
        "ready": status.ready,
        "requires_optional": status.requires_optional,
        "browser_use": {
            "available": status.browser_use.available,
            "mode": status.browser_use.mode,
            "version": status.browser_use.version,
            "path": status.browser_use.path,
            "from_submodule": status.browser_use.from_submodule,
        },
        "submodule": status.submodule,
        "missing_packages": list(status.missing_packages),
        "warnings": list(status.warnings),
        "notes": list(status.notes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--harness",
        help="Check a single harness (default: all registered harnesses)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--submodules-only",
        action="store_true",
        help="Only print pinned harness submodule status",
    )
    parser.add_argument(
        "--skip-harness",
        action="append",
        default=[],
        metavar="NAME",
        help="Do not fail when these harnesses are not ready (repeatable)",
    )
    args = parser.parse_args()

    if args.submodules_only:
        payload = {"submodules": all_submodule_statuses()}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            for item in payload["submodules"]:
                flag = "OK" if item["commit_ok"] else "DRIFT"
                if not item["initialized"]:
                    flag = "MISSING"
                print(
                    f"[{flag}] {item['harness']}: {item['path']} "
                    f"({item['release_label']})"
                )
                if item["current_commit"]:
                    print(f"      commit: {item['current_commit'][:12]}")
                if item["pinned_commit"]:
                    print(f"      pinned: {item['pinned_commit'][:12]}")
        failed = [
            item["harness"]
            for item in payload["submodules"]
            if not item["initialized"] or not item["commit_ok"]
        ]
        return 1 if failed else 0

    if args.harness:
        statuses = {args.harness: inspect_harness(args.harness)}
    else:
        statuses = inspect_all_harnesses()

    if args.json:
        print(json.dumps({k: _status_to_dict(v) for k, v in statuses.items()}, indent=2))
    else:
        for name, status in statuses.items():
            flag = "OK" if status.ready else "MISSING"
            print(f"[{flag}] {name}")
            if status.browser_use.available:
                print(
                    f"      browser-use: {status.browser_use.mode}"
                    f" ({status.browser_use.version or 'unknown'})"
                )
            else:
                print("      browser-use: missing")
            if status.submodule:
                sub = status.submodule
                print(
                    f"      submodule: {sub['path']} "
                    f"commit={sub.get('current_commit', '?')[:12]} "
                    f"pin={sub.get('pinned_commit', '-')[:12] if sub.get('pinned_commit') else '-'}"
                )
            for item in status.missing_packages:
                print(f"      missing: {item}")
            for item in status.warnings:
                print(f"      warn: {item}")
            for item in status.notes:
                print(f"      note: {item}")

    failed = [
        name
        for name, status in statuses.items()
        if not status.ready and name not in set(args.skip_harness)
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
