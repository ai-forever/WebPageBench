#!/usr/bin/env python3
"""Build aggregated README.md from latest eval runs for all models and harnesses."""

from __future__ import annotations

import argparse
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO_ROOT)

from bench_eval.aggregate_report import (  # noqa: E402
    FULL_BENCH_MIN_TASKS,
    discover_all_run_paths,
    discover_latest_runs,
    write_aggregate_report,
    write_results_archive,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate latest eval results.json for every harness × model "
            "into a single Markdown README with averaged statistics and LLM cost"
        ),
    )
    parser.add_argument(
        "--base-dir",
        default=os.getenv("EVAL_RESULTS_BASE_DIR", "tests/eval"),
        help="Base directory with eval runs (default: tests/eval)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output README path (default: <base-dir>/README.md)",
    )
    parser.add_argument(
        "--require-finished",
        action="store_true",
        help="Skip combinations whose latest run has finished=false",
    )
    parser.add_argument(
        "--skip-enrich",
        action="store_true",
        help="Do not write extended metrics back into results.json",
    )
    parser.add_argument(
        "--skip-run-reports",
        action="store_true",
        help="Do not write per-run README.md next to each results.json",
    )
    parser.add_argument(
        "--pass-at-k",
        type=int,
        default=3,
        metavar="K",
        help="k for Pass@k across historical runs of the same harness × model (default: 3)",
    )
    parser.add_argument(
        "--min-tasks-for-aggregate",
        type=int,
        default=FULL_BENCH_MIN_TASKS,
        metavar="N",
        help=(
            "Include only runs with at least N tasks in the aggregate README "
            f"(default: {FULL_BENCH_MIN_TASKS}, i.e. full bench; smoke runs excluded). "
            "Use 0 to include all runs."
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print discovered harness × model paths and exit without writing README",
    )
    parser.add_argument(
        "--zip-output",
        default=os.path.join(_REPO_ROOT, "results.zip"),
        help="Path for results.zip archive (default: <repo-root>/results.zip)",
    )
    parser.add_argument(
        "--skip-zip",
        action="store_true",
        help="Do not build results.zip with full-bench artifacts",
    )
    args = parser.parse_args()
    min_total_tasks = args.min_tasks_for_aggregate or None

    if args.list:
        entries = discover_latest_runs(
            args.base_dir,
            require_finished=args.require_finished,
            min_total_tasks=min_total_tasks,
        )
        if not entries:
            print(f"No results under {args.base_dir}")
            raise SystemExit(1)
        for entry in sorted(entries, key=lambda item: (item.harness, item.model_dir)):
            status = "finished" if entry.finished else "unfinished"
            print(
                f"{entry.harness}\t{entry.model}\t{status}\t{entry.results_path}"
            )
        return

    output = write_aggregate_report(
        args.base_dir,
        output_path=args.output,
        require_finished=args.require_finished,
        enrich_results=not args.skip_enrich,
        pass_at_k=max(args.pass_at_k, 1),
        write_run_reports=not args.skip_run_reports,
        min_total_tasks=min_total_tasks,
    )
    entries = discover_latest_runs(
        args.base_dir,
        require_finished=args.require_finished,
        min_total_tasks=min_total_tasks,
    )
    all_entries = discover_latest_runs(
        args.base_dir,
        require_finished=args.require_finished,
    )
    enriched_count = 0
    run_report_count = 0
    if not args.skip_enrich or not args.skip_run_reports:
        all_runs = discover_all_run_paths(
            args.base_dir,
            require_finished=args.require_finished,
        )
        if not args.skip_enrich:
            enriched_count = len(all_runs)
        if not args.skip_run_reports:
            run_report_count = len(
                {
                    path.resolve()
                    for paths in all_runs.values()
                    for path in paths
                }
            )
    print(
        f"Wrote {output} ({len(entries)} full-bench harness × model combinations"
        + (
            f"; {len(all_entries)} total including smoke"
            if min_total_tasks is not None and len(all_entries) != len(entries)
            else ""
        )
        + f"; enriched {enriched_count} results.json; "
        f"per-run README: {run_report_count})"
    )
    if not args.skip_zip:
        zip_path = write_results_archive(
            entries,
            aggregate_readme=output,
            output_zip=args.zip_output,
        )
        print(f"Wrote {zip_path} ({len(entries)} model/harness entries)")


if __name__ == "__main__":
    main()
