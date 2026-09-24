"""Display helpers for Gradio tables."""

from __future__ import annotations

import html

import pandas as pd

from src.formatting import fmt_number


def display_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame([{"—": "No data"}])
    out = df.copy().astype(object)
    return out.where(pd.notnull(out), "—")


def _cell_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if pd.isna(value):
        return "—"
    if isinstance(value, float):
        return fmt_number(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return str(value)


def dataframe_to_html(df: pd.DataFrame | None, *, empty_note: str = "No data") -> str:
    if df is None or df.empty:
        return f'<p class="wab-detail-note">{html.escape(empty_note)}</p>'

    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in df.columns)
    body_rows = []
    for row in df.itertuples(index=False, name=None):
        cells = []
        for col, value in zip(df.columns, row, strict=True):
            text = _cell_text(value)
            css_class = ""
            if col in {"Success %", "Success"} and text not in {"—", "✓", "✗"}:
                css_class = ' class="wab-metric-value"'
            elif col in {"Tasks", "Metric", "Harness", "Input", "Model", "Class", "Task"}:
                css_class = ' class="wab-mono-cell"'
            cells.append(f"<td{css_class}>{html.escape(text)}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    rows = "".join(body_rows)
    return (
        '<div class="wab-table-wrap wab-detail-table-wrap">'
        f'<table class="wab-table wab-detail-table"><thead><tr>{headers}</tr></thead>'
        f"<tbody>{rows}</tbody></table></div>"
    )
