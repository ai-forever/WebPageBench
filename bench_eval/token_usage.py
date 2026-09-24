"""Normalize LLM token usage from agent harness history objects."""

from __future__ import annotations

from typing import Any, Mapping, TypedDict


class TokenUsage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    llm_calls: int


class ModelTokenUsage(TypedDict, total=False):
    """Per-model token/cost counters (fallback, review, auxiliary slots)."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    llm_calls: int
    cost_usd: float
    roles: list[str]


def empty_token_usage() -> TokenUsage:
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "llm_calls": 0,
    }


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _pick_int(payload: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        if key not in payload:
            continue
        coerced = _coerce_int(payload.get(key))
        if coerced is not None:
            return coerced
    return None


def normalize_token_usage(payload: dict[str, Any] | None) -> TokenUsage:
    """Return a stable token usage dict with non-negative integers."""
    if not payload:
        return empty_token_usage()

    prompt = _pick_int(
        payload,
        "prompt_tokens",
        "total_prompt_tokens",
        "input_tokens",
    )
    completion = _pick_int(
        payload,
        "completion_tokens",
        "total_completion_tokens",
        "output_tokens",
    )
    total = _pick_int(payload, "total_tokens")
    llm_calls = _pick_int(payload, "llm_calls", "entry_count", "invocations")

    prompt = max(prompt or 0, 0)
    completion = max(completion or 0, 0)
    if total is None:
        total = prompt + completion
    total = max(total, 0)
    llm_calls = max(llm_calls or 0, 0)

    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "llm_calls": llm_calls,
    }


def _usage_to_dict(usage: Any) -> dict[str, Any]:
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return usage
    if hasattr(usage, "model_dump"):
        try:
            return usage.model_dump(mode="json")
        except TypeError:
            return usage.model_dump()
    if hasattr(usage, "dict"):
        return usage.dict()
    return {key: getattr(usage, key) for key in dir(usage) if not key.startswith("_")}


def extract_token_usage_from_history(history: Any) -> TokenUsage:
    """
    Extract token totals from a browser-use AgentHistoryList (or compatible object).

    Requires ``calculate_cost=True`` on the browser-use Agent so ``history.usage``
    is populated after ``agent.run()``.
    """
    if history is None:
        return empty_token_usage()

    usage = getattr(history, "usage", None)
    if usage is not None:
        return normalize_token_usage(_usage_to_dict(usage))

    return empty_token_usage()


def extract_token_usage_from_messages(messages: Any) -> TokenUsage:
    """Sum token usage from LangChain message lists (deepagents / LangGraph)."""
    if not messages:
        return empty_token_usage()

    merged = empty_token_usage()
    llm_calls = 0
    for message in messages:
        role = getattr(message, "type", None) or getattr(message, "role", None)
        if role not in {"ai", "assistant"}:
            continue

        usage = getattr(message, "usage_metadata", None)
        if usage is None:
            response_metadata = getattr(message, "response_metadata", None) or {}
            if isinstance(response_metadata, dict):
                usage = response_metadata.get("token_usage")
        if not usage:
            continue

        merged = merge_token_usage(merged, normalize_token_usage(_usage_to_dict(usage)))
        llm_calls += 1

    if llm_calls and merged["llm_calls"] == 0:
        merged["llm_calls"] = llm_calls
    return merged


def merge_token_usage(*usages: TokenUsage | dict[str, Any] | None) -> TokenUsage:
    """Sum token counters from multiple harness stages (e.g. HERMES + browser-use)."""
    merged = empty_token_usage()
    for usage in usages:
        normalized = normalize_token_usage(usage)
        merged["prompt_tokens"] += normalized["prompt_tokens"]
        merged["completion_tokens"] += normalized["completion_tokens"]
        merged["total_tokens"] += normalized["total_tokens"]
        merged["llm_calls"] += normalized["llm_calls"]
    return merged


def empty_model_token_usage() -> ModelTokenUsage:
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "llm_calls": 0,
    }


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def normalize_model_token_usage(payload: dict[str, Any] | None) -> ModelTokenUsage:
    """Return stable per-model usage counters with optional recorded cost."""
    normalized = normalize_token_usage(payload)
    result: ModelTokenUsage = {
        "prompt_tokens": normalized["prompt_tokens"],
        "completion_tokens": normalized["completion_tokens"],
        "total_tokens": normalized["total_tokens"],
        "llm_calls": normalized["llm_calls"],
    }
    if not payload:
        return result

    for key in ("cost_usd", "total_cost_usd", "cost", "total_cost"):
        cost = _coerce_float(payload.get(key))
        if cost is not None and cost > 0:
            result["cost_usd"] = cost
            break

    roles = payload.get("roles")
    if isinstance(roles, list):
        cleaned = sorted({str(role).strip() for role in roles if str(role).strip()})
        if cleaned:
            result["roles"] = cleaned
    return result


def merge_token_usage_by_model(
    *maps: Mapping[str, ModelTokenUsage | dict[str, Any] | None] | None,
) -> dict[str, ModelTokenUsage]:
    """Sum per-model counters across harness stages or eval tasks."""
    merged: dict[str, ModelTokenUsage] = {}
    for usage_map in maps:
        if not usage_map:
            continue
        for model, usage in usage_map.items():
            model_name = str(model or "").strip() or "unknown"
            current = merged.setdefault(model_name, empty_model_token_usage())
            normalized = normalize_model_token_usage(usage if isinstance(usage, dict) else None)
            current["prompt_tokens"] += normalized["prompt_tokens"]
            current["completion_tokens"] += normalized["completion_tokens"]
            current["total_tokens"] += normalized["total_tokens"]
            current["llm_calls"] += normalized["llm_calls"]
            if "cost_usd" in normalized and normalized["cost_usd"] > 0:
                current["cost_usd"] = float(current.get("cost_usd") or 0.0) + normalized["cost_usd"]
            roles = normalized.get("roles") or []
            if roles:
                existing = set(current.get("roles") or [])
                current["roles"] = sorted(existing.union(roles))
    return merged


def aggregate_token_usage_by_model(
    tests: list[dict[str, Any]],
) -> dict[str, ModelTokenUsage]:
    """Aggregate per-test ``token_usage_by_model`` maps into one run-level map."""
    per_test_maps = [
        row.get("token_usage_by_model")
        for row in tests
        if isinstance(row.get("token_usage_by_model"), dict)
    ]
    return merge_token_usage_by_model(*per_test_maps)


def tag_model_roles(
    usage_by_model: dict[str, ModelTokenUsage],
    *,
    model_slots: dict[str, list[str]] | None,
) -> dict[str, ModelTokenUsage]:
    """Attach configured slot roles (main, fallback, review, …) to measured models."""
    if not model_slots:
        return usage_by_model

    roles_for_model: dict[str, set[str]] = {}
    for role, models in model_slots.items():
        for model in models:
            model_name = str(model or "").strip()
            if not model_name:
                continue
            roles_for_model.setdefault(model_name, set()).add(role)

    tagged: dict[str, ModelTokenUsage] = {}
    for model, usage in usage_by_model.items():
        entry = dict(usage)
        roles = set(entry.get("roles") or [])
        roles.update(roles_for_model.get(model, set()))
        if roles:
            entry["roles"] = sorted(roles)
        tagged[model] = entry
    return tagged


def extract_token_usage_by_model_from_history(history: Any) -> dict[str, ModelTokenUsage]:
    """Extract per-model totals from browser-use AgentHistoryList.usage.by_model."""
    if history is None:
        return {}

    usage = getattr(history, "usage", None)
    if usage is None:
        return {}

    payload = _usage_to_dict(usage)
    by_model = payload.get("by_model")
    if not isinstance(by_model, dict) or not by_model:
        return {}

    result: dict[str, ModelTokenUsage] = {}
    for model_key, stats in by_model.items():
        stats_dict = _usage_to_dict(stats)
        model = str(stats_dict.get("model") or model_key or "").strip() or "unknown"
        usage_fields: dict[str, Any] = {
            "prompt_tokens": stats_dict.get("prompt_tokens"),
            "completion_tokens": stats_dict.get("completion_tokens"),
            "total_tokens": stats_dict.get("total_tokens"),
            "llm_calls": stats_dict.get("invocations"),
        }
        cost = _coerce_float(stats_dict.get("cost"))
        if cost is not None and cost > 0:
            usage_fields["cost_usd"] = cost
        result[model] = normalize_model_token_usage(usage_fields)
    return result
