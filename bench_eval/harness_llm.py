"""LLM client helpers for non-browser-use harness adapters."""

from __future__ import annotations

import os
from typing import Any

from bench_eval.config import EvalConfig
from bench_eval.llm_factory import (
    LLM_ACCEPT_ENCODING_HEADERS,
    build_llm_http_client,
    build_llm_sync_http_client,
)
from bench_eval.node_bin import node_path_env, resolve_npx_command
from bench_eval.playwright_mcp_preflight import resolve_playwright_mcp_executable


def litellm_model_name(config: EvalConfig) -> str:
    """Map eval config to a LiteLLM model id (OpenHands SDK)."""
    provider = config.llm_provider.lower()
    if provider == "openrouter":
        return f"openrouter/{config.llm_model}"
    if provider == "gigachat":
        return f"gigachat/{config.llm_model}"
    if provider == "ollama":
        return f"ollama/{config.llm_model}"
    return f"openai/{config.llm_model}"


def create_langchain_chat_model(config: EvalConfig) -> Any:
    """Return a LangChain chat model for DeepAgents and similar harnesses."""
    from langchain_openai import ChatOpenAI

    kwargs: dict[str, Any] = {
        "model": config.llm_model,
        "temperature": config.llm_temperature,
        "max_retries": config.llm_max_retries,
        "timeout": config.agent_llm_timeout,
    }
    if config.llm_api_key:
        kwargs["api_key"] = config.llm_api_key
    if config.llm_base_url:
        kwargs["base_url"] = config.llm_base_url
    kwargs["default_headers"] = dict(LLM_ACCEPT_ENCODING_HEADERS)
    kwargs["http_async_client"] = build_llm_http_client()
    kwargs["http_client"] = build_llm_sync_http_client()
    return ChatOpenAI(**kwargs)


def _openhands_llm_kwargs(cls: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    fields = getattr(cls, "model_fields", None) or getattr(cls, "__fields__", None)
    if not fields:
        return kwargs
    return {key: value for key, value in kwargs.items() if key in fields}


def create_openhands_llm(config: EvalConfig) -> Any:
    """Return an OpenHands SDK LLM configured from eval env."""
    from bench_eval.openhands_browser_patch import prepare_openhands_runtime

    prepare_openhands_runtime()
    from openhands.sdk.llm import LLM
    from pydantic import SecretStr

    api_key = config.llm_api_key or os.getenv("LLM_API_KEY") or ""
    kwargs: dict[str, Any] = {
        "usage_id": "agent",
        "model": litellm_model_name(config),
        "api_key": SecretStr(api_key),
        "temperature": config.llm_temperature,
        "num_retries": config.llm_max_retries,
        "extra_headers": dict(LLM_ACCEPT_ENCODING_HEADERS),
        "default_headers": dict(LLM_ACCEPT_ENCODING_HEADERS),
        "httpx_client": build_llm_http_client(),
        "http_client": build_llm_sync_http_client(),
    }
    if config.llm_base_url:
        kwargs["base_url"] = config.llm_base_url
    return LLM(**_openhands_llm_kwargs(LLM, kwargs))


def _env_truthy(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def default_playwright_mcp_args(*, executable_path: str | None = None) -> list[str]:
    """CLI args for @playwright/mcp aligned with the Python preflight."""
    args = [
        "-y",
        "@playwright/mcp@latest",
        "--headless",
    ]
    if _env_truthy("AGENT_CHROMIUM_NO_SANDBOX", default=True):
        args.append("--no-sandbox")
    if executable_path:
        args.extend(["--executable-path", executable_path])
    else:
        args.extend(["--browser", "chrome"])
    return args


def playwright_mcp_connection() -> dict[str, Any]:
    """Stdio Playwright MCP connection used by the DeepAgents harness."""
    command = resolve_npx_command() or os.getenv("PLAYWRIGHT_MCP_COMMAND", "npx")
    executable = (
        os.getenv("PLAYWRIGHT_MCP_EXECUTABLE_PATH", "").strip()
        or resolve_playwright_mcp_executable()
        or None
    )
    args_raw = os.getenv("PLAYWRIGHT_MCP_ARGS", "").strip()
    if args_raw:
        args = args_raw.split()
    else:
        args = default_playwright_mcp_args(executable_path=executable)
    env = node_path_env()
    browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if browsers_path:
        env["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    if executable:
        env["PLAYWRIGHT_MCP_EXECUTABLE_PATH"] = executable
    else:
        env["PLAYWRIGHT_MCP_BROWSER"] = "chrome"
    env["PLAYWRIGHT_MCP_HEADLESS"] = "true"
    timeout = os.getenv("PLAYWRIGHT_MCP_TIMEOUT", "120000").strip()
    if timeout:
        env["PLAYWRIGHT_TIMEOUT"] = timeout
    connection: dict[str, Any] = {
        "command": command,
        "args": args,
        "transport": "stdio",
        "env": env,
    }
    return connection
