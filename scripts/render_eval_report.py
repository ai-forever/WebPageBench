#!/usr/bin/env python3
"""Build README.md report from eval results.json."""

from __future__ import annotations

import argparse
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO_ROOT)

from bench_eval.run_report import find_latest_results, resolve_results_path, write_run_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render Markdown README report from eval results.json",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to results.json or run directory (tests/eval/<model>/<harness>/<date>/)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Use the latest run under tests/eval/ (optionally scoped by --model / --harness)",
    )
    parser.add_argument(
        "--model",
        help="Model subdirectory under tests/eval/ for --latest",
    )
    parser.add_argument(
        "--harness",
        help="Harness subdirectory under tests/eval/<model>/ for --latest",
    )
    parser.add_argument(
        "--base-dir",
        default=os.getenv("EVAL_RESULTS_BASE_DIR", "tests/eval"),
        help="Base directory with eval runs (default: tests/eval)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output README path (default: README.md next to results.json)",
    )
    args = parser.parse_args()

    if args.latest:
        results_path = find_latest_results(
            args.base_dir,
            model=args.model,
            harness=args.harness,
        )
    elif args.path:
        results_path = resolve_results_path(args.path)
    else:
        parser.error("Provide PATH or use --latest")

    output = write_run_report(results_path, output_path=args.output)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
