"""GigaAgent harness: GigaCode Universal Agent (``gc-cli``) with Playwright MCP.

``gc-cli --config <file> -q "<task>"`` is the headless entry point. The config
carries the OpenAI-compatible backend, the Playwright MCP server and the
guards; ``logging.console_trace: true`` with ``logging.format: jsonl`` makes
stdout a readable event stream. The answer is the ``task_report`` of the
``turn_finish`` envelope, which arrives JSON-encoded in the ``answer`` field of
the single ``final_answer`` event.

The config mirrors ``write_gigaagent_agentic_config`` in lighteval
(``src/lighteval/harnesses/wrapped/cli_agentic_bridge.py``), which was checked
against gc-ua 0.2.3:

* MCP servers live under ``mcp.servers.<name>``;
* the confirmation guards default to ``ask``, which denies without a tty, so
  they are pinned open or every browser call would be refused;
* OpenAI-backed providers need the strict tool-schema spelling.

One departure from lighteval: the browser server is ``stream_stdio`` with
``persistent_session: true``, as GigaAgent's own Playwright snippet
(``recommended_mcp/browser_playwright``) prescribes. Plain ``stdio`` spawns a
new server per tool call -- every call got a fresh, empty browser -- and reads
the first line back as the result, which for Playwright MCP is its
``roots/list`` request, so every observation was that request.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

from bench_eval.config import EvalConfig
from bench_eval.harnesses.base import AgentRunResult, normalize_agent_result
from bench_eval.harnesses.cli_agent import (
    PLAYWRIGHT_MCP_SERVER_NAME,
    build_task_prompt,
    iter_json_lines,
    playwright_mcp_stdio_server,
    resolve_cli_binary,
    run_cli,
    tail,
)
from bench_eval.token_usage import normalize_token_usage

HARNESS = "gigaagent"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MAX_OUTPUT_TOKENS = 4096

#: ``turn_finish`` outcomes in which the agent says it produced an answer.
SCOREABLE_OUTCOMES = frozenset({"direct_answer", "full_solution"})
#: Outcomes in which it says it did not; the report is a status line.
UNFINISHED_OUTCOMES = frozenset({"couldnt_solve", "need_additional_info", "abandoned"})


def resolve_backend_base_url(config: EvalConfig) -> str:
    explicit = os.getenv("GIGAAGENT_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    if config.llm_base_url:
        return config.llm_base_url.rstrip("/")
    if config.llm_provider.lower() == "openrouter":
        return "https://openrouter.ai/api/v1"
    return DEFAULT_OPENAI_BASE_URL


def build_gigaagent_config(
    *,
    base_url: str,
    model: str,
    max_steps: int,
    request_timeout_s: float,
    mcp_server: dict[str, Any],
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    strict_tools_schema: bool = True,
) -> dict[str, Any]:
    server: dict[str, Any] = {
        "command": mcp_server["command"],
        "args": list(mcp_server.get("args") or []),
        "transport": "stream_stdio",
        # One server and one Chromium for the whole task; closed at exit.
        "persistent_session": True,
        "persistent_session_close_tool": "browser_close",
        "description": "Browser automation via Playwright: navigate, click, type, read the page.",
    }
    if mcp_server.get("env"):
        server["env"] = dict(mcp_server["env"])
    return {
        "backend": {
            "api_mode": "chat_completions",
            "completions_url": f"{base_url.rstrip('/')}/chat/completions",
            "chat_completion_headers": {"Authorization": "Bearer ${ENV:OPENAI_API_KEY}"},
            "use_ssl": base_url.startswith("https://"),
            "use_retry": True,
            "request_timeout_sec": max(1, int(request_timeout_s)),
            "chat_completions_max_tokens": max_output_tokens,
            "openai_strict_tools_schema": strict_tools_schema,
        },
        "agent": {
            "model": model,
            "client_name": "webpagebench",
            "verbose": False,
            "max_steps": max(1, int(max_steps)),
            "use_server_subagents": False,
            "use_local_subagents": False,
        },
        "logging": {"console_trace": True, "format": "jsonl", "save_logs": False},
        "security": {
            "command_moderation": {"enabled": False, "mode": "allow"},
            "write_guard": {"enabled": False},
            "read_guard": {"enabled": False},
            "url_policy": {"enabled": False},
        },
        "mcp": {"servers": {PLAYWRIGHT_MCP_SERVER_NAME: server}},
    }


def build_gigaagent_argv(binary: str, *, config_path: str, prompt: str) -> list[str]:
    return [binary, "--config", config_path, "-q", prompt]


def extract_gigaagent_answer(events: list[dict[str, Any]]) -> tuple[Optional[str], Optional[str], dict[str, Any]]:
    """Return ``(answer, error, envelope)`` from the ``final_answer`` event.

    A run whose agent declares it did not finish, or that stopped at its step
    limit, yields no answer: its report is a status line, not a submission.
    """
    finals = [e for e in events if e.get("event") == "final_answer"]
    if len(finals) != 1:
        return None, f"gigaagent emitted {len(finals)} final_answer events (expected 1)", {}
    raw = finals[0].get("answer")
    if not isinstance(raw, str) or not raw.strip():
        return None, "gigaagent final_answer carries no answer envelope", {}
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        return None, "gigaagent final_answer is not a JSON turn_finish envelope", {}
    if not isinstance(envelope, dict):
        return None, "gigaagent final_answer is not a JSON object", {}
    if envelope.get("ok") is False or "status" in envelope:
        return None, f"gigaagent stopped without an answer (status={envelope.get('status')!r})", envelope
    outcome = envelope.get("solution_type")
    if outcome not in SCOREABLE_OUTCOMES:
        return None, f"gigaagent reported solution_type={outcome!r}", envelope
    report = envelope.get("task_report")
    if not isinstance(report, str) or not report.strip():
        return None, "gigaagent turn_finish carries no task_report", envelope
    return report.strip(), None, envelope


def _gigaagent_token_usage(events: list[dict[str, Any]], llm_calls: int) -> dict[str, int]:
    usage_events = [e for e in events if e.get("event") == "run_usage"]
    if not usage_events:
        return normalize_token_usage({"llm_calls": llm_calls})
    total = (usage_events[-1].get("usage") or {}).get("total") or {}
    prompt_tokens = int(total.get("input") or 0)
    completion_tokens = int(total.get("output") or 0)
    return normalize_token_usage(
        {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "llm_calls": llm_calls,
        }
    )


def parse_gigaagent_stream(stdout: str) -> dict[str, Any]:
    events = list(iter_json_lines(stdout))
    steps: list[dict[str, Any]] = []
    submission_ids: set[str] = set()
    assistant_turns = 0
    for event in events:
        if event.get("event") != "dialog_message" or not isinstance(event.get("payload"), dict):
            continue
        payload = event["payload"]
        ptype = str(payload.get("type") or "")
        if ptype == "function_call":
            assistant_turns += 1
            if payload.get("name") == "turn_finish":
                # The submission envelope, not a browser action; its report
                # is read from the final_answer event below.
                submission_ids.add(str(payload.get("call_id") or ""))
                continue
            try:
                arguments = json.loads(payload.get("arguments") or "{}")
            except (TypeError, json.JSONDecodeError):
                arguments = payload.get("arguments")
            steps.append(
                {
                    "index": len(steps),
                    "kind": "action",
                    "tool": payload.get("name"),
                    "action": arguments,
                    "id": payload.get("call_id"),
                }
            )
        elif ptype == "function_call_output":
            if str(payload.get("call_id") or "") in submission_ids:
                continue
            output = payload.get("output")
            steps.append(
                {
                    "index": len(steps),
                    "kind": "observation",
                    "tool_use_id": payload.get("call_id"),
                    "content": tail(output if isinstance(output, str) else json.dumps(output), 4000),
                }
            )
        elif payload.get("role") == "assistant" and isinstance(payload.get("content"), str):
            assistant_turns += 1
            steps.append(
                {
                    "index": len(steps),
                    "kind": "message",
                    "source": "agent",
                    "content": payload["content"].strip(),
                }
            )
    answer, error, envelope = extract_gigaagent_answer(events)
    return {
        "final_result": answer,
        "error": error,
        "is_done": answer is not None,
        "token_usage": _gigaagent_token_usage(events, assistant_turns),
        "trajectory": {
            "harness": HARNESS,
            "summary": {"step_count": len(steps)},
            "steps": steps,
        },
        "metadata": {
            "solution_type": envelope.get("solution_type"),
            "tool_calls": sum(1 for s in steps if s["kind"] == "action"),
        },
    }


def _run_gigaagent_sync(
    task: str,
    *,
    config: EvalConfig,
    navigate_url: Optional[str],
    task_key: Optional[str],
) -> dict[str, Any]:
    binary = resolve_cli_binary("GIGAAGENT_BIN", "gc-cli")
    base_url = resolve_backend_base_url(config)
    api_key = os.getenv("GIGAAGENT_API_KEY", "").strip() or config.llm_api_key or ""
    prompt = build_task_prompt(task, navigate_url)

    workspace = Path(tempfile.mkdtemp(prefix="dab-gigaagent-"))
    config_path = workspace / "config.yml"
    # JSON is valid YAML; gc-cli loads either.
    config_path.write_text(
        json.dumps(
            build_gigaagent_config(
                base_url=base_url,
                model=config.llm_model,
                max_steps=config.agent_max_steps,
                request_timeout_s=config.agent_llm_timeout,
                mcp_server=playwright_mcp_stdio_server(),
                max_output_tokens=int(
                    os.getenv("GIGAAGENT_MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS))
                ),
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = api_key
    print(
        f"[gigaagent] run model={config.llm_model} endpoint={base_url} "
        f"max_steps={config.agent_max_steps}",
        flush=True,
    )
    run = run_cli(
        build_gigaagent_argv(binary, config_path=str(config_path), prompt=prompt),
        env=env,
        cwd=str(workspace),
        timeout=config.agent_run_timeout,
    )
    (workspace / "trace.jsonl").write_text(run.stdout, encoding="utf-8")
    parsed = parse_gigaagent_stream(run.stdout)
    error = parsed["error"]
    if run.timed_out:
        error = f"gigaagent exceeded AGENT_RUN_TIMEOUT={config.agent_run_timeout:.0f}s"
    elif run.returncode not in (0, None):
        error = f"gigaagent exited {run.returncode}: {tail(run.stderr) or tail(run.stdout)}"
    return {
        "final_result": parsed["final_result"],
        "steps": parsed["trajectory"]["summary"]["step_count"],
        "is_done": parsed["is_done"] and error is None,
        "trajectory": parsed["trajectory"],
        "token_usage": parsed["token_usage"],
        "error": error,
        "harness_metadata": {
            **parsed["metadata"],
            "workspace": str(workspace),
            "returncode": run.returncode,
            "task_key": task_key,
            "endpoint": base_url,
        },
    }


async def run_gigaagent_harness(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    navigate_url = entry_url or task_url
    started_at = time.perf_counter()
    payload = await asyncio.to_thread(
        _run_gigaagent_sync,
        task,
        config=config,
        navigate_url=navigate_url,
        task_key=task_key,
    )
    duration_seconds = time.perf_counter() - started_at
    return normalize_agent_result(
        {
            **payload,
            "task_url": task_url,
            "entry_url": navigate_url,
            "warmup": {"skipped": True, "reason": "gigaagent-playwright-mcp"},
            "duration_seconds": duration_seconds,
        },
        harness=HARNESS,
    )
