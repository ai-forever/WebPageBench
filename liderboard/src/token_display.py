"""Token counts and per-model usage labels for the leaderboard."""

from __future__ import annotations

import html
from typing import Any

from src.formatting import fmt_cost
from src.models import LeaderboardEntry

_UNKNOWN_MODEL_KEYS = frozenset({"", "unknown", "unknown_model"})
_SINGLE_MODEL_HARNESSES = frozenset({"browser-use", "ouroboros-cut"})
_OUROBOROS_FULL_PREFIX = "ouroboros-full"
_OUROBOROS_AUX_ROLES = frozenset({"fallback", "review"})


def fmt_tokens(value: float | int | None) -> str:
    if value is None:
        return "—"
    amount = float(value)
    if amount <= 0:
        return "0"
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.2f}M"
    if amount >= 1_000:
        return f"{amount / 1_000:.2f}K"
    return f"{amount:.2f}"


def _usage_tokens(usage: dict[str, Any]) -> int:
    total = usage.get("total_tokens")
    if isinstance(total, (int, float)) and total > 0:
        return int(total)
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    return prompt + completion


def _display_model_name(model: str, primary_model: str) -> str:
    normalized = str(model or "").strip()
    if normalized.lower() in _UNKNOWN_MODEL_KEYS:
        return primary_model
    return normalized


def _role_label(model: str, primary_model: str, roles: list[str]) -> str:
    display = _display_model_name(model, primary_model)
    if display == primary_model and not roles:
        return "primary"
    if roles:
        return "/".join(roles)
    if display == primary_model:
        return "primary"
    return "aux"


def compact_token_usage_by_model(
    usage_by_model: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(usage_by_model, dict):
        return {}
    compact: dict[str, dict[str, Any]] = {}
    for model, usage in usage_by_model.items():
        if not isinstance(usage, dict):
            continue
        row: dict[str, Any] = {
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
            "llm_calls": int(usage.get("llm_calls") or 0),
        }
        cost = usage.get("cost_usd")
        if isinstance(cost, (int, float)) and cost > 0:
            row["cost_usd"] = float(cost)
        roles = usage.get("roles")
        if isinstance(roles, list) and roles:
            row["roles"] = [str(role) for role in roles]
        compact[str(model)] = row
    return compact


def token_usage_from_run(run: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(run, dict):
        return {}
    return compact_token_usage_by_model(run.get("token_usage_by_model"))


def sum_usage_by_model(
    usage_by_model: dict[str, dict[str, Any]] | None,
) -> tuple[int, float | None]:
    """Sum token and recorded cost counters across per-model buckets."""
    tokens = 0
    cost = 0.0
    has_cost = False
    for usage in (usage_by_model or {}).values():
        if not isinstance(usage, dict):
            continue
        tokens += _usage_tokens(usage)
        amount = usage.get("cost_usd")
        if isinstance(amount, (int, float)) and float(amount) > 0:
            cost += float(amount)
            has_cost = True
    return tokens, (cost if has_cost else None)


def entry_recorded_totals(entry: LeaderboardEntry) -> tuple[int | None, float | None]:
    """Return authoritative totals from per-model buckets, falling back to run totals."""
    tokens, cost = sum_usage_by_model(entry.token_usage_by_model)
    total_tokens = tokens if tokens > 0 else entry.total_tokens
    total_cost = cost if cost is not None and cost > 0 else entry.total_cost_usd
    return total_tokens, total_cost


def reconcile_entry_usage_totals(entry: LeaderboardEntry) -> None:
    """Keep run totals aligned with summed token_usage_by_model when recorded."""
    by_model = entry.token_usage_by_model or {}
    if not by_model:
        return
    tokens, cost = sum_usage_by_model(by_model)
    if tokens > 0:
        entry.total_tokens = tokens
    if cost is not None and cost > 0:
        entry.total_cost_usd = cost
        if entry.total_tasks:
            entry.avg_cost_per_task_usd = cost / entry.total_tasks


def _short_model_name(model: str) -> str:
    return model.split("/")[-1] if "/" in model else model


def _model_roles_index(model_slots: dict[str, list[str]]) -> dict[str, list[str]]:
    index: dict[str, set[str]] = {}
    for role, models in model_slots.items():
        for model in models:
            model_name = str(model or "").strip()
            if not model_name:
                continue
            index.setdefault(model_name, set()).add(str(role))
    return {model: sorted(roles) for model, roles in sorted(index.items())}


def _normalize_model_slots(slots: dict[str, Any] | None) -> dict[str, list[str]]:
    if not isinstance(slots, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for slot, models in slots.items():
        if not isinstance(models, list):
            continue
        cleaned = [str(model) for model in models if str(model or "").strip()]
        if cleaned:
            normalized[str(slot)] = cleaned
    return normalized


def _task_ouroboros_model_slots(test: dict[str, Any]) -> dict[str, list[str]]:
    agent = test.get("agent") or {}
    meta = agent.get("harness_metadata") or {}
    sync = meta.get("ouroboros_llm_sync") or {}
    return _normalize_model_slots(sync.get("model_slots"))


def _has_per_model_token_split(entry: LeaderboardEntry) -> bool:
    by_model = entry.token_usage_by_model or {}
    if not by_model:
        return False

    primary = entry.model
    display_models: set[str] = set()
    for model, usage in by_model.items():
        if not isinstance(usage, dict):
            continue
        display_models.add(_display_model_name(str(model), primary))
        roles = [str(role) for role in (usage.get("roles") or [])]
        if _role_label(str(model), primary, roles) != "primary":
            return True
    return len(display_models) > 1


def _has_ouroboros_slot_split(entry: LeaderboardEntry) -> bool:
    if not entry.harness.startswith(_OUROBOROS_FULL_PREFIX):
        return False
    return bool(entry.ouroboros_model_slots)


def has_model_usage_split(entry: LeaderboardEntry) -> bool:
    """True when per-model breakdown adds info beyond the run's primary LLM."""
    if entry.harness in _SINGLE_MODEL_HARNESSES:
        return False
    if _has_per_model_token_split(entry):
        return True
    return _has_ouroboros_slot_split(entry)


def _compact_slot_label(model: str, roles: list[str], *, primary: str) -> str:
    short = _short_model_name(model)
    aux_roles = [role for role in roles if role in _OUROBOROS_AUX_ROLES]
    if aux_roles:
        return f"{short} ({'/'.join(aux_roles)})"
    if model == primary:
        return f"{short} (main)"
    return short


def _ouroboros_slot_display_lines(entry: LeaderboardEntry) -> list[str]:
    index = _model_roles_index(entry.ouroboros_model_slots)
    if not index:
        return []

    total_tokens, total_cost = entry_recorded_totals(entry)
    total_bits: list[str] = []
    if total_tokens:
        total_bits.append(fmt_tokens(total_tokens))
    if total_cost:
        total_bits.append(fmt_cost(total_cost))
    total_line = " · ".join(total_bits)

    if len(index) == 1:
        short = _short_model_name(next(iter(index)))
        if total_line:
            return [f"{short} {total_line}"]
        return [short]

    primary = entry.model
    lines = [
        _compact_slot_label(model, index[model], primary=primary)
        for model in sorted(index, key=lambda name: (name != primary, name))
    ]
    if total_line:
        lines.append(f"{total_line} total")
    return lines


def _format_token_usage_breakdown(entry: LeaderboardEntry) -> str:
    by_model = entry.token_usage_by_model or {}
    primary = entry.model
    rows: list[tuple[str, str, str, str]] = []
    for model, usage in sorted(by_model.items()):
        if not isinstance(usage, dict):
            continue
        display = _display_model_name(str(model), primary)
        short = _short_model_name(display)
        role = _role_label(str(model), primary, list(usage.get("roles") or []))
        tokens = fmt_tokens(_usage_tokens(usage))
        cost = usage.get("cost_usd")
        cost_s = fmt_cost(float(cost)) if isinstance(cost, (int, float)) and cost > 0 else ""
        rows.append((short, role, tokens, cost_s))

    if not rows:
        return "—"

    if len(rows) == 1 and rows[0][1] == "primary":
        short, _, tokens, cost_s = rows[0]
        extra = f" · {cost_s}" if cost_s and cost_s != "—" else ""
        return f"{short} {tokens}{extra}"

    parts: list[str] = []
    for short, role, tokens, cost_s in rows:
        label = "primary" if role == "primary" else role
        bit = f"{short} {tokens} ({label})"
        if cost_s and cost_s != "—":
            bit += f" {cost_s}"
        parts.append(bit)
    return " · ".join(parts)


def _format_ouroboros_slots_breakdown(entry: LeaderboardEntry) -> str:
    lines = _ouroboros_slot_display_lines(entry)
    if not lines:
        return "—"
    return " · ".join(lines)


def format_model_usage_breakdown(entry: LeaderboardEntry) -> str:
    if not has_model_usage_split(entry):
        return "—"
    if _has_per_model_token_split(entry):
        return _format_token_usage_breakdown(entry)
    return _format_ouroboros_slots_breakdown(entry)


def format_model_usage_breakdown_html(entry: LeaderboardEntry) -> str:
    if not has_model_usage_split(entry):
        return "—"
    if _has_per_model_token_split(entry):
        text = _format_token_usage_breakdown(entry)
        return f'<span class="wab-token-split" title="{html.escape(text)}">{html.escape(text)}</span>'

    lines = _ouroboros_slot_display_lines(entry)
    if not lines:
        return "—"
    title = " · ".join(lines)
    body_parts: list[str] = []
    for line in lines:
        css_class = "wab-token-split-total" if line.endswith(" total") else "wab-token-split-line"
        body_parts.append(f'<span class="{css_class}">{html.escape(line)}</span>')
    body = "".join(body_parts)
    return f'<span class="wab-token-split" title="{html.escape(title)}">{body}</span>'


def format_task_token_usage(
    test: dict[str, Any],
    *,
    primary_model: str,
    ouroboros_model_slots: dict[str, list[str]] | None = None,
) -> str:
    harness = str(test.get("agent_harness") or "")
    if harness in _SINGLE_MODEL_HARNESSES:
        return "—"

    slots = _task_ouroboros_model_slots(test) or _normalize_model_slots(ouroboros_model_slots)
    by_model = test.get("token_usage_by_model")
    if isinstance(by_model, dict) and by_model:
        entry = LeaderboardEntry(
            model=primary_model,
            harness=harness,
            token_usage_by_model=compact_token_usage_by_model(by_model),
            ouroboros_model_slots=slots,
        )
        if _has_per_model_token_split(entry):
            return _format_token_usage_breakdown(entry)

    if harness.startswith(_OUROBOROS_FULL_PREFIX) and slots:
        entry = LeaderboardEntry(
            model=primary_model,
            harness=harness,
            token_usage_by_model=compact_token_usage_by_model(by_model if isinstance(by_model, dict) else None),
            ouroboros_model_slots=slots,
        )
        if _has_ouroboros_slot_split(entry):
            return _format_ouroboros_slots_breakdown(entry)

    usage = test.get("token_usage")
    if isinstance(usage, dict):
        return fmt_tokens(_usage_tokens(usage))
    return "—"
