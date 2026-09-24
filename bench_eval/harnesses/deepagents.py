"""DeepAgents harness: LangGraph agent with Playwright MCP browser tools."""

from __future__ import annotations

import asyncio
import contextlib
import time
from typing import Any, Optional

from bench_eval.config import EvalConfig
from bench_eval.harness_llm import create_langchain_chat_model, playwright_mcp_connection
from bench_eval.harness_trajectory import serialize_message_trajectory
from bench_eval.harnesses.base import AgentRunResult, normalize_agent_result
from bench_eval.token_usage import extract_token_usage_from_messages


def _extract_final_text(messages: list[Any]) -> Optional[str]:
    for message in reversed(messages):
        role = getattr(message, "type", None) or getattr(message, "role", None)
        if role not in {"ai", "assistant"}:
            continue
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()
    return None


def _count_tool_steps(messages: list[Any]) -> int:
    return sum(
        1
        for message in messages
        if (getattr(message, "type", None) or getattr(message, "role", None))
        in {"tool", "ai", "assistant"}
    )


def _progress_hint(messages: list[Any]) -> str:
    if not messages:
        return ""
    message = messages[-1]
    role = getattr(message, "type", None) or getattr(message, "role", None) or "?"
    if role == "tool":
        name = getattr(message, "name", None) or "tool"
        return f" last={name}"
    if role in {"ai", "assistant"}:
        tool_calls = getattr(message, "tool_calls", None) or []
        if tool_calls:
            names: list[str] = []
            for call in tool_calls[:3]:
                if isinstance(call, dict):
                    names.append(str(call.get("name") or call.get("id") or "?"))
                else:
                    names.append(str(getattr(call, "name", None) or "?"))
            return f" last=ai→{','.join(names)}"
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            snippet = content.strip().replace("\n", " ")[:60]
            return f" last=ai:{snippet!r}"
    return f" last={role}"


def _unwrap_agent_exception(exc: BaseException) -> BaseException:
    current = exc
    seen: set[int] = set()
    while id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, BaseExceptionGroup) and current.exceptions:
            if len(current.exceptions) == 1:
                current = current.exceptions[0]
                continue
            for sub in current.exceptions:
                root = _unwrap_agent_exception(sub)
                if isinstance(root, TimeoutError) and (
                    "AGENT_RUN_IDLE_TIMEOUT" in str(root)
                    or "AGENT_RUN_TIMEOUT" in str(root)
                ):
                    return root
            current = current.exceptions[0]
            continue
        break
    return current


def format_agent_exception(exc: BaseException) -> str:
    root = _unwrap_agent_exception(exc)
    message = str(root).strip()
    if message:
        return f"{type(root).__name__}: {message}"
    return type(root).__name__


def _select_task_exception(done: set[asyncio.Task[Any]]) -> BaseException | None:
    errors: list[BaseException] = []
    for task in done:
        if task.cancelled():
            continue
        exc = task.exception()
        if exc is not None:
            errors.append(exc)
    if not errors:
        return None
    for exc in errors:
        root = _unwrap_agent_exception(exc)
        if isinstance(root, TimeoutError) and (
            "AGENT_RUN_IDLE_TIMEOUT" in str(root)
            or "AGENT_RUN_TIMEOUT" in str(root)
        ):
            return root
    return _unwrap_agent_exception(errors[0])


async def _invoke_deep_agent(
    agent: Any,
    *,
    prompt: str,
    recursion_limit: int,
    idle_timeout: float = 0.0,
    state_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    input_state = {"messages": [{"role": "user", "content": prompt}]}
    run_config = {"recursion_limit": recursion_limit}
    progress = {"count": 0, "at": time.perf_counter()}

    async def _consume() -> dict[str, Any]:
        final_state: dict[str, Any] | None = None
        last_message_count = 0
        invoke_started = time.perf_counter()
        async for state in agent.astream(
            input_state,
            config=run_config,
            stream_mode="values",
        ):
            final_state = state
            if state_snapshot is not None:
                state_snapshot["state"] = state
            messages = list(state.get("messages") or [])
            count = len(messages)
            if count != last_message_count:
                elapsed = time.perf_counter() - invoke_started
                hint = _progress_hint(messages)
                print(
                    f"[deepagents] progress messages={count} elapsed={elapsed:.0f}s{hint}",
                    flush=True,
                )
                last_message_count = count
                progress["count"] = count
                progress["at"] = time.perf_counter()
        if final_state is None:
            raise RuntimeError("deepagents agent finished without state")
        if state_snapshot is not None:
            state_snapshot["state"] = final_state
        return final_state

    async def _watch_idle() -> None:
        if idle_timeout <= 0:
            return
        poll_interval = min(5.0, max(0.05, idle_timeout / 4))
        while True:
            await asyncio.sleep(poll_interval)
            idle_for = time.perf_counter() - progress["at"]
            if idle_for >= idle_timeout:
                raise TimeoutError(
                    f"deepagents agent exceeded AGENT_RUN_IDLE_TIMEOUT="
                    f"{idle_timeout:.0f}s (messages={progress['count']}, "
                    f"recursion_limit={recursion_limit})"
                )

    consume_task = asyncio.create_task(_consume())
    idle_task = asyncio.create_task(_watch_idle()) if idle_timeout > 0 else None
    pending = {consume_task}
    if idle_task is not None:
        pending.add(idle_task)

    done, still_running = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
    for task in still_running:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    if consume_task in done and not consume_task.cancelled():
        exc = consume_task.exception()
        if exc is None:
            return consume_task.result()

    selected = _select_task_exception(done)
    if selected is not None:
        raise selected

    raise RuntimeError("deepagents agent finished without state")


async def _invoke_deep_agent_with_run_timeout(
    agent: Any,
    *,
    prompt: str,
    recursion_limit: int,
    run_timeout: float,
    idle_timeout: float = 0.0,
    state_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return await asyncio.wait_for(
            _invoke_deep_agent(
                agent,
                prompt=prompt,
                recursion_limit=recursion_limit,
                idle_timeout=idle_timeout,
                state_snapshot=state_snapshot,
            ),
            timeout=run_timeout,
        )
    except TimeoutError as exc:
        if "AGENT_RUN_IDLE_TIMEOUT" in str(exc):
            raise
        raise TimeoutError(
            f"deepagents agent exceeded AGENT_RUN_TIMEOUT={run_timeout:.0f}s "
            f"(recursion_limit={recursion_limit})"
        ) from exc


def _build_deepagents_result(
    *,
    messages: list[Any],
    config: EvalConfig,
    task_url: Optional[str],
    navigate_url: Optional[str],
    started_at: float,
    tools_count: int,
    recursion_limit: int,
    run_timeout: float,
    idle_timeout: float,
    task_key: Optional[str],
    error: Optional[str] = None,
) -> AgentRunResult:
    duration_seconds = time.perf_counter() - started_at
    final = _extract_final_text(messages)
    trajectory = serialize_message_trajectory(
        messages,
        harness="deepagents",
        extra={"mcp_tool_count": tools_count},
    )
    steps = _count_tool_steps(messages)
    payload: dict[str, Any] = {
        "final_result": final,
        "steps": steps,
        "task_url": task_url,
        "entry_url": navigate_url,
        "warmup": {"skipped": True, "reason": "playwright-mcp"},
        "is_done": bool(final) and error is None,
        "duration_seconds": duration_seconds,
        "trajectory": trajectory,
        "history": messages,
        "token_usage": extract_token_usage_from_messages(messages),
        "harness_metadata": {
            "mcp": "playwright",
            "recursion_limit": recursion_limit,
            "run_timeout": run_timeout,
            "idle_timeout": idle_timeout,
            "task_key": task_key,
        },
    }
    if error:
        payload["error"] = error
        if not final:
            payload["final_result"] = error
    return normalize_agent_result(payload, harness="deepagents")


async def run_deepagents_harness(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    from bench_eval.deepagents_import import import_create_deep_agent
    from langchain_mcp_adapters.client import MultiServerMCPClient

    create_deep_agent = import_create_deep_agent()

    navigate_url = entry_url or task_url
    prompt = task.strip()
    if navigate_url:
        prompt = f"{prompt}\n\nStart URL: {navigate_url}"

    started_at = time.perf_counter()
    print("[deepagents] loading Playwright MCP tools", flush=True)
    mcp_client = MultiServerMCPClient({"playwright": playwright_mcp_connection()})
    tools = await asyncio.wait_for(
        mcp_client.get_tools(),
        timeout=config.agent_browser_start_timeout,
    )
    print(f"[deepagents] loaded {len(tools)} MCP tools", flush=True)

    model = create_langchain_chat_model(config)
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=(
            "You are a web browsing agent for benchmark evaluation. "
            "Use Playwright browser tools to complete the user's task in a real browser. "
            "Navigate to the provided start URL first when given."
        ),
    )

    recursion_limit = max(config.agent_max_steps * 2, 20)
    run_timeout = config.agent_run_timeout
    idle_timeout = config.agent_run_idle_timeout
    idle_suffix = (
        f" idle_timeout={idle_timeout:.0f}s" if idle_timeout > 0 else ""
    )
    print(
        f"[deepagents] invoke recursion_limit={recursion_limit} "
        f"run_timeout={run_timeout:.0f}s llm_timeout={config.agent_llm_timeout:.0f}s"
        f"{idle_suffix}",
        flush=True,
    )
    state_snapshot: dict[str, Any] = {}
    try:
        result = await _invoke_deep_agent_with_run_timeout(
            agent,
            prompt=prompt,
            recursion_limit=recursion_limit,
            run_timeout=run_timeout,
            idle_timeout=idle_timeout,
            state_snapshot=state_snapshot,
        )
    except Exception as exc:
        error_text = format_agent_exception(exc)
        print(f"[deepagents] agent error: {error_text}", flush=True)
        partial = state_snapshot.get("state") or {}
        messages = list(partial.get("messages") or [])
        return _build_deepagents_result(
            messages=messages,
            config=config,
            task_url=task_url,
            navigate_url=navigate_url,
            started_at=started_at,
            tools_count=len(tools),
            recursion_limit=recursion_limit,
            run_timeout=run_timeout,
            idle_timeout=idle_timeout,
            task_key=task_key,
            error=error_text,
        )

    messages = list(result.get("messages") or [])
    return _build_deepagents_result(
        messages=messages,
        config=config,
        task_url=task_url,
        navigate_url=navigate_url,
        started_at=started_at,
        tools_count=len(tools),
        recursion_limit=recursion_limit,
        run_timeout=run_timeout,
        idle_timeout=idle_timeout,
        task_key=task_key,
    )
