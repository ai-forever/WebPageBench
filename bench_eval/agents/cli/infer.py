"""Single-task inference: drive one URL with a GUI model and print the actions.

Smoke-tests an endpoint, a prompt, and the coordinate mapping without touching
DeepEval or the WebPageBench backend.

    python -m bench_eval.agents.cli.infer qwen3-vl-8b \\
        --url http://127.0.0.1:5173/<track_id>/state_hub/bench_hub \\
        --task "Найди чайник и добавь его в корзину" --max-steps 8

    # one prediction from a saved screenshot, no browser at all
    python -m bench_eval.agents.cli.infer uitars-1.5-7b \\
        --screenshot shot.png --task "Открой раздел Книги" --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from bench_eval.agents.core.base import Observation
from bench_eval.agents.core.executor import BrowserComputer
from bench_eval.agents.core.images import image_size
from bench_eval.agents.core.loop import run_agent_loop
from bench_eval.agents.core.settings import build_agent, build_settings


async def _predict_once(model: str, screenshot: Path, task: str, overrides: dict) -> int:
    settings = build_settings(model, overrides=overrides)
    agent = build_agent(settings)
    data = screenshot.read_bytes()
    width, height = image_size(data)
    observation = Observation(
        screenshot=data,
        screen_width=width,
        screen_height=height,
        url=str(screenshot),
    )
    try:
        prediction = await agent.predict(task, observation)
    finally:
        await agent.close()

    print(json.dumps(prediction.to_dict(), indent=2, ensure_ascii=False))
    return 0 if prediction.actions else 1


async def _run_browser(model: str, url: str, task: str, overrides: dict, headless: bool) -> int:
    settings = build_settings(model, overrides=overrides)
    agent = build_agent(settings)
    computer = BrowserComputer(
        width=settings.screen_width,
        height=settings.screen_height,
        headless=headless,
        settle_seconds=settings.action_settle_seconds,
    )
    try:
        await computer.start()
        await computer.goto(url)
        result = await run_agent_loop(agent, computer, task, settings=settings, log_prefix=model)
    finally:
        await computer.close()
        await agent.close()

    print(
        json.dumps(
            {
                "status": result.status,
                "is_done": result.is_done,
                "steps": result.step_count,
                "final_result": result.final_result,
                "duration_seconds": round(result.duration_seconds, 2),
                "token_usage": result.token_usage,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if result.is_done else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one GUI model on one task")
    parser.add_argument("model", help="Registered model name or alias")
    parser.add_argument("--task", required=True, help="Task instruction")
    parser.add_argument("--url", help="Start URL (browser mode)")
    parser.add_argument("--screenshot", type=Path, help="PNG file (single-prediction mode)")
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--headed", action="store_true", help="Show the browser window")
    parser.add_argument("--save-screenshots", metavar="DIR", help="Write per-step PNGs here")
    parser.add_argument("--dry-run", action="store_true", help="One prediction only, no execution")
    args = parser.parse_args(argv)

    overrides: dict = {"max_steps": args.max_steps}
    if args.save_screenshots:
        overrides["save_screenshots"] = True
        overrides["screenshot_dir"] = args.save_screenshots

    if args.screenshot or args.dry_run:
        if not args.screenshot:
            parser.error("--dry-run requires --screenshot")
        return asyncio.run(_predict_once(args.model, args.screenshot, args.task, overrides))

    if not args.url:
        parser.error("either --url or --screenshot is required")
    return asyncio.run(_run_browser(args.model, args.url, args.task, overrides, not args.headed))


if __name__ == "__main__":
    raise SystemExit(main())
