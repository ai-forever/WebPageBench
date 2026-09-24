"""Agent trajectory list and detail views for the leaderboard."""

from __future__ import annotations

import html
import json
import re
from typing import Any

from src.bench_config import load_bench_config, section_label
from src.load_entries import entry_by_id, entry_label, load_raw_results
from src.models import LeaderboardEntry
from src.token_display import format_task_token_usage
from src.ui import fmt_cost


def parse_trace_nav(payload: str) -> tuple[str, str, str]:
    """Parse traces:<view>:<entry_id>[:<test_name>] payloads."""
    parts = (payload or "").split(":", 3)
    if len(parts) < 2 or parts[0] != "traces":
        return "list", "", ""
    view = parts[1] if len(parts) > 1 else "list"
    entry_id = parts[2] if len(parts) > 2 else ""
    test_name = parts[3] if len(parts) > 3 else ""
    return view, entry_id, test_name


def _esc(value: object) -> str:
    return html.escape(str(value if value is not None else "—"))


def _truncate(text: str, limit: int = 600) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _task_section_id(test_name: str) -> str | None:
    config = load_bench_config()
    for section_id, meta in config.get("sections", {}).items():
        if test_name in (meta.get("tasks") or []):
            return section_id
    return None


def _task_section_label(test_name: str) -> str:
    section_id = _task_section_id(test_name)
    if section_id:
        return section_label(section_id)
    return "—"


def format_duration(seconds: float | int | None) -> str:
    if seconds is None:
        return "—"
    try:
        total = float(seconds)
    except (TypeError, ValueError):
        return "—"
    if total < 60:
        return f"{total:.2f}s"
    minutes = int(total // 60)
    secs = int(total % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m"


def _extract_url_from_state(state: object) -> str | None:
    if not isinstance(state, str):
        return None
    match = re.search(r"url='([^']+)'", state)
    return match.group(1) if match else None


def _format_browser_action(model_output: dict[str, Any] | None) -> str:
    if not model_output:
        return "—"
    actions = model_output.get("action")
    if not isinstance(actions, list) or not actions:
        return "—"
    parts: list[str] = []
    for item in actions:
        if not isinstance(item, dict):
            continue
        for name, payload in item.items():
            if isinstance(payload, dict):
                brief = ", ".join(f"{k}={v}" for k, v in list(payload.items())[:4])
                parts.append(f"{name}({brief})")
            else:
                parts.append(f"{name}({payload})")
    return "; ".join(parts) if parts else "—"


def _normalize_agent_step(step: dict[str, Any], harness: str) -> dict[str, str]:
    harness = (harness or "").lower()
    title = "Step"
    body_parts: list[str] = []
    action = "—"
    url = ""

    if "model_output" in step:
        model_output = step.get("model_output") or {}
        title = f"Step {step.get('step', step.get('metadata', {}).get('step_number', '?'))}"
        action = _format_browser_action(model_output)
        thinking = model_output.get("thinking") or model_output.get("next_goal")
        if thinking:
            body_parts.append(str(thinking))
        results = step.get("result")
        if isinstance(results, list):
            for row in results[:2]:
                if isinstance(row, dict) and row.get("extracted_content"):
                    body_parts.append(str(row["extracted_content"]))
        url = _extract_url_from_state(step.get("state")) or ""
        if not body_parts and step.get("state_message"):
            body_parts.append(_truncate(str(step["state_message"]), 400))
    elif step.get("kind") == "message":
        title = f"Message ({step.get('source', 'agent')})"
        body_parts.append(str(step.get("content") or ""))
    elif step.get("kind") == "action":
        title = f"Action {step.get('index', '?')}"
        tool = step.get("tool") or step.get("action", {}).get("kind")
        action = str(tool or "action")
        payload = step.get("action")
        if isinstance(payload, dict):
            body_parts.append(_truncate(json.dumps(payload, ensure_ascii=False), 500))
    else:
        title = f"Step {step.get('index', step.get('step', '?'))}"
        body_parts.append(_truncate(json.dumps(step, ensure_ascii=False), 500))

    return {
        "title": title,
        "action": action,
        "body": _truncate("\n\n".join(part for part in body_parts if part), 1200),
        "url": url,
    }


def _step_sidebar_label(step: dict[str, Any], harness: str) -> str:
    if "model_output" in step:
        model_output = step.get("model_output") or {}
        actions = model_output.get("action")
        if isinstance(actions, list) and actions and isinstance(actions[0], dict):
            return str(next(iter(actions[0].keys())))
        return f"Step {step.get('step', '?')}"
    if step.get("kind") == "message":
        return "User Message" if step.get("source") == "user" else "Agent Message"
    if step.get("kind") == "action":
        return str(step.get("tool") or "action")
    return f"Step {step.get('index', step.get('step', '?'))}"


def _step_kind_class(step: dict[str, Any]) -> str:
    if step.get("kind") == "user":
        return "user"
    if step.get("kind") == "message" and step.get("source") == "user":
        return "user"
    if step.get("kind") == "action" or "model_output" in step:
        return "tool"
    return "agent"


def _ui_agent_steps(test: dict[str, Any], harness: str) -> list[dict[str, str]]:
    trajectory = test.get("trajectory") or {}
    agent_steps = (trajectory.get("agent") or {}).get("steps") or []
    rows: list[dict[str, str]] = [
        {
            "id": "0",
            "label": "User Message",
            "kind": "user",
            "title": "TASK",
            "action": "",
            "body": str(test.get("input") or ""),
            "url": str(test.get("task_url") or ""),
        }
    ]
    for raw_step in agent_steps:
        if not isinstance(raw_step, dict):
            continue
        if raw_step.get("kind") == "message" and raw_step.get("source") == "user":
            continue
        norm = _normalize_agent_step(raw_step, harness)
        rows.append(
            {
                "id": str(len(rows)),
                "label": _step_sidebar_label(raw_step, harness),
                "kind": _step_kind_class(raw_step),
                "title": norm["title"],
                "action": norm["action"],
                "body": norm["body"],
                "url": norm["url"],
            }
        )
    return rows


def _extract_action_rows(test: dict[str, Any], harness: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for step in _ui_agent_steps(test, harness)[1:]:
        if step["action"] and step["action"] != "—":
            rows.append({"step": step["id"], "name": step["label"], "detail": step["action"]})
    extended = test.get("extended_metrics") or {}
    if not rows and extended.get("action_count"):
        rows.append(
            {
                "step": "—",
                "name": "summary",
                "detail": f"action_count={extended.get('action_count')}, redundancy={extended.get('action_redundancy')}",
            }
        )
    return rows


def _coerce_positive_cost(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    amount = float(value)
    return amount if amount > 0 else None


def _task_cost_usd(test: dict[str, Any], model: str) -> float | None:
    """Return per-task LLM cost from recorded usage or pricing table."""
    usage_by_model = test.get("token_usage_by_model")
    if isinstance(usage_by_model, dict) and usage_by_model:
        total = 0.0
        priced = False
        for usage in usage_by_model.values():
            if not isinstance(usage, dict):
                continue
            cost = _coerce_positive_cost(usage.get("cost_usd"))
            if cost is not None:
                total += cost
                priced = True
        if priced:
            return total

    for container in (
        test,
        test.get("token_usage") if isinstance(test.get("token_usage"), dict) else None,
    ):
        if not isinstance(container, dict):
            continue
        for key in ("cost_usd", "total_cost_usd", "cost", "total_cost"):
            cost = _coerce_positive_cost(container.get(key))
            if cost is not None:
                return cost

    usage = test.get("token_usage")
    if not isinstance(usage, dict):
        return None
    try:
        from src.export_results import _ensure_repo_on_path

        _ensure_repo_on_path()
        from bench_eval.llm_cost import compute_token_cost_usd, load_pricing_table
        from bench_eval.token_usage import normalize_token_usage

        normalized = normalize_token_usage(usage)
        cost, _ = compute_token_cost_usd(
            model=model,
            prompt_tokens=normalized["prompt_tokens"],
            completion_tokens=normalized["completion_tokens"],
            total_tokens=normalized["total_tokens"],
            pricing_table=load_pricing_table(),
        )
        return cost if cost is not None and cost > 0 else None
    except Exception:
        return None


def _format_tokens(token_usage: dict[str, Any] | None) -> str:
    if not token_usage:
        return "—"
    prompt = token_usage.get("prompt_tokens")
    completion = token_usage.get("completion_tokens")
    if prompt is None and completion is None:
        total = token_usage.get("total_tokens")
        return str(total) if total is not None else "—"
    prompt_s = f"{float(prompt) / 1000:.2f}K" if isinstance(prompt, (int, float)) and prompt >= 1000 else str(prompt or 0)
    completion_s = (
        f"{float(completion) / 1000:.2f}K" if isinstance(completion, (int, float)) and completion >= 1000 else str(completion or 0)
    )
    return f"{prompt_s} in / {completion_s} out"


def _meta_cell(icon: str, label: str, value: object) -> str:
    return (
        '<div class="wab-trace-meta-cell">'
        f'<div class="wab-trace-meta-label"><span class="wab-trace-meta-icon">{icon}</span>{_esc(label)}</div>'
        f'<div class="wab-trace-meta-value">{_esc(value)}</div>'
        "</div>"
    )


def _trace_slug(entry: LeaderboardEntry, test_name: str) -> str:
    short_model = entry.model.split("/")[-1] if "/" in entry.model else entry.model
    return f"{test_name}-{entry.harness}-{short_model}"


def _detail_tab_button(tab_id: str, label: str, count: int | None = None, *, active: bool = False) -> str:
    count_html = f'<span class="wab-trace-tab-count">{count}</span>' if count is not None else ""
    active_cls = " active" if active else ""
    return (
        f'<button type="button" class="wab-trace-detail-tab{active_cls}" '
        f'data-wab-trace-tab="{html.escape(tab_id)}">{html.escape(label)}{count_html}</button>'
    )


def trace_summaries_for_entry(entry: LeaderboardEntry) -> list[dict[str, Any]]:
    raw = load_raw_results(entry)
    if not raw:
        return []
    rows: list[dict[str, Any]] = []
    for test in raw.get("tests") or []:
        if not isinstance(test, dict):
            continue
        test_name = str(test.get("test_name") or "")
        if not test_name:
            continue
        trajectory = test.get("trajectory") or {}
        agent_steps = (trajectory.get("agent") or {}).get("steps") or []
        dab_events = trajectory.get("dab_events") or []
        ui = test.get("ui_taxonomy") or {}
        rows.append(
            {
                "test_name": test_name,
                "section": _task_section_label(test_name),
                "success": bool(test.get("success")),
                "duration": test.get("duration_seconds"),
                "agent_steps": test.get("agent_steps") or len(agent_steps),
                "dab_events": len(dab_events),
                "input": str(test.get("input") or ""),
                "domain": ui.get("domain") or "",
                "primary_class": (ui.get("checked_classes") or [None])[0],
            }
        )
    rows.sort(key=lambda row: row["test_name"])
    return rows


def _status_badge(success: bool) -> str:
    css = "wab-trace-status pass" if success else "wab-trace-status fail"
    label = "PASS" if success else "FAIL"
    return f'<span class="{css}">{label}</span>'


def _trace_pill(entry_id: str, inner: str, *, active: bool = False) -> str:
    active_cls = " active" if active else ""
    return (
        f'<button type="button" class="wab-trace-pill{active_cls}" '
        f'data-wab-trace-filter="{html.escape(entry_id)}">{inner}</button>'
    )


def _trace_card(entry_id: str, test_name: str, inner: str, *, visible: bool = True) -> str:
    hidden = "" if visible else ' style="display:none"'
    payload = f"traces:detail:{entry_id}:{test_name}"
    return (
        f'<button type="button" class="wab-trace-card" data-wab-entry-id="{html.escape(entry_id)}"'
        f' data-wab-trace="{html.escape(payload)}"{hidden}>'
        f"{inner}</button>"
    )


def _trace_link(payload: str, inner: str, css_class: str = "wab-trace-link") -> str:
    return (
        f'<button type="button" class="{css_class}" data-wab-trace="{html.escape(payload)}">'
        f"{inner}</button>"
    )


def build_traces_shell(
    entries: list[LeaderboardEntry],
    *,
    view: str = "list",
    entry_id: str = "",
    test_name: str = "",
) -> str:
    if not entries:
        return (
            '<div class="wab-traces">'
            '<h2 class="wab-traces-title">Agent Traces</h2>'
            '<p class="wab-detail-note">No submissions yet. Export results after eval.</p>'
            "</div>"
        )

    if view == "detail" and entry_id and test_name:
        return build_trace_detail(entries, entry_id, test_name)

    selected = entry_by_id(entries, entry_id) or entries[0]
    selected_id = selected.entry_id
    return _build_traces_list(entries, selected_id)


def _build_traces_list(entries: list[LeaderboardEntry], selected_id: str) -> str:
    selected_entry = entry_by_id(entries, selected_id) or entries[0]
    selected_summaries = trace_summaries_for_entry(selected_entry)
    pills: list[str] = []
    for entry in entries:
        count = (
            len(selected_summaries)
            if entry.entry_id == selected_entry.entry_id
            else int(entry.total_tasks or 0)
        )
        active = entry.entry_id == selected_id
        label = html.escape(entry.model.split("/")[-1] if "/" in entry.model else entry.model)
        harness = html.escape(entry.harness)
        inner = (
            f'<span class="wab-trace-pill-model">{label}</span>'
            f'<span class="wab-trace-pill-harness">{harness}</span>'
            f'<span class="wab-trace-pill-count">{count}</span>'
        )
        pills.append(_trace_pill(entry.entry_id, inner, active=active))

    cards: list[str] = []
    for row in selected_summaries:
        test_name = row["test_name"]
        short_name = test_name.replace("bench_", "", 1) if test_name.startswith("bench_") else test_name
        tags = []
        if row["domain"]:
            tags.append(f'<span class="wab-badge domain">{_esc(row["domain"])}</span>')
        if row["primary_class"]:
            tags.append(f'<span class="wab-badge taxonomy">{_esc(row["primary_class"])}</span>')
        tags_html = "".join(tags)
        card_inner = (
            f'<div class="wab-trace-card-accent {"pass" if row["success"] else "fail"}"></div>'
            f'<div class="wab-trace-card-body">'
            f'<div class="wab-trace-card-top">'
            f'<span class="wab-trace-card-id">#{_esc(short_name)}</span>'
            f'<span class="wab-trace-card-section">{_esc(row["section"])}</span>'
            f"{_status_badge(row['success'])}"
            f'<span class="wab-trace-card-duration">⏱ {_esc(format_duration(row["duration"]))}</span>'
            f'<span class="wab-trace-card-steps">{row["agent_steps"]} steps · {row["dab_events"]} WebPageBench</span>'
            f"</div>"
            f'<p class="wab-trace-card-task">{_esc(_truncate(row["input"], 220))}</p>'
            f'<div class="wab-trace-card-tags">{tags_html}</div>'
            f"</div>"
        )
        cards.append(_trace_card(selected_entry.entry_id, test_name, card_inner))

    body = "".join(cards) if cards else '<p class="wab-detail-note">No task traces in this run.</p>'
    return (
        '<div class="wab-traces">'
        '<h2 class="wab-traces-title">Agent Traces</h2>'
        '<p class="wab-traces-subtitle">Step-by-step agent actions and WebPageBench events from every eval run.</p>'
        f'<div class="wab-trace-pills">{"".join(pills)}</div>'
        f'<div class="wab-trace-cards">{body}</div>'
        "</div>"
    )


def _find_test(entry: LeaderboardEntry, test_name: str) -> dict[str, Any] | None:
    raw = load_raw_results(entry)
    if not raw:
        return None
    for test in raw.get("tests") or []:
        if isinstance(test, dict) and test.get("test_name") == test_name:
            return test
    return None


def build_trace_detail(entries: list[LeaderboardEntry], entry_id: str, test_name: str) -> str:
    entry = entry_by_id(entries, entry_id)
    if entry is None:
        return '<div class="wab-traces"><p class="wab-detail-note">Submission not found.</p></div>'

    test = _find_test(entry, test_name)
    if test is None:
        return '<div class="wab-traces"><p class="wab-detail-note">Task trace not found.</p></div>'

    raw = load_raw_results(entry) or {}
    run = raw.get("run") or {}
    trajectory = test.get("trajectory") or {}
    dab_events = trajectory.get("dab_events") or []
    harness = entry.harness or (test.get("agent_harness") or "")
    ui = test.get("ui_taxonomy") or {}
    dab_check = test.get("dab_check") or {}
    agent = test.get("agent") or {}
    ui_steps = _ui_agent_steps(test, harness)
    action_rows = _extract_action_rows(test, harness)

    short_name = test_name.replace("bench_", "", 1) if test_name.startswith("bench_") else test_name
    slug = _trace_slug(entry, test_name)
    provider = entry.provider or run.get("provider") or "—"
    domain = ui.get("domain") or "—"
    section = _task_section_label(test_name)
    token_usage = test.get("token_usage") or agent.get("token_usage") or {}
    task_cost = _task_cost_usd(test, entry.model)
    model_usage = format_task_token_usage(
        test,
        primary_model=entry.model,
        ouroboros_model_slots=entry.ouroboros_model_slots,
    )
    success = bool(test.get("success"))

    meta_grid = "".join(
        [
            _meta_cell("#", "Task", f"#{short_name}"),
            _meta_cell("🧪", "Test case", test_name),
            _meta_cell("🤖", "Model", entry.model),
            _meta_cell("☁", "Provider", provider),
            _meta_cell("🏷", "Category", f"{section} / {domain}"),
            _meta_cell("🌐", "Harness", harness),
            _meta_cell("🖼", "Input", entry.input_modality),
            _meta_cell("👣", "Steps", test.get("agent_steps") or max(0, len(ui_steps) - 1)),
            _meta_cell("🪙", "Tokens", _format_tokens(token_usage)),
            _meta_cell("🧩", "Model usage", model_usage),
            _meta_cell("💰", "Cost", fmt_cost(task_cost)),
            _meta_cell("⏱", "Duration", format_duration(test.get("duration_seconds"))),
            _meta_cell("🚩", "Result", "PASS" if success else "FAIL"),
        ]
    )

    step_nav_items: list[str] = []
    step_panels: list[str] = []
    for step in ui_steps:
        active = " active" if step["id"] == "0" else ""
        step_nav_items.append(
            f'<button type="button" class="wab-trace-step-item{active}" data-wab-trace-step="{html.escape(step["id"])}" '
            f'data-wab-step-label="{html.escape(step["label"].lower())}">'
            f'<span class="wab-trace-step-num">{int(step["id"]) + 1}</span>'
            f'<span class="wab-trace-step-kind wab-trace-step-kind-{html.escape(step["kind"])}"></span>'
            f'<span class="wab-trace-step-label">{_esc(step["label"])}</span>'
            "</button>"
        )
        url_line = f'<div class="wab-trace-step-url">{_esc(step["url"])}</div>' if step["url"] else ""
        action_line = (
            f'<div class="wab-trace-step-action-line"><strong>Action:</strong> {_esc(step["action"])}</div>'
            if step["action"]
            else ""
        )
        step_panels.append(
            f'<div class="wab-trace-step-panel{active}" data-wab-trace-step-panel="{html.escape(step["id"])}">'
            f'<div class="wab-trace-step-panel-head"><span class="wab-trace-step-kind wab-trace-step-kind-{html.escape(step["kind"])}"></span>'
            f"<strong>{_esc(step['title'])}</strong></div>"
            f"{url_line}{action_line}"
            f'<pre class="wab-trace-step-body">{_esc(step["body"])}</pre>'
            "</div>"
        )

    action_cards = []
    for row in action_rows:
        action_cards.append(
            '<article class="wab-trace-dab-event">'
            f'<div class="wab-trace-dab-head"><strong>Step {row["step"]}: {_esc(row["name"])}</strong></div>'
            f'<pre class="wab-trace-step-body">{_esc(row["detail"])}</pre>'
            "</article>"
        )

    dab_cards = []
    for event in dab_events[:120]:
        if not isinstance(event, dict):
            continue
        event_name = event.get("event_name") or event.get("event_data", {}).get("type") or "event"
        event_data = event.get("event_data") or {}
        summary = _truncate(json.dumps(event_data, ensure_ascii=False), 800)
        dab_cards.append(
            '<article class="wab-trace-dab-event">'
            f'<div class="wab-trace-dab-head"><strong>{_esc(event_name)}</strong>'
            f'<span>{_esc(event.get("event_ts"))}</span></div>'
            f'<pre class="wab-trace-step-body">{_esc(summary)}</pre>'
            "</article>"
        )

    checks = dab_check.get("check_results") or []
    check_rows = []
    for row in checks:
        if not isinstance(row, dict):
            continue
        ok = bool(row.get("passed"))
        mark = "✓" if ok else "✗"
        check_rows.append(
            "<li>"
            f'<span class="{"wab-trace-check-pass" if ok else "wab-trace-check-fail"}">{mark}</span> '
            f"{_esc(row.get('condition') or row.get('name') or 'condition')}"
            "</li>"
        )
    checks_html = "<ul class='wab-trace-checks'>" + "".join(check_rows) + "</ul>" if check_rows else "<p>—</p>"

    export_json = json.dumps(test, ensure_ascii=False).replace("</", "<\\/")
    tabs = "".join(
        [
            _detail_tab_button("agent", "Agent", len(ui_steps), active=True),
            _detail_tab_button("actions", "Actions", len(action_rows) or None),
            _detail_tab_button("requests", "Requests", len(dab_events) or None),
            _detail_tab_button("eval", "Eval", len(checks) or None),
            _detail_tab_button("logs", "Logs"),
        ]
    )

    actions_body = "".join(action_cards) if action_cards else '<p class="wab-detail-note">No actions recorded.</p>'
    requests_body = "".join(dab_cards) if dab_cards else '<p class="wab-detail-note">No WebPageBench events.</p>'

    back = _trace_link(f"traces:list:{entry_id}", "← Traces", "wab-trace-back")

    return (
        f'<div class="wab-traces wab-trace-detail-view" id="wab-trace-detail">'
        f'<nav class="wab-trace-crumb">{back}<span class="wab-trace-crumb-sep">›</span>'
        f'<span class="wab-trace-crumb-current">{_esc(slug)}</span></nav>'
        '<header class="wab-trace-hero-card">'
        f'<p class="wab-trace-hero-task">{_esc(test.get("input") or "")}</p>'
        f'<div class="wab-trace-meta-grid">{meta_grid}</div>'
        '<div class="wab-trace-hero-foot">'
        f"{_status_badge(success)}"
        '<button type="button" class="wab-trace-export" data-wab-trace-export="1">⬇ Export JSON</button>'
        "</div>"
        f'<script type="application/json" class="wab-trace-export-data">{export_json}</script>'
        "</header>"
        f'<div class="wab-trace-detail-tabs">{tabs}</div>'
        '<div class="wab-trace-detail-panels">'
        '<section class="wab-trace-detail-panel active" data-wab-trace-panel="agent">'
        '<div class="wab-trace-split">'
        '<aside class="wab-trace-step-sidebar">'
        '<div class="wab-trace-step-sidebar-head">'
        '<input type="text" class="wab-trace-step-filter" placeholder="Filter steps..." />'
        f'<span class="wab-trace-step-total">{len(ui_steps)} steps</span>'
        "</div>"
        f'<div class="wab-trace-step-nav">{"".join(step_nav_items)}</div>'
        "</aside>"
        f'<main class="wab-trace-step-main">{"".join(step_panels)}</main>'
        "</div>"
        "</section>"
        '<section class="wab-trace-detail-panel" data-wab-trace-panel="actions">'
        f'<div class="wab-trace-dab-list">{actions_body}</div>'
        "</section>"
        '<section class="wab-trace-detail-panel" data-wab-trace-panel="requests">'
        f'<div class="wab-trace-dab-list">{requests_body}</div>'
        "</section>"
        '<section class="wab-trace-detail-panel" data-wab-trace-panel="eval">'
        f"<p><strong>all_passed:</strong> {_esc(dab_check.get('all_passed'))}</p>"
        f"{checks_html}"
        f"<p><strong>failed_conditions:</strong> {_esc(', '.join(dab_check.get('failed_conditions') or []) or '—')}</p>"
        "</section>"
        '<section class="wab-trace-detail-panel" data-wab-trace-panel="logs">'
        "<h4>Agent output</h4>"
        f'<pre class="wab-trace-output">{_esc(_truncate(str(test.get("actual_output") or ""), 6000))}</pre>'
        "<h4>Final result</h4>"
        f'<pre class="wab-trace-output">{_esc(_truncate(str(agent.get("final_result") or ""), 4000))}</pre>'
        "<h4>Agent error</h4>"
        f'<pre class="wab-trace-output">{_esc(test.get("agent_error") or "—")}</pre>'
        "</section>"
        "</div>"
        "</div>"
    )


def build_trace_js_on_load() -> str:
    """Gradio 6 js_on_load for trace list/detail interactions (must include 'navigate')."""
    return """
function filterTraceEntry(root, entryId) {
  if (!root || !entryId) return;
  root.querySelectorAll(".wab-trace-pill").forEach((pill) => {
    pill.classList.toggle("active", pill.getAttribute("data-wab-trace-filter") === entryId);
  });
  root.querySelectorAll(".wab-trace-card").forEach((card) => {
    card.style.display = card.getAttribute("data-wab-entry-id") === entryId ? "flex" : "none";
  });
}

element.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-wab-trace-tab]");
  if (tab && tab.closest(".wab-trace-detail-view")) {
    event.preventDefault();
    const root = tab.closest(".wab-trace-detail-view");
    const tabId = tab.getAttribute("data-wab-trace-tab");
    root.querySelectorAll("[data-wab-trace-tab]").forEach((el) => {
      el.classList.toggle("active", el === tab);
    });
    root.querySelectorAll("[data-wab-trace-panel]").forEach((panel) => {
      panel.classList.toggle("active", panel.getAttribute("data-wab-trace-panel") === tabId);
    });
    return;
  }

  const stepBtn = event.target.closest("[data-wab-trace-step]");
  if (stepBtn && stepBtn.closest(".wab-trace-detail-view")) {
    event.preventDefault();
    const root = stepBtn.closest(".wab-trace-detail-view");
    const stepId = stepBtn.getAttribute("data-wab-trace-step");
    root.querySelectorAll("[data-wab-trace-step]").forEach((el) => {
      el.classList.toggle("active", el === stepBtn);
    });
    root.querySelectorAll("[data-wab-trace-step-panel]").forEach((panel) => {
      panel.classList.toggle("active", panel.getAttribute("data-wab-trace-step-panel") === stepId);
    });
    return;
  }

  const exportBtn = event.target.closest("[data-wab-trace-export]");
  if (exportBtn && exportBtn.closest(".wab-trace-detail-view")) {
    event.preventDefault();
    const root = exportBtn.closest(".wab-trace-detail-view");
    const dataEl = root.querySelector(".wab-trace-export-data");
    if (!dataEl) return;
    const blob = new Blob([dataEl.textContent], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = (root.querySelector(".wab-trace-crumb-current")?.textContent || "trace") + ".json";
    a.click();
    URL.revokeObjectURL(url);
    return;
  }

  const pill = event.target.closest("[data-wab-trace-filter]");
  if (pill) {
    event.preventDefault();
    const entryId = pill.getAttribute("data-wab-trace-filter");
    if (!entryId) return;
    trigger("navigate", { payload: `traces:list:${entryId}` });
    return;
  }

  const navBtn = event.target.closest("[data-wab-trace]");
  if (!navBtn) return;
  event.preventDefault();
  const payload = navBtn.getAttribute("data-wab-trace");
  if (!payload) return;
  if (payload.startsWith("traces:list:")) {
    trigger("navigate", { payload });
    return;
  }
  if (window.wabOpenDetailTab) window.wabOpenDetailTab("traces");
  const anchor = document.getElementById("wab-detail-anchor");
  if (anchor) anchor.scrollIntoView({ behavior: "smooth", block: "start" });
  trigger("navigate", { payload });
});

element.addEventListener("input", (event) => {
  const input = event.target.closest(".wab-trace-step-filter");
  if (!input) return;
  const root = input.closest(".wab-trace-detail-view");
  if (!root) return;
  const query = (input.value || "").trim().toLowerCase();
  root.querySelectorAll("[data-wab-trace-step]").forEach((btn) => {
    const label = btn.getAttribute("data-wab-step-label") || "";
    btn.style.display = !query || label.includes(query) ? "" : "none";
  });
});
"""
