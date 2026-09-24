"""Tests for syncing eval LLM env into Ouroboros full harness modes."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.ouroboros_llm_sync import (
    OUROBOROS_AUXILIARY_MODEL_KEYS,
    build_ouroboros_llm_settings,
    collect_ouroboros_model_slots,
    merge_ouroboros_llm_env,
    ouroboros_httpx_hook_dir,
    ouroboros_model_id,
    sync_ouroboros_server_llm,
    validate_bench_safe_ouroboros_models,
)


def test_ouroboros_model_id_openrouter_frontier_models():
    assert ouroboros_model_id("openrouter", "openai/gpt-5.5") == "openai/gpt-5.5"
    assert ouroboros_model_id("openrouter", "anthropic/claude-opus-4.7") == "anthropic/claude-opus-4.7"
    assert ouroboros_model_id("openrouter", "z-ai/glm-5.1") == "z-ai/glm-5.1"


def test_ouroboros_model_id_gigachat():
    assert ouroboros_model_id("gigachat", "GigaChat-3-Ultra") == "gigachat::GigaChat-3-Ultra"


def test_build_ouroboros_llm_settings_gigachat_maps_token_to_credentials():
    settings = build_ouroboros_llm_settings(
        {
            "LLM_PROVIDER": "gigachat",
            "LLM_MODEL": "GigaChat-3-Ultra",
            "GIGACHAT_TOKEN": "auth-key",
            "GIGACHAT_BASE_URL": "https://gigachat.ift.sberdevices.ru/v1",
            "LLM_MAX_RETRIES": "5",
            "EVAL_MOCK": "bench",
        }
    )
    assert settings["OUROBOROS_MODEL"] == "gigachat::GigaChat-3-Ultra"
    assert settings["GIGACHAT_CREDENTIALS"] == "auth-key"
    assert settings["GIGACHAT_BASE_URL"] == "https://gigachat.ift.sberdevices.ru/v1"
    assert settings["OUROBOROS_TRANSIENT_RETRY_MAX"] == "5"
    for key in OUROBOROS_AUXILIARY_MODEL_KEYS:
        assert settings[key] == "gigachat::GigaChat-3-Ultra"


def test_build_ouroboros_llm_settings_openrouter():
    settings = build_ouroboros_llm_settings(
        {
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": "google/gemini-2.5-flash",
            "OPENROUTER_API_KEY": "sk-or-v1-test",
            "EVAL_MOCK": "bench",
        }
    )
    assert settings["OUROBOROS_MODEL"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_MODEL_HEAVY"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_MODEL_LIGHT"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_MODEL_FALLBACKS"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_REVIEW_MODELS"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_SCOPE_REVIEW_MODELS"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_SCOPE_REVIEW_MODEL"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_MODEL_DEEP_SELF_REVIEW"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_WEBSEARCH_MODEL"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_ALLOW_MUTATIVE_SUBAGENTS"] == "false"
    assert settings["OPENROUTER_API_KEY"] == "sk-or-v1-test"
    assert "OPENROUTER_BASE_URL" not in settings


def test_build_ouroboros_llm_settings_openrouter_forwards_proxy_base_url():
    settings = build_ouroboros_llm_settings(
        {
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": "google/gemini-2.5-flash",
            "OPENROUTER_API_KEY": "sk-or-v1-test",
            "LLM_BASE_URL": "https://proxy.example/api/v1",
            "EVAL_MOCK": "bench",
        }
    )
    assert settings["OPENROUTER_BASE_URL"] == "https://proxy.example/api/v1"
    assert settings["OPENAI_BASE_URL"] == "https://proxy.example/api/v1"


def test_build_ouroboros_llm_settings_openrouter_key_only_uses_ouroboros_defaults():
    settings = build_ouroboros_llm_settings(
        {
            "LLM_PROVIDER": "openrouter",
            "OPENROUTER_API_KEY": "sk-or-v1-test",
            "EVAL_MOCK": "bench",
        }
    )
    assert settings["OUROBOROS_MODEL"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_MODEL_FALLBACKS"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_WEBSEARCH_MODEL"] == "google/gemini-2.5-flash"
    assert settings["OPENROUTER_API_KEY"] == "sk-or-v1-test"


def test_validate_bench_safe_ouroboros_models_blocks_expensive():
    with pytest.raises(ValueError, match="Blocked model family"):
        validate_bench_safe_ouroboros_models(
            {"OUROBOROS_REVIEW_MODELS": "anthropic/claude-opus-4.8"},
            env={"EVAL_MOCK": "bench"},
        )


def test_validate_bench_safe_ouroboros_models_allows_explicit_frontier_llm_model():
    env = {
        "LLM_PROVIDER": "openrouter",
        "LLM_MODEL": "openai/gpt-5.5",
        "OPENROUTER_API_KEY": "sk-or-v1-test",
        "EVAL_MOCK": "bench",
        "DAB_OUROBOROS_BENCH_LOCK": "1",
    }
    settings = build_ouroboros_llm_settings(env)
    validate_bench_safe_ouroboros_models(settings, env=env)
    assert settings["OUROBOROS_MODEL"] == "openai/gpt-5.5"
    assert settings["OUROBOROS_REVIEW_MODELS"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_SCOPE_REVIEW_MODELS"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_MODEL_DEEP_SELF_REVIEW"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_WEBSEARCH_MODEL"] == "openai/gpt-5.5"


def test_build_ouroboros_llm_settings_openrouter_deepseek_keeps_cheap_review():
    settings = build_ouroboros_llm_settings(
        {
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": "deepseek/deepseek-v4-flash",
            "OPENROUTER_API_KEY": "sk-or-v1-test",
            "EVAL_MOCK": "bench",
        }
    )
    assert settings["OUROBOROS_MODEL"] == "deepseek/deepseek-v4-flash"
    assert settings["OUROBOROS_REVIEW_MODELS"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_SCOPE_REVIEW_MODEL"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_WEBSEARCH_MODEL"] == "deepseek/deepseek-v4-flash"


def test_build_ouroboros_llm_settings_openrouter_claude_opus():
    settings = build_ouroboros_llm_settings(
        {
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": "anthropic/claude-opus-4.7",
            "OPENROUTER_API_KEY": "sk-or-v1-test",
            "EVAL_MOCK": "bench",
            "DAB_OUROBOROS_BENCH_LOCK": "1",
        }
    )
    assert settings["OUROBOROS_MODEL"] == "anthropic/claude-opus-4.7"
    assert settings["OUROBOROS_REVIEW_MODELS"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_SCOPE_REVIEW_MODEL"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_WEBSEARCH_MODEL"] == "anthropic/claude-opus-4.7"


def test_build_ouroboros_llm_settings_openrouter_glm():
    settings = build_ouroboros_llm_settings(
        {
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": "z-ai/glm-5.1",
            "OPENROUTER_API_KEY": "sk-or-v1-test",
            "EVAL_MOCK": "bench",
            "DAB_OUROBOROS_BENCH_LOCK": "1",
        }
    )
    assert settings["OUROBOROS_MODEL"] == "z-ai/glm-5.1"
    assert settings["OUROBOROS_MODEL_HEAVY"] == "z-ai/glm-5.1"
    assert settings["OUROBOROS_REVIEW_MODELS"] == "google/gemini-2.5-flash"
    assert settings["OUROBOROS_MODEL_DEEP_SELF_REVIEW"] == "google/gemini-2.5-flash"


def test_merge_ouroboros_llm_env_replaces_root_pythonpath():
    merged = merge_ouroboros_llm_env(
        {
            "PYTHONPATH": "/repo/lib/src:/repo",
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": "google/gemini-2.5-flash",
            "OPENROUTER_API_KEY": "sk-or-v1-test",
            "EVAL_MOCK": "bench",
        }
    )
    hook = str(ouroboros_httpx_hook_dir())
    assert merged["PYTHONPATH"] == hook
    assert "/repo" not in merged["PYTHONPATH"].replace(hook, "")


def test_merge_ouroboros_llm_env_injects_model_slots():
    merged = merge_ouroboros_llm_env(
        {
            "PATH": "/bin",
            "LLM_PROVIDER": "gigachat",
            "LLM_MODEL": "GigaChat-3-Ultra",
            "GIGACHAT_TOKEN": "auth-key",
            "EVAL_MOCK": "bench",
        }
    )
    assert merged["OUROBOROS_MODEL"] == "gigachat::GigaChat-3-Ultra"
    assert merged["GIGACHAT_CREDENTIALS"] == "auth-key"
    assert merged["OUROBOROS_WEBSEARCH_MODEL"] == "gigachat::GigaChat-3-Ultra"
    assert merged["PATH"] == "/bin"
    assert merged["PYTHONPATH"] == str(ouroboros_httpx_hook_dir())
    assert merged["PYTHONPATH"].endswith("ouroboros_httpx_hook")


def test_sync_ouroboros_server_llm_posts_settings():
    client = MagicMock()
    client.apply_settings = MagicMock(return_value={"ok": True})
    settings = sync_ouroboros_server_llm(
        client,
        env={
            "LLM_PROVIDER": "gigachat",
            "LLM_MODEL": "GigaChat-3-Ultra",
            "GIGACHAT_TOKEN": "auth-key",
            "EVAL_MOCK": "bench",
        },
    )
    client.apply_settings.assert_called_once()
    assert settings["OUROBOROS_MODEL"] == "gigachat::GigaChat-3-Ultra"


def test_shell_export_lines_openrouter():
    from bench_eval.ouroboros_llm_sync import shell_export_lines

    lines = shell_export_lines(
        {
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": "google/gemini-2.5-flash",
            "OPENROUTER_API_KEY": "sk-or-v1-test",
            "EVAL_MOCK": "bench",
        }
    )
    joined = "\n".join(lines)
    assert "export OPENROUTER_API_KEY=" in joined
    assert "export OUROBOROS_MODEL=" in joined
    assert "export OUROBOROS_WEBSEARCH_MODEL=" in joined


def test_validate_ouroboros_llm_settings_requires_openrouter_key():
    from bench_eval.ouroboros_llm_sync import validate_ouroboros_llm_settings

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        validate_ouroboros_llm_settings(
            {
                "LLM_PROVIDER": "openrouter",
                "LLM_MODEL": "google/gemini-2.5-flash",
                "EVAL_MOCK": "bench",
            }
        )


def test_run_ouroboros_full_task_syncs_llm_before_api(tmp_path, monkeypatch):
    from dataclasses import replace

    from bench_eval.ouroboros_client import run_ouroboros_full_task
    from bench_eval.ouroboros_config import load_ouroboros_harness_config

    monkeypatch.setenv("LLM_PROVIDER", "gigachat")
    monkeypatch.setenv("LLM_MODEL", "GigaChat-3-Ultra")
    monkeypatch.setenv("GIGACHAT_TOKEN", "auth-key")
    monkeypatch.setenv("EVAL_MOCK", "bench")

    config = load_ouroboros_harness_config("configs/ouroboros.full_isolated.json")
    config = replace(config, ouroboros_url="http://127.0.0.1:9123")

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.synced = False

        def health(self):
            return {"ok": True}

        def apply_settings(self, settings):
            self.synced = True
            self.settings = settings
            return settings

        def set_post_task_evolution(self, enabled):
            return None

        def run_task(self, prompt, **kwargs):
            return {"status": "completed", "final_answer": "done", "turns": 1}

    with patch("bench_eval.ouroboros_client.OuroborosHTTPClient", FakeClient):
        result = run_ouroboros_full_task(
            "task",
            config=config,
            drive_root=tmp_path / "drive",
            timeout_seconds=30,
        )

    assert result["is_done"] is True
    assert result["harness_metadata"]["ouroboros_llm_sync"]["model"] == "gigachat::GigaChat-3-Ultra"


def test_collect_ouroboros_model_slots_parses_fallback_and_review():
    settings = build_ouroboros_llm_settings(
        {
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": "google/gemini-2.5-flash",
            "OUROBOROS_MODEL_FALLBACKS": "deepseek/deepseek-v4-flash,google/gemini-2.5-flash",
            "OPENROUTER_API_KEY": "sk-test",
            "EVAL_MOCK": "bench",
        }
    )
    slots = collect_ouroboros_model_slots(settings)
    assert slots["main"] == ["google/gemini-2.5-flash"]
    assert slots["fallback"] == ["deepseek/deepseek-v4-flash", "google/gemini-2.5-flash"]
    assert slots["review"] == ["google/gemini-2.5-flash"]
