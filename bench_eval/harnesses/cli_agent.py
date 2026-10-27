"""Shared plumbing for harnesses that drive an external agent CLI.

Claude Code and GigaAgent are both headless command lines: the eval writes a
config file, hands the task text to the binary, and reads back a JSON event
stream. Both get the browser through the same Playwright MCP server the
DeepAgents harness uses (:func:`bench_eval.harness_llm.playwright_mcp_connection`).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from bench_eval.harness_llm import playwright_mcp_connection

#: Name the Playwright MCP server is registered under in every CLI config.
PLAYWRIGHT_MCP_SERVER_NAME = "playwright"


def build_task_prompt(task: str, navigate_url: Optional[str]) -> str:
    """Task text exactly as the OpenHands harness phrases it.

    ``task`` already carries ``EVAL_TASK_SUFFIX`` (appended in
    :mod:`bench_eval.dataset`), so caller constraints reach the agent here.
    """
    prompt = task.strip()
    if navigate_url:
        prompt = f"{prompt}\n\nStart URL: {navigate_url}"
    return prompt


def playwright_mcp_stdio_server() -> dict[str, Any]:
    """The Playwright MCP server as a plain ``command``/``args``/``env`` mapping."""
    connection = playwright_mcp_connection()
    return {
        "command": str(connection["command"]),
        "args": [str(arg) for arg in connection.get("args") or []],
        "env": {k: str(v) for k, v in (connection.get("env") or {}).items() if v is not None},
    }


def resolve_cli_binary(env_var: str, default: str) -> str:
    """Return the CLI to launch: ``$env_var`` if set, else ``default`` on PATH."""
    configured = os.getenv(env_var, "").strip()
    if configured:
        return configured
    found = shutil.which(default)
    if found is None:
        raise RuntimeError(
            f"{default!r} is not on PATH; install it or point {env_var} at the binary."
        )
    return found


def iter_json_lines(text: str) -> Iterable[dict[str, Any]]:
    """Yield every JSON object line of a JSONL stream, skipping log noise."""
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


@dataclass(frozen=True)
class CliRun:
    returncode: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool


def run_cli(
    argv: list[str],
    *,
    env: dict[str, str],
    cwd: str,
    timeout: float,
    stdin_text: Optional[str] = None,
) -> CliRun:
    """Run one CLI invocation to completion, never raising on a timeout."""
    try:
        completed = subprocess.run(
            argv,
            input=stdin_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            env=env,
            timeout=timeout if timeout and timeout > 0 else None,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        def _text(value: Any) -> str:
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            return value or ""

        return CliRun(None, _text(exc.stdout), _text(exc.stderr), True)
    return CliRun(completed.returncode, completed.stdout or "", completed.stderr or "", False)


def tail(text: str, limit: int = 2000) -> str:
    text = text.strip()
    return text if len(text) <= limit else "..." + text[-limit:]
