"""Tests for shared leaderboard number formatting."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LIDERBOARD_ROOT = _REPO_ROOT / "liderboard"
if str(_LIDERBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIDERBOARD_ROOT))

from src.formatting import (  # noqa: E402
    fmt_cost,
    fmt_duration,
    fmt_number,
    fmt_pct_value,
    fmt_steps,
    round2,
)


def test_fmt_number_regular_values():
    assert fmt_number(None) == "—"
    assert fmt_number(0) == "0.00"
    assert fmt_number(1.234) == "1.23"
    assert fmt_number(0.01) == "0.01"
    assert fmt_number(12.5) == "12.50"


def test_fmt_number_small_nonzero_values():
    assert fmt_number(0.0064) == "0.0064"
    assert fmt_number(0.004) == "0.004"
    assert fmt_number(0.0099) == "0.0099"
    assert fmt_number(0.00012) == "0.00012"


def test_fmt_cost():
    assert fmt_cost(None) == "—"
    assert fmt_cost(0) == "FREE"
    assert fmt_cost(-0.5) == "FREE"
    assert fmt_cost(0.42) == "$0.42"
    assert fmt_cost(0.0064) == "$0.0064"
    assert fmt_cost(0.004) == "$0.004"


def test_fmt_pct_value():
    assert fmt_pct_value(None) == "—"
    assert fmt_pct_value(0.5) == "50.00%"
    assert fmt_pct_value(0.0064) == "0.64%"
    assert fmt_pct_value(0.0001) == "0.01%"


def test_fmt_steps():
    assert fmt_steps(None) == "—"
    assert fmt_steps(1159) == "1159"
    assert fmt_steps(22.7) == "23"


def test_fmt_duration():
    assert fmt_duration(None) == "—"
    assert fmt_duration(45.2) == "45.20s"
    assert fmt_duration(0.0064) == "0.0064s"
    assert fmt_duration(120) == "2.00m"
    assert fmt_duration(8925) == "2h 28m"
    assert fmt_duration(3600) == "1h"


def test_round2():
    assert round2(None) is None
    assert round2(1.234) == 1.23
    assert round2(0.0064) == 0.01
