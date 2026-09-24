"""Golden-path Playwright tests: every tests/bench/tasks/*.json must pass client.check()."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BENCH_DIR = Path(__file__).resolve().parent
if str(_BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(_BENCH_DIR))


from bench_eval.bench_verify import BENCH_TESTS_DIR
from bench_eval.ui_helpers import create_track
from golden_path_runners import run_task

pytestmark = pytest.mark.ui

TASK_STEMS = sorted(p.stem for p in (BENCH_TESTS_DIR / "tasks").glob("*.json"))


@pytest.mark.parametrize("stem", TASK_STEMS)
def test_task_golden_path(page, require_services, stem: str):
    track_id = create_track(f"gp_{stem}"[:80], task_stem=stem)
    run_task(page, track_id, stem)
