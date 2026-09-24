"""Unit tests for LLM client factory and retry configuration."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import EvalConfig, load_config
from bench_eval.llm_factory import (
    RetryingChatModel,
    create_llm,
    maybe_gunzip_http_body,
)


def test_load_config_default_llm_max_retries(monkeypatch):
    monkeypatch.delenv("LLM_MAX_RETRIES", raising=False)
    config = load_config()
    assert config.llm_max_retries == 3


def test_load_config_reads_llm_max_retries(monkeypatch):
    monkeypatch.setenv("LLM_MAX_RETRIES", "5")
    config = load_config()
    assert config.llm_max_retries == 5


def test_create_llm_openai_passes_max_retries():
    config = EvalConfig(llm_provider="openai", llm_model="gpt-4.1-mini", llm_max_retries=2)
    llm = create_llm(config)
    assert llm.max_retries == 2


def test_create_llm_openrouter_passes_max_retries():
    config = EvalConfig(
        llm_provider="openrouter",
        llm_model="google/gemini-2.5-flash",
        llm_max_retries=4,
    )
    llm = create_llm(config)
    assert llm.max_retries == 4
    assert llm.default_headers == {"Accept-Encoding": "identity"}
    assert llm.http_client is not None


def test_maybe_gunzip_http_body_decodes_gzip_without_header():
    import gzip

    raw = gzip.compress(b'{"ok": true}')
    assert raw[:2] == b"\x1f\x8b"
    assert maybe_gunzip_http_body(raw) == b'{"ok": true}'
    assert maybe_gunzip_http_body(b'{"ok": true}') == b'{"ok": true}'


def test_create_llm_gigachat_uses_native_adapter():
    config = EvalConfig(
        llm_provider="gigachat",
        llm_model="GigaChat-3-Ultra",
        llm_base_url="https://gigachat.ift.sberdevices.ru/v1",
        llm_api_key="test-token",
        llm_max_retries=5,
    )
    llm = create_llm(config)
    from bench_eval.gigachat_chat import ChatGigaChat

    assert isinstance(llm, ChatGigaChat)
    assert llm.model == "GigaChat-3-Ultra"
    assert llm.access_token == "test-token"
    assert llm.max_retries == 5


def test_create_llm_ollama_wraps_with_retries():
    config = EvalConfig(llm_provider="ollama", llm_model="llama3.1:8b", llm_max_retries=3)
    llm = create_llm(config)
    assert isinstance(llm, RetryingChatModel)
    assert llm.max_retries == 3


@pytest.mark.asyncio
async def test_retrying_chat_model_retries_on_provider_error():
    wrapped = MagicMock()
    wrapped.provider = "ollama"
    wrapped.name = "llama3.1:8b"
    wrapped.model = "llama3.1:8b"
    from browser_use.llm.exceptions import ModelProviderError

    wrapped.ainvoke = AsyncMock(
        side_effect=[
            ModelProviderError("rate limit", status_code=429),
            {"content": "ok"},
        ]
    )
    llm = RetryingChatModel(wrapped=wrapped, max_retries=2)
    result = await llm.ainvoke([])
    assert result == {"content": "ok"}
    assert wrapped.ainvoke.await_count == 2
