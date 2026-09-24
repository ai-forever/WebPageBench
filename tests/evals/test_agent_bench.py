"""
End-to-end evaluation of LLM browser agents on WebPageBench mocks.

Run with:
    deepeval test run tests/evals/test_agent_bench.py

Goldens are injected via pytest_generate_tests in tests/evals/conftest.py.
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from deepeval import assert_test
from deepeval.dataset import Golden
from deepeval.test_case import LLMTestCase

from bench_eval.config import EvalConfig
from bench_eval.metrics import AGENT_BENCH_METRICS
from bench_eval.results import get_recorder
from bench_eval.runner import run_golden


def test_agent_bench_task(golden: Golden, eval_config: EvalConfig):
    recorder = get_recorder(eval_config)
    test_name = golden.name or "golden"
    recorder.on_test_start(test_name)
    test_case: LLMTestCase = run_golden(golden, config=eval_config)
    recorder.record_test(test_case)
    assert_test(
        test_case=test_case,
        metrics=AGENT_BENCH_METRICS,
        run_async=False,
    )
