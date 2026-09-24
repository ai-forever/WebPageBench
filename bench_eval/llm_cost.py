"""Estimate LLM API cost from eval results.json token usage."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bench_eval.token_usage import normalize_model_token_usage, normalize_token_usage

DEFAULT_PRICING_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/"
    "model_prices_and_context_window.json"
)
CACHE_DIR_NAME = "dab_eval/model_pricing"
CACHE_DURATION_SECONDS = 24 * 60 * 60

_COST_KEYS = (
    "total_cost",
    "total_cost_usd",
    "cost",
    "cost_usd",
)

_UNKNOWN_MODEL_KEYS = frozenset({"", "unknown", "unknown_model"})


def _pricing_model_name(model: str, *, primary_model: str) -> str:
    """Map placeholder usage buckets (common in Ouroboros) to the run's primary model."""
    normalized = str(model or "").strip()
    if normalized.lower() in _UNKNOWN_MODEL_KEYS:
        return str(primary_model or "").strip() or normalized or "unknown"
    return normalized


@dataclass(frozen=True)
class ModelPricing:
    input_cost_per_token: float
    output_cost_per_token: float
    pricing_key: str | None = None


@dataclass(frozen=True)
class ModelCostBreakdown:
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_cost_usd: float | None
    priced: bool
    pricing_key: str | None = None
    source: str = "computed"
    roles: tuple[str, ...] = ()
    llm_calls: int = 0


@dataclass(frozen=True)
class CostBreakdown:
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_cost_usd: float | None
    avg_cost_per_task_usd: float | None
    tasks_with_cost: int
    priced: bool
    pricing_key: str | None = None
    source: str = "computed"
    by_model: tuple[ModelCostBreakdown, ...] = ()
    auxiliary_cost_usd: float | None = None


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _extract_recorded_cost(payload: dict[str, Any] | None) -> float | None:
    """Return a strictly positive recorded cost, if present."""
    if not payload:
        return None
    for key in _COST_KEYS:
        cost = _coerce_float(payload.get(key))
        if cost is not None and cost > 0:
            return cost
    return None


def _cache_dir() -> Path:
    explicit = os.getenv("DAB_MODEL_PRICING_CACHE_DIR")
    if explicit:
        return Path(explicit)
    xdg = os.getenv("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / CACHE_DIR_NAME
    return Path.home() / ".cache" / CACHE_DIR_NAME


def _pricing_url() -> str:
    return os.getenv("DAB_MODEL_PRICING_URL", DEFAULT_PRICING_URL)


def _load_overrides() -> dict[str, dict[str, Any]]:
    path = os.getenv("DAB_MODEL_PRICING_OVERRIDES")
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.is_file():
        return {}
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _fetch_pricing_data(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "dab-eval/llm-cost"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_cache_file(cache_file: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    timestamp = payload.get("timestamp")
    source_url = payload.get("source_url")
    data = payload.get("data")
    if not isinstance(timestamp, (int, float)) or not isinstance(data, dict):
        return None
    if source_url != _pricing_url():
        return None
    if time.time() - float(timestamp) >= CACHE_DURATION_SECONDS:
        return None
    return data


def _write_cache_file(cache_file: Path, data: dict[str, Any]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": time.time(),
        "source_url": _pricing_url(),
        "data": data,
    }
    cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_pricing_table(*, refresh: bool = False) -> dict[str, Any]:
    """Load LiteLLM pricing table with local cache and optional overrides."""
    overrides = _load_overrides()
    if refresh:
        data: dict[str, Any] = {}
    else:
        cache_file = _cache_dir() / "pricing.json"
        data = _read_cache_file(cache_file) or {}

    if not data:
        try:
            data = _fetch_pricing_data(_pricing_url())
            _write_cache_file(_cache_dir() / "pricing.json", data)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            data = {}

    merged = dict(data)
    merged.update(overrides)
    return merged


def _pricing_candidates(model: str) -> list[str]:
    normalized = model.strip()
    if not normalized:
        return []

    short_name = normalized.split("/")[-1]
    provider, _, tail = normalized.partition("/")
    candidates = [
        normalized,
        normalized.lower(),
        short_name,
        short_name.lower(),
        f"openrouter/{normalized}",
        f"openrouter/{short_name}",
    ]
    if provider and tail:
        candidates.extend(
            [
                f"{provider}/{tail.lower()}",
                tail,
                tail.lower(),
            ]
        )
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            deduped.append(candidate)
    return deduped


def resolve_model_pricing(
    model: str,
    pricing_table: dict[str, Any] | None = None,
) -> ModelPricing | None:
    """Resolve per-token pricing for a model name."""
    table = pricing_table if pricing_table is not None else load_pricing_table()
    for candidate in _pricing_candidates(model):
        row = table.get(candidate)
        if not isinstance(row, dict):
            continue
        input_cost = _coerce_float(row.get("input_cost_per_token"))
        output_cost = _coerce_float(row.get("output_cost_per_token"))
        if input_cost is None and output_cost is None:
            continue
        return ModelPricing(
            input_cost_per_token=max(input_cost or 0.0, 0.0),
            output_cost_per_token=max(output_cost or 0.0, 0.0),
            pricing_key=candidate,
        )
    return None


def compute_token_cost_usd(
    *,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int | None = None,
    pricing_table: dict[str, Any] | None = None,
) -> tuple[float | None, str | None]:
    pricing = resolve_model_pricing(model, pricing_table)
    if pricing is None:
        return None, None

    prompt = max(prompt_tokens, 0)
    completion = max(completion_tokens, 0)
    if prompt == 0 and completion == 0:
        tokens = max(total_tokens or 0, 0)
        if tokens <= 0:
            return None, None
        # No prompt/completion split: estimate with input rate.
        total = tokens * pricing.input_cost_per_token
        return (total, pricing.pricing_key) if total > 0 else (None, None)

    total = (
        prompt * pricing.input_cost_per_token
        + completion * pricing.output_cost_per_token
    )
    return (total, pricing.pricing_key) if total > 0 else (None, None)


def _usage_cost_from_tokens(
    *,
    model: str,
    usage: dict[str, Any],
    pricing_table: dict[str, Any] | None,
    pricing_model: str | None = None,
) -> tuple[float | None, str | None, str]:
    recorded = _extract_recorded_cost(usage)
    if recorded is not None:
        return recorded, None, "recorded"

    normalized = normalize_token_usage(usage)
    cost, pricing_key = compute_token_cost_usd(
        model=pricing_model or model,
        prompt_tokens=normalized["prompt_tokens"],
        completion_tokens=normalized["completion_tokens"],
        total_tokens=normalized["total_tokens"],
        pricing_table=pricing_table,
    )
    return cost, pricing_key, "computed"


def _model_usage_cost(
    *,
    model: str,
    usage: dict[str, Any],
    pricing_table: dict[str, Any] | None,
    primary_model: str | None = None,
) -> ModelCostBreakdown:
    normalized = normalize_model_token_usage(usage)
    pricing_model = _pricing_model_name(model, primary_model=primary_model or model)
    cost, pricing_key, source = _usage_cost_from_tokens(
        model=model,
        usage=usage,
        pricing_table=pricing_table,
        pricing_model=pricing_model,
    )
    roles = tuple(normalized.get("roles") or ())
    return ModelCostBreakdown(
        model=model,
        prompt_tokens=int(normalized.get("prompt_tokens") or 0),
        completion_tokens=int(normalized.get("completion_tokens") or 0),
        total_cost_usd=cost,
        priced=cost is not None and cost > 0,
        pricing_key=pricing_key,
        source=source,
        roles=roles,
        llm_calls=int(normalized.get("llm_calls") or 0),
    )


def _aggregate_tests_token_usage_by_model(tests: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    per_model: dict[str, dict[str, Any]] = {}
    for row in tests:
        usage_map = row.get("token_usage_by_model")
        if not isinstance(usage_map, dict):
            continue
        for model, usage in usage_map.items():
            model_name = str(model or "").strip() or "unknown"
            bucket = per_model.setdefault(
                model_name,
                {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "llm_calls": 0,
                    "roles": set(),
                },
            )
            normalized = normalize_model_token_usage(usage if isinstance(usage, dict) else None)
            bucket["prompt_tokens"] += int(normalized.get("prompt_tokens") or 0)
            bucket["completion_tokens"] += int(normalized.get("completion_tokens") or 0)
            bucket["total_tokens"] += int(normalized.get("total_tokens") or 0)
            bucket["llm_calls"] += int(normalized.get("llm_calls") or 0)
            recorded_cost = normalized.get("cost_usd")
            if isinstance(recorded_cost, (int, float)) and recorded_cost > 0:
                bucket["cost_usd"] = float(bucket.get("cost_usd") or 0.0) + float(recorded_cost)
            for role in normalized.get("roles") or []:
                bucket["roles"].add(str(role))
    for bucket in per_model.values():
        roles = bucket.pop("roles", set())
        if roles:
            bucket["roles"] = sorted(roles)
    return per_model


def _compute_multi_model_cost(
    *,
    primary_model: str,
    usage_by_model: dict[str, dict[str, Any]],
    pricing_table: dict[str, Any] | None,
    total_tasks: int,
) -> CostBreakdown:
    table = pricing_table if pricing_table is not None else load_pricing_table()
    model_breakdowns: list[ModelCostBreakdown] = []
    total_cost = 0.0
    priced = False
    sources: set[str] = set()
    pricing_key: str | None = None
    prompt_tokens = 0
    completion_tokens = 0

    for model in sorted(usage_by_model):
        usage = usage_by_model[model]
        breakdown = _model_usage_cost(
            model=model,
            usage=usage,
            pricing_table=table,
            primary_model=primary_model,
        )
        model_breakdowns.append(breakdown)
        prompt_tokens += breakdown.prompt_tokens
        completion_tokens += breakdown.completion_tokens
        if breakdown.total_cost_usd is not None and breakdown.total_cost_usd > 0:
            total_cost += breakdown.total_cost_usd
            priced = True
            sources.add(breakdown.source)
            if breakdown.pricing_key and pricing_key is None:
                pricing_key = breakdown.pricing_key

    auxiliary_cost = 0.0
    has_auxiliary = False
    for breakdown in model_breakdowns:
        if breakdown.model == primary_model:
            continue
        if breakdown.total_cost_usd is None or breakdown.total_cost_usd <= 0:
            continue
        auxiliary_cost += breakdown.total_cost_usd
        has_auxiliary = True

    avg = (total_cost / total_tasks) if total_tasks and priced else None
    return CostBreakdown(
        model=primary_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_cost_usd=total_cost if priced else None,
        avg_cost_per_task_usd=avg,
        tasks_with_cost=total_tasks if priced else 0,
        priced=priced,
        pricing_key=pricing_key,
        source="mixed" if len(sources) > 1 else (next(iter(sources)) if sources else "computed"),
        by_model=tuple(model_breakdowns),
        auxiliary_cost_usd=auxiliary_cost if has_auxiliary else None,
    )


def compute_results_cost(
    payload: dict[str, Any],
    *,
    pricing_table: dict[str, Any] | None = None,
) -> CostBreakdown:
    """Estimate total and per-task cost for one results.json payload."""
    run = payload.get("run") or {}
    tests = payload.get("tests") or []
    model = str(run.get("model") or "unknown")
    total_tasks = int(run.get("total_tasks") or len(tests) or 0)

    table = pricing_table if pricing_table is not None else load_pricing_table()

    run_usage_by_model = run.get("token_usage_by_model")
    if isinstance(run_usage_by_model, dict) and run_usage_by_model:
        return _compute_multi_model_cost(
            primary_model=model,
            usage_by_model=run_usage_by_model,
            pricing_table=table,
            total_tasks=total_tasks,
        )

    tests_usage_by_model = _aggregate_tests_token_usage_by_model(tests)
    if tests_usage_by_model:
        return _compute_multi_model_cost(
            primary_model=model,
            usage_by_model=tests_usage_by_model,
            pricing_table=table,
            total_tasks=total_tasks,
        )

    run_recorded = _extract_recorded_cost(run)
    if run_recorded is not None:
        total_tasks = int(run.get("total_tasks") or len(tests) or 0)
        avg = (run_recorded / total_tasks) if total_tasks else None
        return CostBreakdown(
            model=model,
            prompt_tokens=int(run.get("prompt_tokens") or 0),
            completion_tokens=int(run.get("completion_tokens") or 0),
            total_cost_usd=run_recorded,
            avg_cost_per_task_usd=avg,
            tasks_with_cost=total_tasks,
            priced=True,
            source="recorded",
        )

    total_cost = 0.0
    tasks_with_cost = 0
    pricing_key: str | None = None
    priced = False
    sources: set[str] = set()

    for row in tests:
        usage = row.get("token_usage") or {}
        cost, key, source = _usage_cost_from_tokens(
            model=model,
            usage=usage,
            pricing_table=table,
        )
        if cost is None or cost <= 0:
            continue
        total_cost += cost
        tasks_with_cost += 1
        priced = True
        sources.add(source)
        if key and pricing_key is None:
            pricing_key = key

    if tasks_with_cost:
        total_tasks = int(run.get("total_tasks") or len(tests) or tasks_with_cost)
        return CostBreakdown(
            model=model,
            prompt_tokens=int(run.get("prompt_tokens") or 0),
            completion_tokens=int(run.get("completion_tokens") or 0),
            total_cost_usd=total_cost,
            avg_cost_per_task_usd=(total_cost / total_tasks) if total_tasks else None,
            tasks_with_cost=tasks_with_cost,
            priced=priced,
            pricing_key=pricing_key,
            source="mixed" if len(sources) > 1 else next(iter(sources)),
        )

    prompt_tokens = int(run.get("prompt_tokens") or 0)
    completion_tokens = int(run.get("completion_tokens") or 0)
    total_tokens = int(run.get("total_tokens") or 0)
    total_cost, pricing_key = compute_token_cost_usd(
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        pricing_table=table,
    )
    total_tasks = int(run.get("total_tasks") or len(tests) or 0)
    return CostBreakdown(
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_cost_usd=total_cost,
        avg_cost_per_task_usd=(total_cost / total_tasks) if total_cost is not None and total_tasks else None,
        tasks_with_cost=0,
        priced=total_cost is not None and total_cost > 0,
        pricing_key=pricing_key,
        source="computed",
    )


def format_usd(value: float | int | None) -> str:
    if value is None:
        return "—"
    amount = float(value)
    if amount <= 0:
        return "—"
    return f"${amount:.4f}"
