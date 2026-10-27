"""Unit tests for the Claude Code and GigaAgent CLI harnesses."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import EvalConfig
from bench_eval.dataset import configs_to_goldens
from bench_eval.harness_factory import available_harnesses, get_harness_runner, normalize_harness_name
from bench_eval.harnesses import claude_code, gigaagent
from bench_eval.harnesses.cli_agent import CliRun, build_task_prompt

_MCP_SERVER = {"command": "npx", "args": ["-y", "@playwright/mcp@latest", "--headless"], "env": {"X": "1"}}
_SUFFIX = "The answer must be at most 50 words."


@pytest.fixture(autouse=True)
def _fake_cli(monkeypatch):
    monkeypatch.setattr(claude_code, "playwright_mcp_stdio_server", lambda: dict(_MCP_SERVER))
    monkeypatch.setattr(gigaagent, "playwright_mcp_stdio_server", lambda: dict(_MCP_SERVER))
    monkeypatch.setenv("CLAUDE_CODE_BIN", "claude")
    monkeypatch.setenv("GIGAAGENT_BIN", "gc-cli")
    for name in ("CLAUDE_CODE_BASE_URL", "CLAUDE_CODE_API_KEY", "GIGAAGENT_BASE_URL", "GIGAAGENT_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def _task_with_suffix(tmp_path, monkeypatch) -> str:
    """Task text exactly as the eval service builds it with extra_instructions."""
    tests_dir = tmp_path / "bench"
    (tests_dir / "tasks").mkdir(parents=True)
    (tests_dir / "build").mkdir(parents=True)
    (tests_dir / "config.json").write_text('{"test_data": {}}', encoding="utf-8")
    (tests_dir / "tasks" / "demo_task.json").write_text(
        '{"test_data": {"task": "Open %HOST% and add a book", "conditions": []}}', encoding="utf-8"
    )
    monkeypatch.setenv("EVAL_TASK_SUFFIX", _SUFFIX)
    goldens = configs_to_goldens(str(tests_dir), frontend_host="127.0.0.1:5173", track_suffix="deadbeef")
    return goldens[0].input


def _openrouter_config(**overrides) -> EvalConfig:
    values = dict(
        llm_provider="openrouter",
        llm_model="qwen/qwen3-coder-30b-a3b-instruct",
        llm_api_key="sk-test",
        llm_base_url="https://openrouter.ai/api/v1",
        agent_max_steps=7,
        agent_run_timeout=60.0,
    )
    values.update(overrides)
    return EvalConfig(**values)


# -- registration -------------------------------------------------------------


def test_aliases_normalize_to_the_new_harnesses():
    assert normalize_harness_name("claude-code") == "claude-code"
    assert normalize_harness_name("claude_code") == "claude-code"
    assert normalize_harness_name("gigaagent") == "gigaagent"
    assert normalize_harness_name("giga-agent") == "gigaagent"
    assert normalize_harness_name("gc-cli") == "gigaagent"


def test_new_harnesses_are_available_and_selectable():
    from bench_eval.harness_compat import import_harness_runner

    assert {"claude-code", "gigaagent"} <= set(available_harnesses())
    with patch("bench_eval.harness_factory.import_harness_runner", side_effect=import_harness_runner):
        with patch("bench_eval.harness_compat.ensure_harness_ready"):
            assert get_harness_runner(EvalConfig(agent_harness="claude-code")).__name__ == "run_claude_code_harness"
            assert get_harness_runner(EvalConfig(agent_harness="gigaagent")).__name__ == "run_gigaagent_harness"


def test_inspect_harness_reports_a_missing_cli_binary(monkeypatch):
    from bench_eval.harness_compat import inspect_harness

    monkeypatch.delenv("CLAUDE_CODE_BIN", raising=False)
    monkeypatch.setattr("bench_eval.harness_compat.shutil.which", lambda name: None)
    status = inspect_harness("claude-code")
    assert not status.ready
    assert any("claude on PATH" in item for item in status.missing_packages)


def test_task_prompt_matches_openhands_phrasing():
    assert build_task_prompt("  Do it  ", "http://h/t") == "Do it\n\nStart URL: http://h/t"
    assert build_task_prompt("Do it", None) == "Do it"


# -- Claude Code ----------------------------------------------------------------


def test_claude_endpoint_uses_openrouter_anthropic_api():
    assert claude_code.resolve_anthropic_endpoint(_openrouter_config()) == (
        "https://openrouter.ai/api",
        "sk-test",
    )


def test_claude_endpoint_prefers_explicit_proxy(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_BASE_URL", "http://127.0.0.1:4000/")
    monkeypatch.setenv("CLAUDE_CODE_API_KEY", "proxy-key")
    config = _openrouter_config(llm_provider="openai", llm_base_url="http://vllm:8000/v1")
    assert claude_code.resolve_anthropic_endpoint(config) == ("http://127.0.0.1:4000", "proxy-key")


def test_claude_endpoint_refuses_a_plain_openai_endpoint():
    config = _openrouter_config(llm_provider="openai", llm_base_url="http://vllm:8000/v1")
    with pytest.raises(RuntimeError, match="Anthropic Messages endpoint"):
        claude_code.resolve_anthropic_endpoint(config)


def test_claude_argv_is_headless_browser_only():
    argv = claude_code.build_claude_argv("claude", model="m", mcp_config="mcp.json", max_turns=5)
    assert argv[:2] == ["claude", "-p"]
    assert argv[argv.index("--output-format") + 1] == "stream-json"
    assert "--verbose" in argv and "--dangerously-skip-permissions" in argv
    assert argv[argv.index("--tools") + 1] == ""
    assert argv[argv.index("--mcp-config") + 1] == "mcp.json"
    assert "--strict-mcp-config" in argv
    assert argv[argv.index("--max-turns") + 1] == "5"


def test_claude_env_drops_inherited_credentials(monkeypatch):
    env = claude_code.build_claude_env(
        base_env={
            "PATH": "/bin",
            "ANTHROPIC_API_KEY": "operator-key",
            "CLAUDE_CODE_OAUTH_TOKEN": "operator-oauth",
            "CLAUDECODE": "1",
        },
        base_url="https://openrouter.ai/api",
        api_key="sk-test",
        model="m",
        config_dir="/tmp/cfg",
    )
    assert env["PATH"] == "/bin"
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in env and "CLAUDECODE" not in env
    assert env["ANTHROPIC_API_KEY"] == ""
    assert env["ANTHROPIC_AUTH_TOKEN"] == "sk-test"
    assert env["ANTHROPIC_BASE_URL"] == "https://openrouter.ai/api"
    assert env["ANTHROPIC_SMALL_FAST_MODEL"] == "m"
    assert env["CLAUDE_CONFIG_DIR"] == "/tmp/cfg"


def test_claude_env_sets_is_sandbox_only_as_root(monkeypatch):
    kwargs = dict(base_env={}, base_url="u", api_key="k", model="m", config_dir="d")
    monkeypatch.setattr(claude_code, "_running_as_root", lambda: True)
    assert claude_code.build_claude_env(**kwargs)["IS_SANDBOX"] == "1"
    monkeypatch.setattr(claude_code, "_running_as_root", lambda: False)
    assert "IS_SANDBOX" not in claude_code.build_claude_env(**kwargs)


def test_claude_mcp_config_registers_playwright():
    config = claude_code.build_claude_mcp_config()
    server = config["mcpServers"]["playwright"]
    assert server["type"] == "stdio"
    assert server["command"] == "npx"
    assert server["args"][-1] == "--headless"


def _claude_stream(*, is_error: bool = False, result: str = "Book added.") -> str:
    events = [
        {"type": "system", "subtype": "init", "tools": [], "mcp_servers": [{"name": "playwright"}]},
        {
            "type": "assistant",
            "message": {
                "id": "msg_1",
                "content": [
                    {"type": "text", "text": "Opening the page."},
                    {
                        "type": "tool_use",
                        "id": "tu_1",
                        "name": "mcp__playwright__browser_navigate",
                        "input": {"url": "http://h/t"},
                    },
                ],
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {"type": "tool_result", "tool_use_id": "tu_1", "content": [{"type": "text", "text": "ok"}]}
                ]
            },
        },
        {"type": "assistant", "message": {"id": "msg_2", "content": [{"type": "text", "text": result}]}},
        {
            "type": "result",
            "subtype": "error_max_turns" if is_error else "success",
            "is_error": is_error,
            "result": result,
            "num_turns": 2,
            "total_cost_usd": 0.01,
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 100,
                "output_tokens": 7,
            },
        },
    ]
    return "[claude-code:unrecognized_model] noise\n" + "\n".join(json.dumps(e) for e in events)


def test_parse_claude_stream_reads_answer_steps_and_tokens():
    parsed = claude_code.parse_claude_stream(_claude_stream())
    assert parsed["final_result"] == "Book added."
    assert parsed["is_done"] is True and parsed["error"] is None
    kinds = [s["kind"] for s in parsed["trajectory"]["steps"]]
    assert kinds == ["message", "action", "observation", "message"]
    assert parsed["trajectory"]["steps"][1]["tool"] == "mcp__playwright__browser_navigate"
    assert parsed["token_usage"] == {
        "prompt_tokens": 115,
        "completion_tokens": 7,
        "total_tokens": 122,
        "llm_calls": 2,
    }


def test_parse_claude_stream_marks_is_error_runs_not_done():
    parsed = claude_code.parse_claude_stream(_claude_stream(is_error=True))
    assert parsed["is_done"] is False
    assert "error_max_turns" in parsed["error"]


def test_claude_harness_delivers_the_task_suffix(tmp_path, monkeypatch):
    task = _task_with_suffix(tmp_path, monkeypatch)
    captured: dict = {}

    def fake_run(argv, *, env, cwd, timeout, stdin_text=None):
        captured.update(argv=argv, env=env, cwd=cwd, timeout=timeout, stdin=stdin_text)
        captured["mcp"] = json.loads(Path(argv[argv.index("--mcp-config") + 1]).read_text(encoding="utf-8"))
        return CliRun(0, _claude_stream(), "", False)

    monkeypatch.setattr(claude_code, "run_cli", fake_run)
    result = asyncio.run(
        claude_code.run_claude_code_harness(
            task,
            config=_openrouter_config(),
            task_url="http://127.0.0.1:5173/demo_task__deadbeef",
            task_key="demo_task",
        )
    )
    assert captured["stdin"].endswith(
        f"{_SUFFIX}\n\nStart URL: http://127.0.0.1:5173/demo_task__deadbeef"
    )
    assert captured["argv"][captured["argv"].index("--model") + 1] == "qwen/qwen3-coder-30b-a3b-instruct"
    assert captured["argv"][captured["argv"].index("--max-turns") + 1] == "7"
    assert captured["timeout"] == 60.0
    assert "playwright" in captured["mcp"]["mcpServers"]
    assert result["harness"] == "claude-code"
    assert result["final_result"] == "Book added."
    assert result["is_done"] is True
    assert result["steps"] == 4
    assert result["token_usage"]["total_tokens"] == 122
    assert "error" not in result


def test_claude_harness_reports_timeouts(monkeypatch):
    monkeypatch.setattr(claude_code, "run_cli", lambda *a, **k: CliRun(None, "", "", True))
    result = asyncio.run(claude_code.run_claude_code_harness("task", config=_openrouter_config()))
    assert result["is_done"] is False
    assert "AGENT_RUN_TIMEOUT" in result["error"]


# -- GigaAgent ------------------------------------------------------------------


def test_gigaagent_config_mirrors_the_lighteval_contract():
    config = gigaagent.build_gigaagent_config(
        base_url="https://openrouter.ai/api/v1/",
        model="m",
        max_steps=9,
        request_timeout_s=120,
        mcp_server=_MCP_SERVER,
    )
    assert config["backend"]["completions_url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert config["backend"]["chat_completion_headers"] == {"Authorization": "Bearer ${ENV:OPENAI_API_KEY}"}
    assert config["backend"]["use_ssl"] is True
    assert config["agent"]["model"] == "m" and config["agent"]["max_steps"] == 9
    assert config["logging"]["console_trace"] is True and config["logging"]["format"] == "jsonl"
    assert config["security"]["command_moderation"] == {"enabled": False, "mode": "allow"}
    server = config["mcp"]["servers"]["playwright"]
    assert server["command"] == "npx"
    # One browser for the whole task: plain stdio respawns the server per call.
    assert server["transport"] == "stream_stdio"
    assert server["persistent_session"] is True
    assert "enabled" not in server


def test_gigaagent_backend_url_resolution(monkeypatch):
    assert gigaagent.resolve_backend_base_url(_openrouter_config()) == "https://openrouter.ai/api/v1"
    assert (
        gigaagent.resolve_backend_base_url(_openrouter_config(llm_base_url=None))
        == "https://openrouter.ai/api/v1"
    )
    monkeypatch.setenv("GIGAAGENT_BASE_URL", "http://gw:8080/v1/")
    assert gigaagent.resolve_backend_base_url(_openrouter_config()) == "http://gw:8080/v1"


def _final_answer(envelope: dict) -> dict:
    return {"event": "final_answer", "answer": json.dumps(envelope)}


def _giga_stream(envelope: dict) -> str:
    events = [
        {
            "event": "dialog_message",
            "payload": {
                "type": "function_call",
                "name": "browser_navigate",
                "call_id": "c1",
                "arguments": json.dumps({"url": "http://h/t"}),
            },
        },
        {"event": "dialog_message", "payload": {"type": "function_call_output", "call_id": "c1", "output": "ok"}},
        {"event": "dialog_message", "payload": {"role": "assistant", "content": "Done."}},
        {
            "event": "dialog_message",
            "payload": {
                "type": "function_call",
                "name": "turn_finish",
                "call_id": "c2",
                "arguments": json.dumps(envelope),
            },
        },
        {"event": "dialog_message", "payload": {"type": "function_call_output", "call_id": "c2", "output": "ok"}},
        {"event": "run_usage", "usage": {"model": "m", "total": {"input": 300, "output": 40}}},
        _final_answer(envelope),
    ]
    return "starting gc-cli\n" + "\n".join(json.dumps(e) for e in events)


def test_gigaagent_answer_is_the_task_report():
    answer, error, _ = gigaagent.extract_gigaagent_answer(
        [_final_answer({"solution_type": "direct_answer", "task_report": " Book added. "})]
    )
    assert (answer, error) == ("Book added.", None)


@pytest.mark.parametrize(
    "envelope",
    [
        {"solution_type": "couldnt_solve", "task_report": "I could not."},
        {"solution_type": "partial_solution", "task_report": "half"},
        {"ok": False, "status": "step_limit"},
        {"solution_type": "direct_answer", "task_report": ""},
    ],
)
def test_gigaagent_non_answers_are_not_scored(envelope):
    answer, error, _ = gigaagent.extract_gigaagent_answer([_final_answer(envelope)])
    assert answer is None and error


def test_gigaagent_requires_exactly_one_final_answer():
    answer, error, _ = gigaagent.extract_gigaagent_answer([])
    assert answer is None and "0 final_answer" in error


def test_parse_gigaagent_stream_reads_steps_and_tokens():
    parsed = gigaagent.parse_gigaagent_stream(
        _giga_stream({"solution_type": "full_solution", "task_report": "Book added."})
    )
    assert parsed["final_result"] == "Book added."
    # turn_finish is the submission, not a browser step.
    assert [s["kind"] for s in parsed["trajectory"]["steps"]] == ["action", "observation", "message"]
    assert parsed["metadata"]["tool_calls"] == 1
    assert parsed["trajectory"]["steps"][0]["action"] == {"url": "http://h/t"}
    assert parsed["token_usage"]["prompt_tokens"] == 300
    assert parsed["token_usage"]["completion_tokens"] == 40
    assert parsed["metadata"]["solution_type"] == "full_solution"


def test_gigaagent_harness_delivers_the_task_suffix(tmp_path, monkeypatch):
    task = _task_with_suffix(tmp_path, monkeypatch)
    captured: dict = {}

    def fake_run(argv, *, env, cwd, timeout, stdin_text=None):
        captured.update(argv=argv, env=env, timeout=timeout)
        captured["config"] = json.loads(Path(argv[argv.index("--config") + 1]).read_text(encoding="utf-8"))
        return CliRun(0, _giga_stream({"solution_type": "direct_answer", "task_report": "Book added."}), "", False)

    monkeypatch.setattr(gigaagent, "run_cli", fake_run)
    result = asyncio.run(
        gigaagent.run_gigaagent_harness(
            task,
            config=_openrouter_config(),
            entry_url="http://127.0.0.1:5173/demo_task__deadbeef",
        )
    )
    prompt = captured["argv"][captured["argv"].index("-q") + 1]
    assert prompt.endswith(f"{_SUFFIX}\n\nStart URL: http://127.0.0.1:5173/demo_task__deadbeef")
    assert captured["env"]["OPENAI_API_KEY"] == "sk-test"
    assert captured["config"]["agent"]["max_steps"] == 7
    assert "playwright" in captured["config"]["mcp"]["servers"]
    assert result["harness"] == "gigaagent"
    assert result["final_result"] == "Book added."
    assert result["is_done"] is True
    assert "error" not in result


def test_gigaagent_harness_reports_nonzero_exit(monkeypatch):
    monkeypatch.setattr(gigaagent, "run_cli", lambda *a, **k: CliRun(2, "", "boom", False))
    result = asyncio.run(gigaagent.run_gigaagent_harness("task", config=_openrouter_config()))
    assert result["is_done"] is False
    assert "exited 2" in result["error"] and "boom" in result["error"]
