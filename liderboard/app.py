"""WebPageBench leaderboard (Gradio Space source)."""

from __future__ import annotations

import os

# HF Spaces enable SSR by default. It is not needed for this app and triggers asyncio
# cleanup errors on Python 3.13 (Invalid file descriptor: -1). launch(ssr_mode=False)
# is ignored on HF — the env var must be set before Gradio is imported.
os.environ.setdefault("GRADIO_SSR_MODE", "false")

import html
import json
from pathlib import Path

import gradio as gr
import pandas as pd

from src.bench_config import load_bench_config, section_order, taxonomy_order
from src.load_entries import (
    FILTER_ALL,
    entry_by_id,
    entry_choices,
    filter_entries,
    harness_filter_choices,
    input_filter_choices,
    load_entries,
    load_raw_results,
)
from src.display import dataframe_to_html
from src.tables import (
    category_description_html,
    section_leaderboard_dataframe,
    taxonomy_leaderboard_dataframe,
)
from src.traces import build_trace_js_on_load, build_traces_shell, parse_trace_nav
from src.ui import build_board, build_highlight_picks, build_nav_js, build_shell_top, load_css
from src.formatting import round2


def _category_table(entries, kind: str, item_id: str):
    if kind == "section":
        desc, df = category_description_html("section", item_id), section_leaderboard_dataframe(entries, item_id)
    else:
        desc, df = category_description_html("taxonomy", item_id), taxonomy_leaderboard_dataframe(entries, item_id)
    return desc, dataframe_to_html(df)


def _metrics_html(entries) -> str:
    metric_rows = [
        {
            "Model": entry.model,
            "Harness": entry.harness,
            "Input": entry.input_modality,
            "Success %": entry.success_pct,
            "Tasks": f"{entry.passed_tasks}/{entry.total_tasks}",
            "Avg duration": round2(entry.avg_duration_seconds),
            "Total duration": round2(entry.total_duration_seconds),
            "Total steps": entry.total_agent_steps,
            "Avg steps": round2(entry.avg_agent_steps),
            "Tokens/task": round2(entry.avg_tokens_per_task),
            "Total tokens": entry.total_tokens,
            "Total $": round2(entry.total_cost_usd),
        }
        for entry in entries
    ]
    return dataframe_to_html(pd.DataFrame(metric_rows))


def _raw_tasks_dataframe(raw: dict | None) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    rows = []
    config = load_bench_config()
    section_labels = {section_id: meta["label"] for section_id, meta in config["sections"].items()}
    for test in raw.get("tests") or []:
        ui = test.get("ui_taxonomy") or {}
        domain = ui.get("domain") or "—"
        rows.append(
            {
                "Section": section_labels.get(domain, domain),
                "Task": test.get("test_name") or "—",
                "Success": "✓" if test.get("success") else "✗",
                "Duration": test.get("duration_seconds"),
                "Steps": test.get("agent_steps"),
            }
        )
    return pd.DataFrame(rows)


def _run_metrics_dataframe(entry, raw: dict | None) -> pd.DataFrame:
    run = (raw or {}).get("run") or {}
    rows = [
        {"Metric": "Success %", "Value": entry.success_pct},
        {"Metric": "Tasks passed", "Value": f"{entry.passed_tasks}/{entry.total_tasks}"},
        {"Metric": "Section avg %", "Value": round2(entry.section_avg_rate * 100) if entry.section_avg_rate is not None else None},
        {"Metric": "Harness", "Value": entry.harness},
        {"Metric": "Input", "Value": entry.input_modality},
        {"Metric": "Provider", "Value": entry.provider or run.get("provider")},
        {"Metric": "Mock", "Value": entry.mock or run.get("mock")},
        {"Metric": "Finished", "Value": entry.finished},
        {"Metric": "Submitted at", "Value": entry.submitted_at or run.get("finished_at") or run.get("started_at")},
        {"Metric": "Avg duration (s)", "Value": round2(entry.avg_duration_seconds or run.get("avg_duration_seconds"))},
        {"Metric": "Avg steps", "Value": round2(entry.avg_agent_steps or run.get("avg_agent_steps"))},
        {"Metric": "Tokens / task", "Value": round2(entry.avg_tokens_per_task or run.get("avg_tokens_per_task"))},
        {"Metric": "Total tokens", "Value": entry.total_tokens or run.get("total_tokens")},
        {"Metric": "Total $", "Value": round2(entry.total_cost_usd)},
        {"Metric": "Agent completion", "Value": round2(entry.agent_completion_rate)},
        {"Metric": "Agent/WebPageBench agreement", "Value": round2(entry.agent_dab_agreement_rate)},
        {"Metric": "Raw results", "Value": entry.raw_results_path},
    ]
    return pd.DataFrame(rows)


def _ui_taxonomy_dataframe(raw: dict | None) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    stats = raw.get("ui_taxonomy_stats") or {}
    by_primary = stats.get("by_primary") or {}
    rows = []
    for class_id, row in sorted(by_primary.items()):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "Class": class_id,
                "Success %": round(float(row["success_rate"]) * 100, 2) if isinstance(row.get("success_rate"), (int, float)) else None,
                "Passed": row.get("passed"),
                "Failed": row.get("failed"),
                "Total": row.get("total"),
            }
        )
    return pd.DataFrame(rows)


def _submission_summary(entry) -> str:
    section_note = ""
    if entry.section_avg_rate is not None and entry.success_rate is not None:
        section_pct = round(entry.section_avg_rate * 100, 2)
        success_pct = entry.success_pct
        if abs(section_pct - (success_pct or 0)) >= 0.5:
            section_note = (
                f'<p class="wab-submission-note">Section-average score: <strong>{section_pct}%</strong>. '
                f"Primary leaderboard metric is WebPageBench task pass rate: "
                f"<strong>{success_pct}%</strong> ({entry.passed_tasks}/{entry.total_tasks}).</p>"
            )

    badges = ", ".join(html.escape(badge) for badge in entry.ui_badges) if entry.ui_badges else "—"
    return (
        '<div class="wab-submission-summary">'
        f'<h3 class="wab-submission-title">{html.escape(entry.model)}</h3>'
        f'<p><strong>Harness:</strong> <span class="wab-inline-mono">{html.escape(entry.harness)}</span></p>'
        f'<p><strong>Input:</strong> <span class="wab-inline-mono">{html.escape(entry.input_modality)}</span></p>'
        f"<p><strong>Success:</strong> {entry.success_pct}% "
        f"({entry.passed_tasks}/{entry.total_tasks} tasks)</p>"
        f"<p><strong>UI badges:</strong> {badges}</p>"
        f"{section_note}"
        "</div>"
    )


def _submission_tables(entry_id: str, entries):
    entry = entry_by_id(entries, entry_id)
    if entry is None:
        empty = dataframe_to_html(pd.DataFrame())
        return "No submission selected.", empty, empty, empty

    summary = _submission_summary(entry)
    raw = load_raw_results(entry)
    if raw is None:
        return (
            summary
            + '<p class="wab-submission-note">Raw <span class="wab-inline-mono">results.json</span> not found. '
            "Run <span class=\"wab-inline-mono\">./scripts/export_leaderboard.sh</span> after eval.</p>",
            dataframe_to_html(_run_metrics_dataframe(entry, None)),
            dataframe_to_html(pd.DataFrame(), empty_note="Raw results not available."),
            dataframe_to_html(pd.DataFrame(), empty_note="Raw results not available."),
        )

    return (
        summary,
        dataframe_to_html(_run_metrics_dataframe(entry, raw)),
        dataframe_to_html(_raw_tasks_dataframe(raw)),
        dataframe_to_html(_ui_taxonomy_dataframe(raw)),
    )


def _raw_json_placeholder(entry_id: str, entries) -> str:
    entry = entry_by_id(entries, entry_id)
    if entry is None:
        return "{}"
    path = entry.raw_results_path or f"results/raw/{entry_id}/results.json"
    return (
        f"// Raw results for {entry.model} × {entry.harness}\n"
        f"// File: {path}\n"
        '// Click "Load full JSON" to fetch the exported results.json.'
    )


def _raw_json_full(entry_id: str, entries) -> str:
    entry = entry_by_id(entries, entry_id)
    if entry is None:
        return "{}"
    raw = load_raw_results(entry)
    if raw is None:
        return "{}"
    return json.dumps(raw, ensure_ascii=False, indent=2)


_DETAIL_TAB_IDS = ("submission", "sections", "taxonomy", "metrics", "about")


def _parse_nav_payload(payload: str) -> tuple[str, str]:
    tab, category = (payload.split(":", 1) + [""])[:2]
    return tab, category


def build_demo(entries=None):
    config = load_bench_config()
    entries = entries if entries is not None else load_entries()
    view_choices = [(f'{view["emoji"]} {view["label"]}', view["id"]) for view in config["views"]]
    submission_choices = entry_choices(entries)
    default_submission = submission_choices[0][1] if submission_choices else None
    section_choices = [(config["sections"][section_id]["label"], section_id) for section_id in section_order()]
    taxonomy_choices = [(config["ui_classes"][class_id]["label"], class_id) for class_id in taxonomy_order()]
    default_section = section_choices[0][1] if section_choices else None
    default_taxonomy = taxonomy_choices[0][1] if taxonomy_choices else None

    theme = gr.themes.Base(
        primary_hue=gr.themes.colors.orange,
        neutral_hue=gr.themes.colors.gray,
    ).set(
        body_background_fill="*neutral_950",
        body_background_fill_dark="*neutral_950",
        block_background_fill="*neutral_900",
        block_background_fill_dark="*neutral_900",
        block_border_color="*neutral_800",
        block_border_color_dark="*neutral_800",
        body_text_color="*neutral_50",
        body_text_color_dark="*neutral_50",
    )

    with gr.Blocks(title="WebPageBench Leaderboard", elem_classes=["wab-root"]) as demo:
        gr.HTML(build_shell_top(entries))
        gr.HTML(build_highlight_picks(entries), elem_classes=["wab-highlights-wrap"])
        view = gr.Radio(
            choices=view_choices,
            value="success",
            show_label=False,
            elem_classes=["wab-view-nav-radio"],
            container=False,
        )
        gr.HTML('<p class="wab-filter-kicker">Input</p>')
        input_filter = gr.Radio(
            choices=input_filter_choices(entries),
            value=FILTER_ALL,
            show_label=False,
            elem_classes=["wab-view-nav-radio", "wab-filter-radio"],
            container=False,
        )
        gr.HTML('<p class="wab-filter-kicker">Harness</p>')
        harness_filter = gr.Radio(
            choices=harness_filter_choices(entries),
            value=FILTER_ALL,
            show_label=False,
            elem_classes=["wab-view-nav-radio", "wab-filter-radio"],
            container=False,
        )
        board = gr.HTML(build_board(entries, "success"))

        def _visible(input_id: str, harness_id: str):
            by_input = filter_entries(entries, input_id=input_id, harness_id=FILTER_ALL)
            harness_opts = harness_filter_choices(by_input)
            valid_ids = {value for _, value in harness_opts}
            selected_harness = harness_id if harness_id in valid_ids else FILTER_ALL
            return filter_entries(entries, input_id=input_id, harness_id=selected_harness), harness_opts, selected_harness

        def on_view_change(view_id: str, input_id: str, harness_id: str):
            visible, _, _ = _visible(input_id, harness_id)
            return build_board(visible, view_id)

        def on_input_or_harness_change(view_id: str, input_id: str, harness_id: str, section_id: str, taxonomy_id: str):
            visible, harness_opts, selected_harness = _visible(input_id, harness_id)
            section_html = _category_table(visible, "section", section_id) if section_id else ("", "")
            taxonomy_html = _category_table(visible, "taxonomy", taxonomy_id) if taxonomy_id else ("", "")
            return (
                build_board(visible, view_id),
                gr.update(choices=harness_opts, value=selected_harness),
                section_html[0],
                section_html[1],
                taxonomy_html[0],
                taxonomy_html[1],
                _metrics_html(visible),
            )

        gr.HTML('<div id="wab-detail-anchor" class="wab-detail-anchor"></div>')

        with gr.Tabs(elem_id="wab-detail-tabs", elem_classes=["wab-tabs"]):
            with gr.Tab("Submission", elem_classes=["wab-tab-panel"]):
                gr.HTML(
                    '<p class="wab-detail-note">Inspect the full exported '
                    '<span class="wab-inline-mono">results.json</span> for a model × harness run.</p>'
                )
                submission = gr.Dropdown(
                    choices=submission_choices,
                    value=default_submission,
                    label="Submission",
                    interactive=True,
                    filterable=True,
                    elem_id="wab-submission-dropdown",
                    elem_classes=["wab-submission-dropdown"],
                )
                initial_detail = _submission_tables(default_submission, entries) if default_submission else (
                    "No submissions yet.",
                    dataframe_to_html(pd.DataFrame()),
                    dataframe_to_html(pd.DataFrame()),
                    dataframe_to_html(pd.DataFrame()),
                )
                detail_summary = gr.HTML(value=initial_detail[0], elem_classes=["wab-submission-summary-wrap"])
                with gr.Accordion("Run metrics", open=True, elem_classes=["wab-accordion"]):
                    detail_metrics = gr.HTML(value=initial_detail[1], elem_classes=["wab-detail-html"])
                with gr.Accordion("Tasks", open=False, elem_classes=["wab-accordion"]):
                    detail_tasks = gr.HTML(value=initial_detail[2], elem_classes=["wab-detail-html"])
                with gr.Accordion("UI taxonomy", open=False, elem_classes=["wab-accordion"]):
                    detail_ui = gr.HTML(value=initial_detail[3], elem_classes=["wab-detail-html"])
                with gr.Accordion("Raw JSON", open=False, elem_classes=["wab-accordion"]):
                    gr.Markdown(
                        '<p class="wab-detail-note">Large files load on demand so tables above stay responsive.</p>'
                    )
                    load_json_btn = gr.Button("Load full JSON", elem_classes=["wab-load-json-btn"])
                    detail_json = gr.Code(
                        value=_raw_json_placeholder(default_submission, entries) if default_submission else "{}",
                        language="json",
                        lines=20,
                        elem_classes=["wab-json"],
                    )

                def on_submission_change(entry_id: str):
                    return _submission_tables(entry_id, entries) + (_raw_json_placeholder(entry_id, entries),)

                submission.change(
                    on_submission_change,
                    inputs=[submission],
                    outputs=[detail_summary, detail_metrics, detail_tasks, detail_ui, detail_json],
                )

                def on_load_full_json(entry_id: str):
                    return _raw_json_full(entry_id, entries)

                load_json_btn.click(
                    on_load_full_json,
                    inputs=[submission],
                    outputs=[detail_json],
                )

            with gr.Tab("Sections", elem_classes=["wab-tab-panel"]):
                gr.HTML(
                    '<p class="wab-detail-note">Leaderboard по доменам бенчмарка. '
                    "Выберите категорию — описание появится под кнопками.</p>"
                )
                section_pick = gr.Radio(
                    choices=section_choices,
                    value=default_section,
                    show_label=False,
                    elem_id="wab-section-pick",
                    elem_classes=["wab-category-radio"],
                    container=False,
                )
                section_initial = _category_table(entries, "section", default_section) if default_section else ("", "")
                section_desc = gr.HTML(value=section_initial[0], elem_classes=["wab-category-desc-wrap"])
                section_table = gr.HTML(value=section_initial[1], elem_classes=["wab-detail-html"])

                def on_section_change(section_id: str, input_id: str, harness_id: str):
                    visible, _, _ = _visible(input_id, harness_id)
                    return _category_table(visible, "section", section_id)

                section_pick.change(
                    on_section_change,
                    inputs=[section_pick, input_filter, harness_filter],
                    outputs=[section_desc, section_table],
                )

            with gr.Tab("UI taxonomy", elem_classes=["wab-tab-panel"]):
                gr.HTML(
                    '<p class="wab-detail-note">Leaderboard по UI-классам (primary). '
                    "Выберите класс — описание появится под кнопками.</p>"
                )
                taxonomy_pick = gr.Radio(
                    choices=taxonomy_choices,
                    value=default_taxonomy,
                    show_label=False,
                    elem_id="wab-taxonomy-pick",
                    elem_classes=["wab-category-radio"],
                    container=False,
                )
                taxonomy_initial = _category_table(entries, "taxonomy", default_taxonomy) if default_taxonomy else ("", "")
                taxonomy_desc = gr.HTML(value=taxonomy_initial[0], elem_classes=["wab-category-desc-wrap"])
                taxonomy_table = gr.HTML(value=taxonomy_initial[1], elem_classes=["wab-detail-html"])

                def on_taxonomy_change(class_id: str, input_id: str, harness_id: str):
                    visible, _, _ = _visible(input_id, harness_id)
                    return _category_table(visible, "taxonomy", class_id)

                taxonomy_pick.change(
                    on_taxonomy_change,
                    inputs=[taxonomy_pick, input_filter, harness_filter],
                    outputs=[taxonomy_desc, taxonomy_table],
                )

            with gr.Tab("Metrics", elem_classes=["wab-tab-panel"]):
                metrics_table = gr.HTML(
                    value=_metrics_html(entries),
                    elem_classes=["wab-detail-html"],
                )

            with gr.Tab("Traces", elem_classes=["wab-tab-panel"]):
                default_entry = default_submission or (entries[0].entry_id if entries else "")

                def on_trace_nav(evt: gr.EventData):
                    payload = str(getattr(evt, "payload", "") or "")
                    view, entry_id, test_name = parse_trace_nav(payload)
                    if view == "list":
                        eid = entry_id or default_entry
                        return build_traces_shell(entries, view="list", entry_id=eid)
                    if view == "detail" and entry_id and test_name:
                        return build_traces_shell(
                            entries, view="detail", entry_id=entry_id, test_name=test_name
                        )
                    return build_traces_shell(entries, view="list", entry_id=default_entry)

                trace_content = gr.HTML(
                    value=build_traces_shell(entries, view="list", entry_id=default_entry),
                    elem_classes=["wab-traces-wrap"],
                    js_on_load=build_trace_js_on_load(),
                )
                trace_content.navigate(on_trace_nav, None, trace_content)

            with gr.Tab("About", elem_classes=["wab-tab-panel"]):
                gr.Markdown((Path(__file__).parent / "docs" / "description.md").read_text(encoding="utf-8"))

        nav_payload = gr.Textbox(
            value="",
            show_label=False,
            visible="hidden",
            elem_id="wab-nav-payload",
            elem_classes=["wab-nav-trigger-hidden"],
        )
        nav_btn = gr.Button(
            "Navigate",
            visible="hidden",
            elem_id="wab-nav-go",
            elem_classes=["wab-nav-trigger-hidden"],
        )

        def on_badge_nav(payload: str = "", input_id: str = FILTER_ALL, harness_id: str = FILTER_ALL):
            no_update = gr.update()
            if not payload:
                return (no_update,) * 6

            visible, _, _ = _visible(input_id, harness_id)
            tab, category = _parse_nav_payload(payload)
            section_pick_up = section_desc_up = section_table_up = no_update
            tax_pick_up = tax_desc_up = tax_table_up = no_update

            if tab == "sections" and category:
                section_pick_up = gr.update(value=category)
                desc, table = _category_table(visible, "section", category)
                section_desc_up = gr.update(value=desc)
                section_table_up = gr.update(value=table)
            elif tab == "taxonomy" and category:
                tax_pick_up = gr.update(value=category)
                desc, table = _category_table(visible, "taxonomy", category)
                tax_desc_up = gr.update(value=desc)
                tax_table_up = gr.update(value=table)

            return (
                section_pick_up,
                section_desc_up,
                section_table_up,
                tax_pick_up,
                tax_desc_up,
                tax_table_up,
            )

        filter_inputs = [view, input_filter, harness_filter, section_pick, taxonomy_pick]
        filter_outputs = [
            board,
            harness_filter,
            section_desc,
            section_table,
            taxonomy_desc,
            taxonomy_table,
            metrics_table,
        ]
        view.change(on_view_change, inputs=[view, input_filter, harness_filter], outputs=board)
        input_filter.change(on_input_or_harness_change, inputs=filter_inputs, outputs=filter_outputs)
        harness_filter.change(on_input_or_harness_change, inputs=filter_inputs, outputs=filter_outputs)

        nav_btn.click(
            on_badge_nav,
            inputs=[nav_payload, input_filter, harness_filter],
            outputs=[
                section_pick,
                section_desc,
                section_table,
                taxonomy_pick,
                taxonomy_desc,
                taxonomy_table,
            ],
            js=(
                "(payload, inputId, harnessId) => {"
                "const p = window.__wabPendingNav || payload || '';"
                "const tab = (p.split(':')[0] || 'submission');"
                "if (window.wabOpenDetailTab) window.wabOpenDetailTab(tab);"
                "document.getElementById('wab-detail-anchor')"
                "?.scrollIntoView({behavior:'smooth', block:'start'});"
                "return [p, inputId, harnessId];"
                "}"
            ),
        )

        demo.load(lambda: None, None, None, js=build_nav_js())

    return demo, theme, load_css()


demo, theme, css = build_demo()

if __name__ == "__main__":
    demo.launch(theme=theme, css=css, share=False, ssr_mode=False)
