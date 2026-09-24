#!/usr/bin/env python3
"""Compute LLM API cost from eval results.json."""

from __future__ import annotations

import argparse
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO_ROOT)

from bench_eval.llm_cost import (  # noqa: E402
    compute_results_cost,
    format_usd,
    load_pricing_table,
)
from bench_eval.run_report import load_results, resolve_results_path  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Estimate LLM API cost from eval results.json",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to results.json or run directory",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON summary",
    )
    parser.add_argument(
        "--refresh-pricing",
        action="store_true",
        help="Refresh cached LiteLLM pricing table",
    )
    args = parser.parse_args()

    if not args.path:
        parser.error("PATH is required")

    results_path = resolve_results_path(args.path)
    payload = load_results(results_path)
    pricing_table = load_pricing_table(refresh=args.refresh_pricing)
    breakdown = compute_results_cost(payload, pricing_table=pricing_table)
    run = payload.get("run") or {}

    if args.json:
        print(
            json.dumps(
                {
                    "results_path": str(results_path),
                    "model": breakdown.model,
                    "provider": run.get("provider"),
                    "agent_harness": run.get("agent_harness"),
                    "total_tasks": run.get("total_tasks"),
                    "prompt_tokens": breakdown.prompt_tokens,
                    "completion_tokens": breakdown.completion_tokens,
                    "total_cost_usd": breakdown.total_cost_usd,
                    "avg_cost_per_task_usd": breakdown.avg_cost_per_task_usd,
                    "auxiliary_cost_usd": breakdown.auxiliary_cost_usd,
                    "tasks_with_cost": breakdown.tasks_with_cost,
                    "priced": breakdown.priced,
                    "pricing_key": breakdown.pricing_key,
                    "source": breakdown.source,
                    "by_model": [
                        {
                            "model": row.model,
                            "prompt_tokens": row.prompt_tokens,
                            "completion_tokens": row.completion_tokens,
                            "total_cost_usd": row.total_cost_usd,
                            "priced": row.priced,
                            "pricing_key": row.pricing_key,
                            "source": row.source,
                            "roles": list(row.roles),
                            "llm_calls": row.llm_calls,
                        }
                        for row in breakdown.by_model
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    print(f"Results: {results_path}")
    print(f"Model: {breakdown.model}")
    if run.get("provider"):
        print(f"Provider: {run['provider']}")
    if run.get("agent_harness"):
        print(f"Harness: {run['agent_harness']}")
    print(f"Prompt tokens: {breakdown.prompt_tokens}")
    print(f"Completion tokens: {breakdown.completion_tokens}")
    print(f"Total cost: {format_usd(breakdown.total_cost_usd)}")
    print(f"Avg cost per task: {format_usd(breakdown.avg_cost_per_task_usd)}")
    if breakdown.auxiliary_cost_usd is not None:
        print(f"Auxiliary/fallback cost: {format_usd(breakdown.auxiliary_cost_usd)}")
    if breakdown.by_model:
        print("Cost by model:")
        for row in breakdown.by_model:
            roles = f" [{', '.join(row.roles)}]" if row.roles else ""
            print(
                f"  {row.model}{roles}: "
                f"prompt={row.prompt_tokens}, completion={row.completion_tokens}, "
                f"calls={row.llm_calls}, cost={format_usd(row.total_cost_usd)}"
            )
    if breakdown.pricing_key:
        print(f"Pricing key: {breakdown.pricing_key}")
    if not breakdown.priced:
        print("Pricing: unavailable for this model (no recorded cost, no LiteLLM match)")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
