"""Load JSON configuration for the hermes-ouroboros eval harness."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

DEFAULT_HERMES_CONFIG_PATH = "configs/hermes_ouroboros.default.json"
_VALID_ANALYSIS_MODES = frozenset({"verify", "red_team", "research", "default"})
_VALID_ON_API_ERROR = frozenset({"continue_with_original_task", "fail"})


@dataclass(frozen=True)
class HermesTaskEnhancementConfig:
    enabled: bool = True
    include_summary: bool = True
    include_full_verdict: bool = True
    include_fatal_flaws: bool = True
    instruction: str = (
        "Execute the web task above in the browser. "
        "Use the council guidance as planning context, not as a substitute "
        "for interacting with the site."
    )


@dataclass(frozen=True)
class HermesHarnessConfig:
    """Client-side settings for bench_eval hermes-ouroboros harness."""

    config_path: str
    api_base_url: str = "http://127.0.0.1:8000"
    api_key: Optional[str] = None
    timeout_seconds: float = 300.0
    analysis_mode: str = "research"
    planning_prompt_prefix: str = (
        "You are planning a browser automation task on a mock e-commerce site."
    )
    planning_prompt_suffix: str = (
        "Identify the safest step-by-step strategy, likely UI pitfalls, "
        "and success criteria for completing this task in a real browser."
    )
    on_api_error: str = "continue_with_original_task"
    browser_inherit_from_eval: bool = True
    browser_max_steps: Optional[int] = None
    task_enhancement: HermesTaskEnhancementConfig = HermesTaskEnhancementConfig()

    def build_planning_query(self, task: str) -> str:
        return (
            f"{self.planning_prompt_prefix.strip()}\n\n"
            f"Task:\n{task.strip()}\n\n"
            f"{self.planning_prompt_suffix.strip()}"
        )

    def resolved_browser_max_steps(self, eval_agent_max_steps: int) -> int:
        if self.browser_max_steps is not None:
            return self.browser_max_steps
        return eval_agent_max_steps


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    section = data.get(name, {})
    return section if isinstance(section, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_hermes_harness_config(
    config_path: Optional[str] = None,
    *,
    env: Optional[dict[str, str]] = None,
) -> HermesHarnessConfig:
    """
    Load hermes harness config from JSON and apply env overrides.

    Precedence (highest last):
    1. JSON file defaults
    2. HERMES_* / HERMES_OUROBOROS_* environment variables
  3. AGENT_MAX_STEPS for browser.max_steps when JSON value is null
    """
    env = env if env is not None else os.environ
    resolved_path = config_path or env.get("HERMES_CONFIG_PATH", DEFAULT_HERMES_CONFIG_PATH)
    raw = _load_json(Path(resolved_path))

    api = _section(raw, "api")
    council = _section(raw, "council")
    browser = _section(raw, "browser")
    enhancement = _section(raw, "task_enhancement")

    analysis_mode = str(
        env.get("HERMES_MODE", council.get("analysis_mode", "research"))
    ).strip().lower()
    if analysis_mode not in _VALID_ANALYSIS_MODES - {"default"}:
        analysis_mode = "research"

    on_api_error = str(
        env.get("HERMES_ON_API_ERROR", council.get("on_api_error", "continue_with_original_task"))
    ).strip()
    if on_api_error not in _VALID_ON_API_ERROR:
        on_api_error = "continue_with_original_task"

    browser_max_steps_raw = browser.get("max_steps")
    if env.get("HERMES_BROWSER_MAX_STEPS"):
        browser_max_steps_raw = env.get("HERMES_BROWSER_MAX_STEPS")
    browser_max_steps = (
        int(browser_max_steps_raw) if browser_max_steps_raw not in (None, "") else None
    )

    return HermesHarnessConfig(
        config_path=resolved_path,
        api_base_url=env.get("HERMES_BASE_URL", api.get("base_url", "http://127.0.0.1:8000")),
        api_key=env.get("HERMES_API_KEY")
        or env.get("HERMES_OUROBOROS_API_KEY")
        or api.get("api_key"),
        timeout_seconds=float(env.get("HERMES_TIMEOUT", api.get("timeout_seconds", 300))),
        analysis_mode=analysis_mode,
        planning_prompt_prefix=str(
            council.get(
                "planning_prompt_prefix",
                "You are planning a browser automation task on a mock e-commerce site.",
            )
        ),
        planning_prompt_suffix=str(
            council.get(
                "planning_prompt_suffix",
                "Identify the safest step-by-step strategy, likely UI pitfalls, "
                "and success criteria for completing this task in a real browser.",
            )
        ),
        on_api_error=on_api_error,
        browser_inherit_from_eval=bool(browser.get("inherit_from_eval_config", True)),
        browser_max_steps=browser_max_steps,
        task_enhancement=HermesTaskEnhancementConfig(
            enabled=bool(enhancement.get("enabled", True)),
            include_summary=bool(enhancement.get("include_summary", True)),
            include_full_verdict=bool(enhancement.get("include_full_verdict", True)),
            include_fatal_flaws=bool(enhancement.get("include_fatal_flaws", True)),
            instruction=str(
                enhancement.get(
                    "instruction",
                    "Execute the web task above in the browser. "
                    "Use the council guidance as planning context, not as a substitute "
                    "for interacting with the site.",
                )
            ),
        ),
    )
