#!/usr/bin/env python3
"""Annotate tests/bench/tasks/*.json with ui_taxonomy from conditions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bench_eval.ui_taxonomy_classify import annotate_task, validate_task_taxonomy  # noqa: E402

TASKS_DIR = ROOT / "tests" / "bench" / "tasks"


def main() -> int:
    errors: list[str] = []
    for path in sorted(TASKS_DIR.glob("*.json")):
        task = json.loads(path.read_text(encoding="utf-8"))
        annotated = annotate_task(task, task_stem=path.stem)
        path.write_text(
            json.dumps(annotated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        errors.extend(validate_task_taxonomy(annotated, task_stem=path.stem))

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"Annotated {len(list(TASKS_DIR.glob('*.json')))} tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
