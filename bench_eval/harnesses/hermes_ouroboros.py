"""hermes-ouroboros harness: council planning layer + browser-use execution."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any, Optional

from bench_eval.config import EvalConfig
from bench_eval.harnesses.base import AgentRunResult, normalize_agent_result
from bench_eval.harnesses.browser_use import run_browser_use_harness
from bench_eval.hermes_config import HermesHarnessConfig, load_hermes_harness_config


def _build_enhanced_task(
    task: str,
    verdict: Any,
    *,
    hermes_config: HermesHarnessConfig,
) -> str:
    """Augment the browser task with HERMES council guidance."""
    enhancement = hermes_config.task_enhancement
    if not enhancement.enabled:
        return task

    sections = []
    if enhancement.include_summary and getattr(verdict, "summary", None):
        sections.append(f"HERMES council summary:\n{verdict.summary}")
    if enhancement.include_full_verdict and getattr(verdict, "full_verdict", None):
        sections.append(f"HERMES arbiter verdict:\n{verdict.full_verdict}")

    if enhancement.include_fatal_flaws:
        fatal_flaws = getattr(verdict, "verdict_sections", {}).get("fatal_flaws")
        if fatal_flaws:
            sections.append(f"Potential pitfalls to avoid:\n{fatal_flaws}")

    guidance = "\n\n".join(section.strip() for section in sections if section)
    if not guidance:
        return task

    return (
        f"{task.strip()}\n\n"
        "---\n"
        "Strategic guidance from the HERMES adversarial council "
        f"(mode={getattr(verdict, 'analysis_mode', hermes_config.analysis_mode)}):\n"
        f"{guidance}\n"
        "---\n"
        f"{enhancement.instruction.strip()}"
    )


def _serialize_verdict(verdict: Any) -> dict[str, Any]:
    return {
        "score": getattr(verdict, "score", None),
        "label": getattr(verdict, "label", None),
        "summary": getattr(verdict, "summary", None),
        "confidence": getattr(verdict, "confidence", None),
        "analysis_mode": getattr(verdict, "analysis_mode", None),
        "session_id": getattr(verdict, "session_id", None),
        "agent_responses": getattr(verdict, "agent_responses", None),
        "web_evidence": getattr(verdict, "web_evidence", None),
        "verdict_sections": getattr(verdict, "verdict_sections", None),
    }


async def run_hermes_ouroboros_harness(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    """
    Run HERMES council deliberation, then execute the task with browser-use.

    HERMES acts as the planning harness between DeepEval and the underlying
    LLM-driven browser agent.
    """
    from hermes_ouroboros import HermesClient

    hermes_config = load_hermes_harness_config(config.hermes_config_path)
    started_at = time.perf_counter()
    hermes_error: Optional[str] = None
    verdict_payload: dict[str, Any] = {}
    enhanced_task = task

    try:
        with HermesClient(
            api_key=hermes_config.api_key,
            base_url=hermes_config.api_base_url,
            timeout=hermes_config.timeout_seconds,
        ) as client:
            query = hermes_config.build_planning_query(task)
            mode = hermes_config.analysis_mode
            if mode == "verify":
                verdict = client.verify(query)
            elif mode == "red_team":
                verdict = client.red_team(query)
            else:
                verdict = client.research(query)
            verdict_payload = _serialize_verdict(verdict)
            enhanced_task = _build_enhanced_task(
                task,
                verdict,
                hermes_config=hermes_config,
            )
    except Exception as exc:
        hermes_error = str(exc)
        if hermes_config.on_api_error == "fail":
            raise

    deliberation_seconds = time.perf_counter() - started_at
    browser_config = config
    if hermes_config.browser_max_steps is not None:
        browser_config = replace(
            config,
            agent_max_steps=hermes_config.resolved_browser_max_steps(config.agent_max_steps),
        )

    browser_result = await run_browser_use_harness(
        enhanced_task,
        config=browser_config,
        task_url=task_url,
        entry_url=entry_url,
    )

    harness_metadata = {
        "config_path": hermes_config.config_path,
        "deliberation_seconds": deliberation_seconds,
        "mode": hermes_config.analysis_mode,
        "base_url": hermes_config.api_base_url,
        "verdict": verdict_payload,
        "error": hermes_error,
        "task_enhanced": enhanced_task != task,
        "on_api_error": hermes_config.on_api_error,
    }

    merged = dict(browser_result)
    merged["harness"] = "hermes-ouroboros"
    merged["harness_metadata"] = harness_metadata
    merged["duration_seconds"] = float(browser_result.get("duration_seconds") or 0.0) + (
        deliberation_seconds if hermes_error is None else 0.0
    )
    return normalize_agent_result(merged, harness="hermes-ouroboros")
