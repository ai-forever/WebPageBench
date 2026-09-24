"""Console progress helpers for eval scoring runs."""

from __future__ import annotations

from typing import Any


def format_progress_start(current: int, total: int | None, test_name: str) -> str:
    total_label = str(total) if total else "?"
    return f"[{current:>{len(total_label)}}/{total_label}] ▶ {test_name}"


def format_progress_result(
    current: int,
    total: int | None,
    row: dict[str, Any],
    *,
    running_success_rate: float,
) -> str:
    total_label = str(total) if total else "?"
    test_name = row.get("test_name") or "unknown"
    success = row.get("success")
    status = "PASS" if success else "FAIL"

    duration = row.get("duration_seconds")
    duration_text = f"{float(duration):.1f}s" if isinstance(duration, (int, float)) else "—"

    steps = row.get("agent_steps")
    steps_text = str(steps) if steps is not None else "—"

    token_usage = row.get("token_usage") or {}
    tokens = row.get("tokens", token_usage.get("total_tokens"))
    tokens_text = str(tokens) if isinstance(tokens, int) else "—"

    dab = row.get("dab_check") or {}
    dab_text = f"{dab.get('passed', 0)}/{dab.get('total', 0)}"

    parts = [
        f"[{current:>{len(total_label)}}/{total_label}]",
        status,
        test_name,
        f"time={duration_text}",
        f"steps={steps_text}",
        f"tokens={tokens_text}",
        f"WebPageBench={dab_text}",
        f"success={running_success_rate:.0%}",
    ]

    if row.get("agent_error"):
        parts.append(f"error={row['agent_error']}")

    return " | ".join(parts)
