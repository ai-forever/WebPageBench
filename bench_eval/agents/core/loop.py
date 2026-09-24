"""Family-agnostic agent loop: observe → predict → act → record."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from bench_eval.agents.core import dump
from bench_eval.agents.core.actions import Action, ActionType
from bench_eval.agents.core.base import GUIAgent, Observation, Prediction
from bench_eval.agents.core.executor import ActionResult, BrowserComputer
from bench_eval.agents.core.settings import AgentSettings
from bench_eval.token_usage import TokenUsage

StepCallback = Callable[["StepRecord"], Awaitable[None]]


@dataclass
class StepRecord:
    step: int
    url: Optional[str]
    prediction: Prediction
    results: list[ActionResult]
    duration_seconds: float
    screenshot_path: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "step": self.step,
            "url": self.url,
            "duration_seconds": round(self.duration_seconds, 3),
            "model_output": self.prediction.to_dict(),
            "result": [item.to_dict() for item in self.results],
        }
        if self.screenshot_path:
            payload["screenshot"] = self.screenshot_path
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass
class LoopResult:
    steps: list[StepRecord] = field(default_factory=list)
    is_done: bool = False
    #: "success" | "failure" | "max_steps" | "max_failures" | "error"
    status: str = "max_steps"
    final_result: Optional[str] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    token_usage_by_model: dict[str, TokenUsage] = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def trajectory(self, *, harness: str, metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Shape expected by ``bench_eval.trajectory.build_trajectory``."""
        action_names: list[str] = []
        errors: list[str] = []
        urls: list[str] = []
        for record in self.steps:
            if record.url:
                urls.append(record.url)
            if record.error:
                errors.append(record.error)
            for result in record.results:
                action_names.append(result.action.type.value)
                if result.error:
                    errors.append(result.error)
        return {
            "steps": [record.to_dict() for record in self.steps],
            "summary": {
                "step_count": self.step_count,
                "is_done": self.is_done,
                "is_successful": self.status == "success" if self.is_done else None,
                "final_result": self.final_result,
                "status": self.status,
                "urls": urls,
                "errors": errors,
                "action_names": action_names,
                "total_duration_seconds": round(self.duration_seconds, 3),
            },
            "harness": harness,
            "metadata": metadata or {},
        }


async def run_agent_loop(
    agent: GUIAgent,
    computer: BrowserComputer,
    instruction: str,
    *,
    settings: AgentSettings,
    on_step: Optional[StepCallback] = None,
    log_prefix: str = "gui-agent",
) -> LoopResult:
    """Drive one task to completion, a terminal action, or the step budget."""
    result = LoopResult()
    started_at = time.perf_counter()
    consecutive_failures = 0
    screenshot_dir = _screenshot_dir(settings)
    last_pointer: tuple[float, float] = (
        settings.screen_width / 2,
        settings.screen_height / 2,
    )

    agent.reset()
    dump.set_context(instruction=instruction)

    for step_index in range(settings.max_steps):
        step_started = time.perf_counter()
        # Model calls made below land in the dump under this step (see core/dump.py).
        dump.set_context(step=step_index + 1, url=computer.url)
        screenshot_path: Optional[str] = None
        url = computer.url

        # Observing, predicting and acting all share one failure path: any of the
        # three can fail on a wedged page, and none of them may end the run.
        try:
            screenshot = await computer.screenshot()
            screenshot_path = _save_screenshot(screenshot_dir, step_index, screenshot)
            observation = Observation(
                screenshot=screenshot,
                screen_width=computer.width,
                screen_height=computer.height,
                url=url,
                step_index=step_index,
            )
            prediction = await agent.predict(instruction, observation)
            actions = agent.coerce(prediction.actions)
            actions = [_fill_drag_origin(action, last_pointer) for action in actions]
            results = await computer.execute_all(actions)
        except Exception as exc:  # noqa: BLE001 - a bad step should not lose the run
            consecutive_failures += 1
            record = StepRecord(
                step=step_index + 1,
                url=url,
                prediction=Prediction(actions=[], error=str(exc)),
                results=[],
                duration_seconds=time.perf_counter() - step_started,
                screenshot_path=screenshot_path,
                error=f"step failed: {type(exc).__name__}: {exc}",
            )
            result.steps.append(record)
            print(f"[{log_prefix}] step {step_index + 1} error: {exc}", flush=True)
            if consecutive_failures >= settings.max_failures:
                result.status = "max_failures"
                result.error = record.error
                break
            continue

        consecutive_failures = 0 if actions else consecutive_failures + 1
        for action in actions:
            if action.x is not None and action.y is not None:
                last_pointer = (action.x, action.y)

        record = StepRecord(
            step=step_index + 1,
            url=observation.url,
            prediction=Prediction(
                actions=actions,
                raw_response=prediction.raw_response,
                thought=prediction.thought,
                action_description=prediction.action_description,
                metadata=prediction.metadata,
                error=prediction.error,
            ),
            results=results,
            duration_seconds=time.perf_counter() - step_started,
            screenshot_path=screenshot_path,
        )
        result.steps.append(record)
        if on_step is not None:
            await on_step(record)

        print(
            f"[{log_prefix}] step {step_index + 1}/{settings.max_steps}: "
            f"{' | '.join(action.describe() for action in actions) or '<no action>'}",
            flush=True,
        )

        terminal = next((action for action in actions if action.is_terminal), None)
        if terminal is not None:
            result.is_done = True
            result.status = "success" if terminal.is_success else "failure"
            result.final_result = terminal.text or prediction.action_description or terminal.describe()
            break

        if consecutive_failures >= settings.max_failures:
            result.status = "max_failures"
            result.error = "model produced no executable action"
            break

    result.duration_seconds = time.perf_counter() - started_at
    usage, by_model = agent.ledger.snapshot()
    result.token_usage = usage
    result.token_usage_by_model = by_model
    if result.final_result is None and result.steps:
        result.final_result = result.steps[-1].prediction.action_description
    return result


def _fill_drag_origin(action: Action, last_pointer: tuple[float, float]) -> Action:
    """``pyautogui.dragTo`` drags from the current cursor; carry that over."""
    if action.type is ActionType.DRAG and action.x is None and action.to_x is not None:
        action.x, action.y = last_pointer
    return action


def _screenshot_dir(settings: AgentSettings) -> Optional[Path]:
    if not settings.save_screenshots:
        return None
    target = Path(settings.screenshot_dir or "tests/eval/gui-agent-screenshots")
    target.mkdir(parents=True, exist_ok=True)
    return target


def _save_screenshot(directory: Optional[Path], step_index: int, data: bytes) -> Optional[str]:
    if directory is None:
        return None
    path = directory / f"step_{step_index + 1:03d}.png"
    path.write_bytes(data)
    return str(path)
