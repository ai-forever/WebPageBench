"""Standalone batch benchmark for GUI models (no DeepEval required).

Same contract as the DeepEval path — create a WebPageBench track, run the agent, verify
via backend telemetry — but as a plain script that writes one JSON report. Use it
for quick sweeps; use ``./scripts/run_eval.sh`` for the canonical, reportable run.

    ./scripts/start_dab.sh                    # backend + frontend must be up
    python -m bench_eval.agents.cli.benchmark qwen3-vl-8b --max-tasks 5
    python -m bench_eval.agents.cli.benchmark uitars-1.5-7b \\
        --task-filter ecommerce_basket --max-steps 20 --output runs/uitars.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from bench_eval.agents.core.executor import BrowserComputer
from bench_eval.agents.core.loop import run_agent_loop
from bench_eval.agents.core.settings import build_agent, build_settings
from bench_eval.config import load_config
from bench_eval.dataset import build_test_configs
from bench_eval.task_url import resolve_entry_url
from bench_eval.track import check_track, create_track, summarize_checks


@dataclass
class TaskOutcome:
    test_name: str
    track_id: str
    task: str
    entry_url: Optional[str]
    steps: int = 0
    status: str = "not_run"
    is_done: bool = False
    passed: int = 0
    failed: int = 0
    total: int = 0
    score: float = 0.0
    all_passed: bool = False
    failed_conditions: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    token_usage: dict[str, Any] = field(default_factory=dict)
    final_result: Optional[str] = None
    error: Optional[str] = None


def _collect_tasks(
    tests_dir: str,
    *,
    frontend_host: str,
    track_suffix: str,
    task_filter: Optional[str],
    max_tasks: Optional[int],
) -> list[tuple[str, dict, str, str, str]]:
    """Return (test_name, config, config_path, track_id, task) for each selected task."""
    selected: list[tuple[str, dict, str, str, str]] = []
    for config_path, config in sorted(build_test_configs(tests_dir).items()):
        test_name = config["test_data"]["test_name"]
        if task_filter and task_filter not in test_name:
            continue
        track_id = f"{test_name.replace(' ', '_').lower()}__{track_suffix}"
        task = config["test_data"]["task"].replace(
            "%HOST%", f"http://{frontend_host}/{track_id}"
        )
        selected.append((test_name, config, config_path, track_id, task))
        if max_tasks is not None and len(selected) >= max_tasks:
            break
    return selected


async def run_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config()
    tests_dir = args.tests_dir or config.resolved_tests_dir()
    track_suffix = args.track_suffix or uuid.uuid4().hex[:8]

    overrides: dict[str, Any] = {}
    if args.max_steps:
        overrides["max_steps"] = args.max_steps
    if args.screenshots:
        overrides["save_screenshots"] = True

    settings = build_settings(args.model, eval_config=config, overrides=overrides)
    tasks = _collect_tasks(
        tests_dir,
        frontend_host=config.frontend_host,
        track_suffix=track_suffix,
        task_filter=args.task_filter,
        max_tasks=args.max_tasks,
    )
    print(
        f"[benchmark] model={settings.spec.name} tasks={len(tasks)} "
        f"endpoint={settings.endpoint.base_url} max_steps={settings.max_steps}",
        flush=True,
    )

    outcomes: list[TaskOutcome] = []
    started_at = time.perf_counter()

    for index, (test_name, task_config, config_path, track_id, task) in enumerate(tasks, start=1):
        print(f"\n[benchmark] ({index}/{len(tasks)}) {test_name}", flush=True)
        outcome = TaskOutcome(
            test_name=test_name,
            track_id=track_id,
            task=task,
            entry_url=None,
        )

        created = create_track(
            test_name=test_name,
            track_id=track_id,
            config_path=config_path,
            api_address=config.api_address,
            https=config.https,
        )
        if created is None:
            outcome.error = "failed to create track on the WebPageBench backend"
            outcome.status = "track_error"
            outcomes.append(outcome)
            continue

        task_url = f"http://{config.frontend_host}/{track_id}"
        entry_url = resolve_entry_url(task_url, config_path)
        outcome.entry_url = entry_url

        if args.screenshots:
            settings.screenshot_dir = str(Path(args.screenshots) / test_name)

        agent = build_agent(settings)
        computer = BrowserComputer.from_eval_config(
            config,
            width=settings.screen_width,
            height=settings.screen_height,
        )
        computer.settle_seconds = settings.action_settle_seconds
        try:
            await computer.start()
            await computer.goto(entry_url, wait_seconds=config.agent_warmup_settle_seconds)
            result = await run_agent_loop(
                agent, computer, task, settings=settings, log_prefix=settings.spec.name
            )
            outcome.steps = result.step_count
            outcome.status = result.status
            outcome.is_done = result.is_done
            outcome.duration_seconds = round(result.duration_seconds, 2)
            outcome.token_usage = dict(result.token_usage or {})
            outcome.final_result = result.final_result
            outcome.error = result.error
        except Exception as exc:  # noqa: BLE001 - one bad task must not stop the sweep
            outcome.status = "error"
            outcome.error = f"{type(exc).__name__}: {exc}"
        finally:
            await computer.close()
            await agent.close()

        checks = summarize_checks(check_track(track_id, config.api_address, https=config.https))
        outcome.passed = checks["passed"]
        outcome.failed = checks["failed"]
        outcome.total = checks["total"]
        outcome.score = checks["score"]
        outcome.all_passed = checks["all_passed"]
        outcome.failed_conditions = checks["failed_conditions"]
        outcomes.append(outcome)

        print(
            f"[benchmark] {test_name}: status={outcome.status} steps={outcome.steps} "
            f"checks={outcome.passed}/{outcome.total} score={outcome.score:.2f}",
            flush=True,
        )

    solved = sum(1 for item in outcomes if item.all_passed)
    report = {
        "model": settings.spec.name,
        "family": settings.spec.family,
        "served_model": settings.endpoint.model,
        "base_url": settings.endpoint.base_url,
        "action_space": settings.spec.action_space.name,
        "coordinate_space": settings.coordinate_space.value,
        "options": settings.options,
        "tests_dir": tests_dir,
        "track_suffix": track_suffix,
        "max_steps": settings.max_steps,
        "task_count": len(outcomes),
        "solved": solved,
        "success_rate": round(solved / len(outcomes), 4) if outcomes else 0.0,
        "mean_condition_score": (
            round(sum(item.score for item in outcomes) / len(outcomes), 4) if outcomes else 0.0
        ),
        "duration_seconds": round(time.perf_counter() - started_at, 2),
        "tasks": [asdict(item) for item in outcomes],
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch-run a GUI model on tests/bench")
    parser.add_argument("model", help="Registered model name or alias")
    parser.add_argument("--tests-dir", help="Defaults to EVAL_MOCK (tests/bench)")
    parser.add_argument("--task-filter", help="Substring match on the task name")
    parser.add_argument("--max-tasks", type=int)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--track-suffix", help="Reuse a fixed suffix instead of a random one")
    parser.add_argument("--screenshots", metavar="DIR", help="Save per-step PNGs under DIR/<task>")
    parser.add_argument("--output", type=Path, help="Write the JSON report here")
    args = parser.parse_args(argv)

    report = asyncio.run(run_benchmark(args))

    print(
        f"\n[benchmark] {report['model']}: solved {report['solved']}/{report['task_count']} "
        f"({report['success_rate']:.1%}), mean condition score {report['mean_condition_score']:.3f}",
        flush=True,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[benchmark] report → {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
