"""Category leaderboard tables and helpers."""

from __future__ import annotations

import html

import pandas as pd

from src.bench_config import (
    load_bench_config,
    section_description,
    section_label,
    section_order,
    taxonomy_description,
    taxonomy_label,
    taxonomy_order,
)
from src.input_modality import harness_input
from src.models import LeaderboardEntry


def section_leaderboard_dataframe(entries: list[LeaderboardEntry], section_id: str) -> pd.DataFrame:
    rows = []
    for entry in entries:
        stats = entry.sections.get(section_id)
        rate = stats.success_rate if stats else None
        rows.append(
            {
                "Model": entry.model,
                "Harness": entry.harness,
                "Input": harness_input(entry.model, entry.harness),
                "Tasks": f"{stats.passed}/{stats.total}" if stats else None,
                "Success %": round(rate * 100, 2) if rate is not None else None,
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Success %", ascending=False, na_position="last")


def taxonomy_leaderboard_dataframe(entries: list[LeaderboardEntry], class_id: str) -> pd.DataFrame:
    rows = []
    for entry in entries:
        row = entry.ui_classes.get(class_id) or {}
        rate = row.get("success_rate")
        passed = row.get("passed")
        total = row.get("total")
        rows.append(
            {
                "Model": entry.model,
                "Harness": entry.harness,
                "Input": harness_input(entry.model, entry.harness),
                "Tasks": f"{passed}/{total}" if passed is not None and total is not None else None,
                "Success %": round(float(rate) * 100, 2) if isinstance(rate, (int, float)) else None,
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Success %", ascending=False, na_position="last")


def category_legend_html(kind: str) -> str:
    config = load_bench_config()
    if kind == "section":
        items = [
            (section_label(section_id), section_description(section_id))
            for section_id in section_order()
        ]
    else:
        items = [
            (taxonomy_label(class_id), taxonomy_description(class_id))
            for class_id in taxonomy_order()
        ]
    spans = "".join(
        f'<span class="wab-legend-item" title="{html.escape(desc)}">{html.escape(label)}</span>'
        for label, desc in items
    )
    return f'<div class="wab-category-legend">{spans}</div>'


def category_description_html(kind: str, item_id: str) -> str:
    if kind == "section":
        desc = section_description(item_id)
        label = section_label(item_id)
    else:
        desc = taxonomy_description(item_id)
        label = taxonomy_label(item_id)
    body = f"<strong>{html.escape(label)}</strong>"
    if desc:
        body += f" — {html.escape(desc)}"
    return f'<p class="wab-category-desc">{body}</p>'


def category_description(kind: str, item_id: str) -> str:
    if kind == "section":
        desc = section_description(item_id)
        label = section_label(item_id)
    else:
        desc = taxonomy_description(item_id)
        label = taxonomy_label(item_id)
    if not desc:
        return f"**{label}**"
    return f"**{label}** — {desc}"
