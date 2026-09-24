"""Shared numeric formatting for leaderboard UI."""

from __future__ import annotations


def round2(value: float | int | None) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    return round(float(value), 2)


def fmt_number(value: float | int | None, *, prefix: str = "", suffix: str = "") -> str:
    """Format a number with 2 decimals, but keep extra precision for small non-zero values."""
    if value is None or isinstance(value, bool):
        return "—"
    amount = float(value)
    if amount == 0:
        return f"{prefix}0.00{suffix}"
    absolute = abs(amount)
    if absolute >= 0.01:
        return f"{prefix}{amount:.2f}{suffix}"
    if absolute >= 1e-8:
        text = f"{amount:.8f}".rstrip("0").rstrip(".")
        return f"{prefix}{text}{suffix}"
    return f"{prefix}{amount:.2g}{suffix}"


def fmt_cost(value: float | None) -> str:
    if value is None:
        return "—"
    if value <= 0:
        return "FREE"
    return fmt_number(value, prefix="$")


def fmt_pct_value(value: float | None) -> str:
    if value is None:
        return "—"
    if value <= 1:
        return fmt_number(value * 100, suffix="%")
    return fmt_number(value, suffix="%")


def fmt_steps(value: float | int | None) -> str:
    if value is None or isinstance(value, bool):
        return "—"
    return str(int(round(float(value))))


def fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return fmt_number(seconds, suffix="s")
    if seconds < 3600:
        return fmt_number(seconds / 60, suffix="m")
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if minutes:
        return f"{hours}h {minutes}m"
    return f"{hours}h"
