"""Extended efficiency and agreement metrics for eval results.json artifacts."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any

from bench_eval.token_usage import normalize_token_usage


def _jsonable_signature(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return str(value)


def extract_action_signatures(trajectory: dict[str, Any] | None) -> list[str]:
    """Collect comparable action signatures from a browser-use trajectory."""
    if not trajectory:
        return []

    agent = trajectory.get("agent") or {}
    summary = agent.get("summary") or {}

    model_actions = summary.get("model_actions")
    if isinstance(model_actions, list) and model_actions:
        return [_jsonable_signature(item) for item in model_actions]

    action_names = summary.get("action_names")
    if isinstance(action_names, list) and action_names:
        return [_jsonable_signature(item) for item in action_names]

    signatures: list[str] = []
    for step in agent.get("steps") or []:
        if not isinstance(step, dict):
            continue
        model_output = step.get("model_output")
        if model_output is None:
            continue
        signatures.append(_jsonable_signature(model_output))
    return signatures


def compute_action_redundancy(signatures: list[str]) -> float:
    """Share of duplicate actions (analog of ToolRedundancy for browser agents)."""
    if not signatures:
        return 0.0
    return (len(signatures) - len(set(signatures))) / len(signatures)


def compute_token_efficiency(*, success: bool, total_tokens: int | None) -> float:
    """Inverse token count for successful tasks; 0 otherwise."""
    if not success or not total_tokens or total_tokens <= 0:
        return 0.0
    return 1.0 / total_tokens


def compute_avg_latency(
    duration_seconds: float | int | None,
    llm_calls: int | None,
) -> float | None:
    """Average seconds per LLM call."""
    if duration_seconds is None or not llm_calls or llm_calls <= 0:
        return None
    return float(duration_seconds) / llm_calls


def _test_duration_seconds(test: dict[str, Any]) -> float | None:
    agent = test.get("agent") or {}
    duration = agent.get("duration_seconds")
    if isinstance(duration, (int, float)):
        return float(duration)
    duration = test.get("duration_seconds")
    if isinstance(duration, (int, float)):
        return float(duration)
    return None


def _test_llm_calls(test: dict[str, Any]) -> int:
    usage = normalize_token_usage(test.get("token_usage"))
    llm_calls = usage.get("llm_calls") or 0
    if llm_calls > 0:
        return llm_calls
    steps = test.get("agent_steps")
    if isinstance(steps, int) and steps > 0:
        return steps
    return 0


def compute_test_extended_metrics(test: dict[str, Any]) -> dict[str, Any]:
    """Per-task extended metrics derived from an existing results.json test row."""
    success = bool(test.get("success"))
    agent_is_done = test.get("agent_is_done")
    usage = normalize_token_usage(test.get("token_usage"))
    total_tokens = usage.get("total_tokens") or test.get("tokens")
    llm_calls = _test_llm_calls(test)
    duration = _test_duration_seconds(test)
    signatures = extract_action_signatures(test.get("trajectory"))

    false_done = agent_is_done is True and not success
    false_incomplete = agent_is_done is False and success
    agreement = None
    if agent_is_done is not None:
        agreement = success == bool(agent_is_done)

    return {
        "token_efficiency": compute_token_efficiency(
            success=success,
            total_tokens=total_tokens if isinstance(total_tokens, int) else None,
        ),
        "avg_latency_seconds": compute_avg_latency(duration, llm_calls),
        "action_redundancy": compute_action_redundancy(signatures),
        "action_count": len(signatures),
        "agent_dab_agreement": agreement,
        "false_done": false_done,
        "false_incomplete": false_incomplete,
    }


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def compute_run_extended_metrics(tests: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate extended metrics across all tasks in one run."""
    token_efficiencies: list[float] = []
    latencies: list[float] = []
    redundancies: list[float] = []
    completion_flags: list[bool] = []
    agreement_flags: list[bool] = []
    false_done_count = 0
    false_incomplete_count = 0
    tasks_with_trajectory = 0

    for test in tests:
        extended = compute_test_extended_metrics(test)
        token_efficiencies.append(extended["token_efficiency"])
        if extended["avg_latency_seconds"] is not None:
            latencies.append(extended["avg_latency_seconds"])
        if extended["action_count"] > 0:
            redundancies.append(extended["action_redundancy"])
            tasks_with_trajectory += 1
        if test.get("agent_is_done") is not None:
            completion_flags.append(bool(test.get("agent_is_done")))
        if extended["agent_dab_agreement"] is not None:
            agreement_flags.append(bool(extended["agent_dab_agreement"]))
        if extended["false_done"]:
            false_done_count += 1
        if extended["false_incomplete"]:
            false_incomplete_count += 1

    total = len(tests)
    return {
        "avg_token_efficiency": _mean(token_efficiencies),
        "avg_latency_per_llm_call_seconds": _mean(latencies),
        "avg_action_redundancy": _mean(redundancies),
        "agent_completion_rate": (
            sum(1 for flag in completion_flags if flag) / len(completion_flags)
            if completion_flags
            else None
        ),
        "agent_dab_agreement_rate": (
            sum(1 for flag in agreement_flags if flag) / len(agreement_flags)
            if agreement_flags
            else None
        ),
        "false_done_count": false_done_count,
        "false_done_rate": (false_done_count / total) if total else None,
        "false_incomplete_count": false_incomplete_count,
        "false_incomplete_rate": (false_incomplete_count / total) if total else None,
        "tasks_with_trajectory": tasks_with_trajectory,
    }


def pass_at_k_unbiased(*, successes: int, attempts: int, k: int) -> float | None:
    """Unbiased Pass@k estimate (same formula as toolcall_metrics)."""
    if k > attempts:
        return None
    if attempts - successes < k:
        return 1.0
    return 1.0 - math.comb(attempts - successes, k) / math.comb(attempts, k)


def compute_pass_at_k(
    payloads: list[dict[str, Any]],
    *,
    k: int,
) -> dict[str, Any] | None:
    """
    Compute Pass@k across multiple eval runs for the same harness × model.

    Each payload is a full results.json document. Attempts are grouped by
  ``test_name``; at most one attempt per run is counted.
    """
    if k < 1 or len(payloads) < 2:
        return None

    attempts_by_task: dict[str, list[bool]] = {}
    run_ids: list[str] = []

    for payload in payloads:
        run = payload.get("run") or {}
        run_ids.append(str(run.get("output_dir") or run.get("started_at") or len(run_ids)))
        seen_in_run: set[str] = set()
        for test in payload.get("tests") or []:
            if not isinstance(test, dict):
                continue
            name = test.get("test_name")
            if not name or name in seen_in_run:
                continue
            seen_in_run.add(name)
            attempts_by_task.setdefault(str(name), []).append(bool(test.get("success")))

    if not attempts_by_task:
        return None

    per_task: dict[str, float | None] = {}
    scored: list[float] = []
    for task_name, attempts in sorted(attempts_by_task.items()):
        n = len(attempts)
        c = sum(1 for item in attempts if item)
        score = pass_at_k_unbiased(successes=c, attempts=n, k=k)
        per_task[task_name] = score
        if score is not None:
            scored.append(score)

    if not scored:
        return None

    return {
        "k": k,
        "run_count": len(payloads),
        "task_count": len(per_task),
        "overall": sum(scored) / len(scored),
        "per_task": per_task,
        "source_run_ids": run_ids,
    }


def enrich_results_payload(
    payload: dict[str, Any],
    *,
    pass_at_k: dict[str, Any] | None = None,
    enriched_at: datetime | None = None,
    enriched_by: str = "bench_eval.extended_metrics",
) -> dict[str, Any]:
    """Return a copy of ``payload`` with extended metrics attached."""
    moment = enriched_at or datetime.now(timezone.utc)
    tests = payload.get("tests") or []
    run = dict(payload.get("run") or {})

    enriched_tests: list[dict[str, Any]] = []
    for test in tests:
        if not isinstance(test, dict):
            enriched_tests.append(test)
            continue
        row = dict(test)
        row["extended_metrics"] = compute_test_extended_metrics(row)
        enriched_tests.append(row)

    run_metrics = compute_run_extended_metrics(enriched_tests)
    run_metrics["enriched_at"] = moment.isoformat()
    if pass_at_k is not None:
        run_metrics["pass_at_k"] = pass_at_k
    run["extended_metrics"] = run_metrics

    enriched = dict(payload)
    enriched["run"] = run
    enriched["tests"] = enriched_tests
    enriched["extended_metrics_meta"] = {
        "enriched_at": moment.isoformat(),
        "enriched_by": enriched_by,
        "schema_version": 1,
    }
    return enriched
