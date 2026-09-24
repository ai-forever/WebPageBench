#!/usr/bin/env python3
"""Build eval dataset JSON from mock task configs."""

from __future__ import annotations

import argparse
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO_ROOT)

from bench_eval.dataset import build_dataset  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build DeepEval dataset from WebPageBench mocks")
    parser.add_argument(
        "--mock",
        default=os.getenv("EVAL_MOCK", "bench"),
        help="Mock/bench folder name under tests/ (default: bench)",
    )
    parser.add_argument(
        "--output",
        default=os.getenv("EVAL_DATASET_PATH", "tests/evals/dataset.json"),
        help="Output dataset path",
    )
    parser.add_argument(
        "--frontend-host",
        default=os.getenv("EVAL_FRONTEND_HOST", "127.0.0.1:5173"),
    )
    parser.add_argument("--task-filter", default=os.getenv("EVAL_TASK_FILTER"))
    parser.add_argument("--max-tasks", type=int, default=None)
    args = parser.parse_args()

    tests_dir = os.path.join("tests", args.mock)
    dataset = build_dataset(
        tests_dir,
        args.output,
        frontend_host=args.frontend_host,
        task_filter=args.task_filter,
        max_tasks=args.max_tasks,
    )
    print(f"Wrote {len(dataset.goldens)} goldens to {args.output}")


if __name__ == "__main__":
    main()
