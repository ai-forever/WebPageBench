"""Claude Code harness: headless ``claude -p`` with Playwright MCP browser tools.

Claude Code speaks the Anthropic Messages API only. OpenRouter serves that API
at ``https://openrouter.ai/api/v1/messages`` for its catalogue (non-Anthropic
models included), so an OpenRouter run needs no proxy. Any other provider must
be put behind an Anthropic-compatible endpoint (for example a LiteLLM proxy)
and named in ``CLAUDE_CODE_BASE_URL``.

Built-in tools are disabled (``--tools ""``): like OpenHands with its
BrowserToolSet, the agent acts on the page only through the browser.
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

HARNESS = "claude-code"
OPENROUTER_ANTHROPIC_BASE_URL = "https://openrouter.ai/api"

#: Inherited variables that would make the child authenticate as whoever runs
#: the eval (a logged-in Claude Code, or a parent Claude Code session) instead
#: of with the key configured for this run.
_INHERITED_PREFIXES = ("ANTHROPIC_", "CLAUDE_", "CLAUDECODE")


def resolve_anthropic_endpoint(config: EvalConfig) -> tuple[str, str]:
    """Return ``(base_url, api_key)`` of the Anthropic-compatible endpoint."""
    api_key = (
        os.getenv("CLAUDE_CODE_API_KEY", "").strip()
        or config.llm_api_key
        or ""
    )
    explicit = os.getenv("CLAUDE_CODE_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/"), api_key
    base_url = (config.llm_base_url or "").lower()
    if config.llm_provider.lower() == "openrouter" or "openrouter.ai" in base_url:
        return OPENROUTER_ANTHROPIC_BASE_URL, api_key
    raise RuntimeError(
        "claude-code needs an Anthropic Messages endpoint. OpenRouter serves one "
        "(LLM_PROVIDER=openrouter); for any other provider run an Anthropic-compatible "
        "proxy (e.g. LiteLLM) and set CLAUDE_CODE_BASE_URL (and CLAUDE_CODE_API_KEY)."
    )


def build_claude_mcp_config() -> dict[str, Any]:
    server = playwright_mcp_stdio_server()
    return {"mcpServers": {PLAYWRIGHT_MCP_SERVER_NAME: {"type": "stdio", **server}}}


def build_claude_argv(binary: str, *, model: str, mcp_config: str, max_turns: int) -> list[str]:
    return [
        binary,
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
        "--no-session-persistence",
        "--model",
        model,
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        mcp_config,
        "--setting-sources",
        "",
        "--max-turns",
        str(max(1, int(max_turns))),
    ]


def _running_as_root() -> bool:
    geteuid = getattr(os, "geteuid", None)
    return bool(geteuid is not None and geteuid() == 0)


def build_claude_env(
    *,
    base_env: dict[str, str],
    base_url: str,
    api_key: str,
    model: str,
    config_dir: str,
) -> dict[str, str]:
    env = {
        key: value
        for key, value in base_env.items()
        if not key.startswith(_INHERITED_PREFIXES)
    }
    env.update(
        {
            "ANTHROPIC_BASE_URL": base_url,
            # OpenRouter (and LiteLLM) take a bearer token; an empty
            # ANTHROPIC_API_KEY keeps Claude Code from preferring x-api-key.
            "ANTHROPIC_AUTH_TOKEN": api_key,
            "ANTHROPIC_API_KEY": "",
            "ANTHROPIC_MODEL": model,
            # Background calls (titles, summaries) default to a Haiku id the
            # endpoint may not serve; keep every call on the evaluated model.
            "ANTHROPIC_SMALL_FAST_MODEL": model,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
            "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
            "CLAUDE_CONFIG_DIR": config_dir,
            "DISABLE_TELEMETRY": "1",
            "DISABLE_AUTOUPDATER": "1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        }
    )
    if _running_as_root():
        # --dangerously-skip-permissions refuses to run as root otherwise.
        env["IS_SANDBOX"] = "1"
    return env


def _block_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text") or ""))
        return "\n".join(p for p in parts if p)
    return ""


def parse_claude_stream(stdout: str) -> dict[str, Any]:
    """Turn ``--output-format stream-json`` into the harness result fields."""
    steps: list[dict[str, Any]] = []
    result_event: Optional[dict[str, Any]] = None
    last_text: Optional[str] = None
    message_ids: set[str] = set()
    tool_calls = 0
    for event in iter_json_lines(stdout):
        etype = event.get("type")
        if etype == "result":
            result_event = event
            continue
        if etype not in {"assistant", "user"}:
            continue
        message = event.get("message") or {}
        if etype == "assistant" and message.get("id"):
            message_ids.add(str(message["id"]))
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text" and etype == "assistant":
                text = str(block.get("text") or "").strip()
                if text:
                    last_text = text
                    steps.append(
                        {"index": len(steps), "kind": "message", "source": "agent", "content": text}
                    )
            elif btype == "tool_use":
                tool_calls += 1
                steps.append(
                    {
                        "index": len(steps),
                        "kind": "action",
                        "tool": block.get("name"),
                        "action": block.get("input"),
                        "id": block.get("id"),
                    }
                )
            elif btype == "tool_result":
                steps.append(
                    {
                        "index": len(steps),
                        "kind": "observation",
                        "tool_use_id": block.get("tool_use_id"),
                        "is_error": bool(block.get("is_error")),
                        "content": tail(_block_text(block.get("content")), 4000),
                    }
                )

    final: Optional[str] = None
    error: Optional[str] = None
    usage = normalize_token_usage(None)
    metadata: dict[str, Any] = {"tool_calls": tool_calls}
    if result_event is not None:
        raw = result_event.get("result")
        if isinstance(raw, str) and raw.strip():
            final = raw.strip()
        if result_event.get("is_error") is True:
            subtype = result_event.get("subtype")
            error = f"claude-code reported is_error (subtype={subtype!r})"
        raw_usage = result_event.get("usage") or {}
        prompt_tokens = sum(
            int(raw_usage.get(key) or 0)
            for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
        )
        completion_tokens = int(raw_usage.get("output_tokens") or 0)
        usage = normalize_token_usage(
            {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "llm_calls": len(message_ids),
            }
        )
        metadata.update(
            {
                "subtype": result_event.get("subtype"),
                "num_turns": result_event.get("num_turns"),
                "total_cost_usd": result_event.get("total_cost_usd"),
                "stop_reason": result_event.get("stop_reason"),
            }
        )
    elif last_text:
        final = last_text
    return {
        "final_result": final,
        "is_done": result_event is not None and error is None and final is not None,
        "error": error,
        "token_usage": usage,
        "trajectory": {
            "harness": HARNESS,
            "summary": {"step_count": len(steps)},
            "steps": steps,
        },
        "metadata": metadata,
    }


def _run_claude_code_sync(
    task: str,
    *,
    config: EvalConfig,
    navigate_url: Optional[str],
    task_key: Optional[str],
) -> dict[str, Any]:
    base_url, api_key = resolve_anthropic_endpoint(config)
    binary = resolve_cli_binary("CLAUDE_CODE_BIN", "claude")
    prompt = build_task_prompt(task, navigate_url)

    workspace = Path(tempfile.mkdtemp(prefix="dab-claude-code-"))
    config_dir = workspace / "claude-config"
    config_dir.mkdir()
    mcp_path = workspace / "mcp.json"
    mcp_path.write_text(json.dumps(build_claude_mcp_config()), encoding="utf-8")

    argv = build_claude_argv(
        binary,
        model=config.llm_model,
        mcp_config=str(mcp_path),
        max_turns=config.agent_max_steps,
    )
    env = build_claude_env(
        base_env=dict(os.environ),
        base_url=base_url,
        api_key=api_key,
        model=config.llm_model,
        config_dir=str(config_dir),
    )
    print(
        f"[claude-code] run model={config.llm_model} endpoint={base_url} "
        f"max_turns={config.agent_max_steps}",
        flush=True,
    )
    run = run_cli(
        argv,
        env=env,
        cwd=str(workspace),
        timeout=config.agent_run_timeout,
        stdin_text=prompt,
    )
    (workspace / "stream.jsonl").write_text(run.stdout, encoding="utf-8")
    parsed = parse_claude_stream(run.stdout)
    error = parsed["error"]
    if run.timed_out:
        error = f"claude-code exceeded AGENT_RUN_TIMEOUT={config.agent_run_timeout:.0f}s"
    elif run.returncode not in (0, None) and error is None:
        error = f"claude-code exited {run.returncode}: {tail(run.stderr) or tail(run.stdout)}"
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


async def run_claude_code_harness(
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
        _run_claude_code_sync,
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
            "warmup": {"skipped": True, "reason": "claude-code-playwright-mcp"},
            "duration_seconds": duration_seconds,
        },
        harness=HARNESS,
    )
