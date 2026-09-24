"""PinchBench-inspired HTML UI for WebPageBench."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from src.bench_config import load_bench_config, task_count
from src.formatting import fmt_cost, fmt_duration, fmt_number, fmt_pct_value, fmt_steps, round2
from src.load_entries import sort_entries
from src.models import LeaderboardEntry
from src.input_modality import INPUT_HELP
from src.token_display import fmt_tokens, format_model_usage_breakdown_html

_DETAIL_TAB_LABELS = {
    "submission": "Submission",
    "sections": "Sections",
    "taxonomy": "UI taxonomy",
    "metrics": "Metrics",
    "traces": "Traces",
    "about": "About",
}


def load_css() -> str:
    return (Path(__file__).resolve().parent.parent / "assets" / "pinchbench.css").read_text(encoding="utf-8")


def score_tier(pct: float | None) -> str:
    if pct is None:
        return "danger"
    if pct >= 70:
        return "success"
    if pct >= 40:
        return "warning"
    return "danger"


def fmt_pct(value: float | None) -> str:
    return fmt_pct_value(value)


def fmt_pct_display(entry: LeaderboardEntry) -> str:
    if entry.success_rate is None:
        return "—"
    return fmt_pct_value(entry.success_rate)


def provider_from_model(model: str, provider: str | None = None) -> str:
    if provider:
        return provider
    if "/" in model:
        return model.split("/", 1)[0]
    return model.split("-", 1)[0]


def _badge_link(label: str, passed: object, total: object, css_class: str, title: str, nav: str) -> str:
    stat_html = ""
    try:
        passed_i = int(passed) if passed is not None else None
        total_i = int(total) if total is not None else None
    except (TypeError, ValueError):
        passed_i = total_i = None
    if passed_i is not None and total_i is not None:
        stat_html = f'<span class="wab-badge-stat">{passed_i}/{total_i}</span>'

    return (
        f'<span role="button" tabindex="0" class="wab-badge wab-badge-link {css_class}" '
        f'title="{html.escape(title)}" data-wab-nav="{html.escape(nav)}">'
        f"{html.escape(label)}{stat_html}</span>"
    )


def _badge(label: str, css_class: str, title: str) -> str:
    return (
        f'<span class="wab-badge {css_class}" title="{html.escape(title)}">'
        f"{html.escape(label)}</span>"
    )


def _row_badges(entry: LeaderboardEntry) -> str:
    config = load_bench_config()
    badges: list[str] = []

    ranked_sections = sorted(
        (
            (stats.success_rate, stats.section_id, stats.label, stats.passed, stats.total)
            for stats in entry.sections.values()
            if stats.success_rate is not None
        ),
        reverse=True,
    )[:2]
    for _, section_id, label, passed, total in ranked_sections:
        desc = config["sections"].get(section_id, {}).get("description", label)
        nav = f"sections:{section_id}"
        badges.append(_badge_link(label, passed, total, "domain", str(desc), nav))

    ranked_taxonomy = sorted(
        (
            (float(row.get("success_rate")), class_id)
            for class_id, row in entry.ui_classes.items()
            if isinstance(row.get("success_rate"), (int, float))
        ),
        reverse=True,
    )[:2]
    if not ranked_taxonomy and entry.ui_badges:
        for class_id in entry.ui_badges[:2]:
            meta = config.get("ui_classes", {}).get(class_id, {})
            label = str(meta.get("label") or class_id)
            row = entry.ui_classes.get(class_id) or {}
            nav = f"taxonomy:{class_id}"
            badges.append(
                _badge_link(
                    label,
                    row.get("passed"),
                    row.get("total"),
                    "taxonomy",
                    str(meta.get("description") or class_id),
                    nav,
                )
            )
    else:
        for _, class_id in ranked_taxonomy:
            meta = config.get("ui_classes", {}).get(class_id, {})
            row = entry.ui_classes.get(class_id) or {}
            label = str(meta.get("label") or class_id)
            nav = f"taxonomy:{class_id}"
            badges.append(
                _badge_link(
                    label,
                    row.get("passed"),
                    row.get("total"),
                    "taxonomy",
                    str(meta.get("description") or class_id),
                    nav,
                )
            )

    return "".join(badges)


def top_section_badges(entry: LeaderboardEntry, limit: int = 2) -> list[str]:
    ranked = [
        (stats.success_rate, stats.label)
        for stats in entry.sections.values()
        if stats.success_rate is not None
    ]
    ranked.sort(reverse=True)
    return [label for _, label in ranked[:limit]]


def pick_winner(entries: list[LeaderboardEntry], metric: str, *, ascending: bool = False) -> LeaderboardEntry | None:
    if not entries:
        return None
    values = [(entry, entry.metric(metric)) for entry in entries]
    values = [(entry, value) for entry, value in values if value is not None]
    if not values:
        return None
    return min(values, key=lambda pair: pair[1])[0] if ascending else max(values, key=lambda pair: pair[1])[0]


def _quick_card(label: str, headline: str, entry: LeaderboardEntry, subtitle: str) -> str:
    return f"""
    <article class="wab-quick-card">
      <div class="wab-quick-kicker">{html.escape(label)}</div>
      <div class="wab-quick-score">{html.escape(headline)}</div>
      <div class="wab-quick-model">{html.escape(entry.model)}</div>
      <div class="wab-quick-meta">{html.escape(subtitle)}<br>{html.escape(entry.harness)}</div>
    </article>
    """


def _pick_headline(entry: LeaderboardEntry, metric: str) -> str:
    if metric == "success_rate" or metric == "full_bench_success_rate":
        return fmt_pct_display(entry)
    if metric == "avg_duration_seconds":
        return fmt_duration(entry.avg_duration_seconds)
    if metric == "total_duration_seconds":
        return fmt_duration(entry.total_duration_seconds)
    if metric in {"total_cost_usd", "avg_cost_per_task_usd"}:
        return fmt_cost(entry.total_cost_usd)
    if metric == "value_score":
        value = entry.value_score
        return fmt_number(value) if value is not None else "—"
    if metric.startswith("domain:"):
        return fmt_pct(entry.metric(metric))
    return fmt_pct_display(entry)


_GLOBAL_HIGHLIGHTS: tuple[dict[str, object], ...] = (
    {
        "label": "Best Overall",
        "metric": "success_rate",
        "ascending": False,
        "subtitle": "Highest WebPageBench success rate on full bench.",
    },
    {
        "label": "Best Budget",
        "metric": "total_cost_usd",
        "ascending": True,
        "subtitle": "Lowest total LLM cost for the run.",
    },
    {
        "label": "Fastest",
        "metric": "total_duration_seconds",
        "ascending": True,
        "subtitle": "Lowest total run duration (sum of per-task times).",
    },
)


def build_highlight_picks(entries: list[LeaderboardEntry]) -> str:
    """Top highlights shown above view tabs on every leaderboard page."""
    cards: list[str] = []
    for pick in _GLOBAL_HIGHLIGHTS:
        metric = str(pick["metric"])
        winner = pick_winner(entries, metric, ascending=bool(pick["ascending"]))
        if winner is None:
            continue
        cards.append(
            _quick_card(
                str(pick["label"]),
                _pick_headline(winner, metric),
                winner,
                str(pick["subtitle"]),
            )
        )
    if not cards:
        return ""
    return (
        '<section class="wab-highlights">'
        '<div class="wab-section-label">Quick Picks</div>'
        f'<div class="wab-quick-grid">{"".join(cards)}</div>'
        "</section>"
    )


def build_quick_picks(entries: list[LeaderboardEntry], view_id: str) -> str:
    config = load_bench_config()
    picks = config["quick_picks"].get(view_id, [])
    cards: list[str] = []
    for pick in picks:
        metric = pick["metric"]
        ascending = metric in {"avg_duration_seconds", "total_duration_seconds", "total_cost_usd"}
        winner = pick_winner(entries, metric, ascending=ascending)
        if winner is None:
            continue
        cards.append(_quick_card(pick["label"], _pick_headline(winner, metric), winner, pick["subtitle"]))
    if not cards:
        return ""
    return f'<div class="wab-quick-grid">{"".join(cards)}</div>'


def _input_badge(entry: LeaderboardEntry) -> str:
    modality = entry.input_modality
    css = modality.replace("+", "-plus-") if modality not in {"—", ""} else "unknown"
    return (
        f'<span class="wab-input wab-input-{html.escape(css)}" '
        f'title="{html.escape(INPUT_HELP)}">{html.escape(modality)}</span>'
    )


def _success_row(idx: int, entry: LeaderboardEntry) -> str:
    pct = entry.success_pct or 0
    tier = score_tier(pct)
    badges = _row_badges(entry)
    return f"""
    <tr>
      <td class="wab-rank">{idx + 1}</td>
      <td class="wab-model-cell">
        <div class="wab-model-name">{html.escape(entry.model)}</div>
        <div class="wab-badges">{badges}</div>
      </td>
      <td><span class="wab-harness">{html.escape(entry.harness)}</span></td>
      <td>{_input_badge(entry)}</td>
      <td>{entry.passed_tasks}/{entry.total_tasks}</td>
      <td class="wab-score-cell">
        <div class="wab-score-value wab-score-{tier}">{html.escape(fmt_pct_display(entry))}</div>
        <div class="wab-bar"><span class="wab-bar-{tier}" style="width:{max(pct, 0):.1f}%"></span></div>
      </td>
    </tr>
    """


def _speed_row(idx: int, entry: LeaderboardEntry) -> str:
    pct = entry.success_pct or 0
    tier = score_tier(pct)
    return f"""
    <tr>
      <td class="wab-rank">{idx + 1}</td>
      <td class="wab-model-cell"><div class="wab-model-name">{html.escape(entry.model)}</div>
        <div class="wab-badges"><span class="wab-badge">{html.escape(entry.harness)}</span>{_input_badge(entry)}</div></td>
      <td>{html.escape(fmt_duration(entry.total_duration_seconds))}</td>
      <td>{html.escape(fmt_duration(entry.avg_duration_seconds))}</td>
      <td>{html.escape(fmt_steps(entry.total_agent_steps))}</td>
      <td class="wab-score-cell">
        <div class="wab-score-value wab-score-{tier}">{html.escape(fmt_pct_display(entry))}</div>
        <div class="wab-bar"><span class="wab-bar-{tier}" style="width:{max(pct, 0):.1f}%"></span></div>
      </td>
    </tr>
    """


def _cost_row(idx: int, entry: LeaderboardEntry) -> str:
    pct = entry.success_pct or 0
    tier = score_tier(pct)
    value = entry.value_score
    return f"""
    <tr>
      <td class="wab-rank">{idx + 1}</td>
      <td class="wab-model-cell"><div class="wab-model-name">{html.escape(entry.model)}</div>
        <div class="wab-badges"><span class="wab-badge">{html.escape(entry.harness)}</span>{_input_badge(entry)}</div></td>
      <td>{html.escape(fmt_cost(entry.total_cost_usd))}</td>
      <td>{html.escape(fmt_cost(entry.avg_cost_per_task_usd))}</td>
      <td>{html.escape(fmt_tokens(entry.total_tokens))}</td>
      <td>{html.escape(fmt_tokens(entry.avg_tokens_per_task))}</td>
      <td class="wab-token-split-cell">{format_model_usage_breakdown_html(entry)}</td>
      <td>{fmt_number(value) if value is not None else "—"}</td>
      <td class="wab-score-cell">
        <div class="wab-score-value wab-score-{tier}">{html.escape(fmt_pct_display(entry))}</div>
        <div class="wab-bar"><span class="wab-bar-{tier}" style="width:{max(pct, 0):.1f}%"></span></div>
      </td>
    </tr>
    """


def build_table(entries: list[LeaderboardEntry], view_id: str) -> str:
    config = load_bench_config()
    view = next(row for row in config["views"] if row["id"] == view_id)
    sorted_entries = sort_entries(entries, view_id)

    if view_id == "speed":
        head = "<tr><th>#</th><th>Model</th><th>Total time</th><th>Avg time</th><th>Total steps</th><th>Success %</th></tr>"
        rows = [_speed_row(i, entry) for i, entry in enumerate(sorted_entries)]
        subtitle = (
            "Sorted by total run duration (run.total_duration_seconds). "
            "Avg time is mean per-task duration. Total steps is the sum of agent_steps across tasks."
        )
    elif view_id == "cost":
        head = (
            "<tr><th>#</th><th>Model</th><th>Total $</th><th>$/task</th>"
            "<th>Total tokens</th><th>Tokens/task</th><th>Model usage</th>"
            "<th>Value</th><th>Success %</th></tr>"
        )
        rows = [_cost_row(i, entry) for i, entry in enumerate(sorted_entries)]
        subtitle = (
            "LLM cost via bench_eval.llm_cost. Tokens from run totals. "
            "Model usage is shown for ouroboros-full runs with multiple configured LLM slots "
            "(main vs fallback/review, …). Hidden for single-LLM harnesses like browser-use "
            "or ouroboros-cut. "
            "Value = success_rate / total_cost_usd."
        )
    else:
        head = "<tr><th>#</th><th>Model</th><th>Harness</th><th>Input</th><th>Tasks</th><th>Success %</th></tr>"
        rows = [_success_row(i, entry) for i, entry in enumerate(sorted_entries)]
        subtitle = (
            "WebPageBench success rate: passed_tasks / total_tasks where dab_check.all_passed is true. "
            f"{INPUT_HELP} See docs/EVAL_README.md."
        )

    body = (
        "".join(rows)
        if rows
        else '<tr><td colspan="9">No runs match the current input / harness filter.</td></tr>'
    )
    return f"""
    <div class="wab-panel">
      <div class="wab-panel-head">
        <h3>{html.escape(view["emoji"])} {html.escape(view["label"])} by model</h3>
        <p>{html.escape(subtitle)}</p>
      </div>
      <div class="wab-table-wrap">
        <table class="wab-table"><thead>{head}</thead><tbody>{body}</tbody></table>
      </div>
      <div class="wab-footnote">
        Tasks and grading criteria:
        <span class="wab-links"><a href="https://github.com/ai-forever/WebPageBench/tree/release/tests/bench" target="_blank">tests/bench</a></span>
        · Metrics:
        <span class="wab-links"><a href="https://github.com/ai-forever/WebPageBench/blob/release/docs/EVAL_README.md" target="_blank">EVAL_README.md</a></span>
      </div>
    </div>
    """


def build_shell_top(entries: list[LeaderboardEntry]) -> str:
    """Header + hero (view switcher is a separate Gradio control)."""
    config = load_bench_config()
    benchmark = config["benchmark"]
    return f"""
    <div class="wab-shell">
      <div class="wab-topbar">
        <div class="wab-brand">
          <div class="wab-logo">🌐</div>
          <div>
            <h1>{html.escape(benchmark["name"])}</h1>
            <p>Web agent benchmark leaderboard</p>
          </div>
        </div>
        <div class="wab-stats">
          <div class="wab-stat"><strong>{len(entries)}</strong> models</div>
          <div class="wab-stat"><strong>{task_count()}</strong> tasks</div>
          <div class="wab-stat"><strong>{len(config["sections"])}</strong> sections</div>
        </div>
      </div>

      <section class="wab-hero">
        <h2>The best models for your web agent.</h2>
        <p>Compare harness × LLM combinations on anonymized mock websites with WebPageBench condition checks.</p>
        <p class="wab-hero-links">
          <a href="#wab-detail-anchor" class="wab-jump-link">Sections &amp; UI taxonomy breakdown ↓</a>
        </p>
      </section>
    </div>
    """


def build_board(entries: list[LeaderboardEntry], view_id: str = "success") -> str:
    return f"""
    <div class="wab-board">
      {build_table(entries, view_id)}
    </div>
    """


def build_shell(entries: list[LeaderboardEntry], view_id: str = "success") -> str:
    return build_shell_top(entries) + build_board(entries, view_id)


def build_nav_js() -> str:
    """Client-side navigation for badge deep links (passed to demo.load js=)."""
    labels = ", ".join(f'"{key}": "{value}"' for key, value in _DETAIL_TAB_LABELS.items())
    return f"""
() => {{
  if (window.__wabNavInit) return [];
  window.__wabNavInit = true;

  const TAB_LABELS = {{{labels}}};

  function setPayload(value) {{
    const root = document.getElementById("wab-nav-payload");
    if (!root) return;
    const input = root.querySelector("textarea, input");
    if (!input) return;
    const proto = input.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
    if (setter) setter.call(input, value);
    else input.value = value;
    input.dispatchEvent(new Event("input", {{ bubbles: true }}));
  }}

  window.wabOpenDetailTab = function (tabId) {{
    const label = TAB_LABELS[tabId];
    if (!label) return;
    const root = document.getElementById("wab-detail-tabs") || document.querySelector(".wab-tabs");
    if (!root) return;
    const buttons = root.querySelectorAll("button");
    for (const btn of buttons) {{
      if ((btn.textContent || "").trim() === label) {{
        btn.click();
        return;
      }}
    }}
    const order = ["submission", "sections", "taxonomy", "metrics", "traces", "about"];
    const idx = order.indexOf(tabId);
    if (idx >= 0 && buttons[idx]) buttons[idx].click();
  }};

  function clickNavButton() {{
    const root = document.getElementById("wab-nav-go");
    if (!root) return false;
    const btn = root.querySelector("button");
    if (!btn) return false;
    btn.click();
    return true;
  }}

  function scrollToDetail() {{
    const anchor = document.getElementById("wab-detail-anchor");
    if (anchor) anchor.scrollIntoView({{ behavior: "smooth", block: "start" }});
  }}

  window.wabNavigate = function (payload) {{
    if (!payload) return;
    window.__wabPendingNav = payload;
    setPayload(payload);
    const tab = payload.split(":", 1)[0] || "submission";
    window.wabOpenDetailTab(tab);
    scrollToDetail();
    setTimeout(clickNavButton, 60);
  }};

  document.addEventListener("click", function (event) {{
    const jump = event.target.closest(".wab-jump-link");
    if (jump) {{
      event.preventDefault();
      scrollToDetail();
      return;
    }}
    const badge = event.target.closest("[data-wab-nav]");
    if (!badge) return;
    event.preventDefault();
    event.stopPropagation();
    window.wabNavigate(badge.getAttribute("data-wab-nav"));
  }});

  document.addEventListener("keydown", function (event) {{
    if (event.key !== "Enter" && event.key !== " ") return;
    const badge = event.target.closest("[data-wab-nav]");
    if (!badge) return;
    event.preventDefault();
    window.wabNavigate(badge.getAttribute("data-wab-nav"));
  }});

  return [];
}}
"""
