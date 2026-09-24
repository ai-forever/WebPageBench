"""Gzip/identity httpx hook used by ouroboros-full-* subprocesses."""

from __future__ import annotations

import gzip
import importlib.util
from pathlib import Path

import httpx
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HOOK_PATH = _REPO_ROOT / "scripts" / "ouroboros_httpx_hook" / "sitecustomize.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("ouroboros_httpx_hook", _HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _GzipJsonTransport(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        body = gzip.compress(b'{"ok": true}')
        return httpx.Response(200, content=body, request=request)


class _GzipJsonAsyncTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        body = gzip.compress(b'{"ok": true}')
        return httpx.Response(200, content=body, request=request)


def test_ouroboros_httpx_hook_gunzips_sync_json():
    hook = _load_hook()
    hook.install()
    client = httpx.Client(transport=_GzipJsonTransport())
    response = client.post("https://proxy.example/api/v1/chat/completions")
    assert response.json() == {"ok": True}
    assert client.headers["Accept-Encoding"] == "identity"


@pytest.mark.asyncio
async def test_ouroboros_httpx_hook_gunzips_async_json():
    hook = _load_hook()
    hook.install()
    async with httpx.AsyncClient(transport=_GzipJsonAsyncTransport()) as client:
        response = await client.post("https://proxy.example/api/v1/chat/completions")
        assert response.json() == {"ok": True}
        assert client.headers["Accept-Encoding"] == "identity"


def test_ouroboros_httpx_hook_stubs_openrouter_auth_key():
    import json
    import urllib.request

    hook = _load_hook()
    hook.install_openrouter_auth_skip()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": "Bearer sk-or-v1-test"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    assert data["data"]["usage"] == 0
    assert data["data"]["usage_daily"] == 0


def test_ouroboros_httpx_hook_stubs_auth_key_on_proxy_url():
    import json
    import urllib.request

    hook = _load_hook()
    hook.install_openrouter_auth_skip()
    req = urllib.request.Request("https://proxy.example/api/v1/auth/key")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    assert data["data"]["usage"] == 0


def test_rewrite_openrouter_url_maps_chat_completions(monkeypatch):
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://proxy.example/api/v1")
    hook = _load_hook()
    assert (
        hook.rewrite_openrouter_url("https://openrouter.ai/api/v1/chat/completions")
        == "https://proxy.example/api/v1/chat/completions"
    )


def test_rewrite_openrouter_url_skips_without_proxy(monkeypatch):
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    hook = _load_hook()
    url = "https://openrouter.ai/api/v1/chat/completions"
    assert hook.rewrite_openrouter_url(url) == url


def test_rewrite_openrouter_url_ignores_official_openrouter_base(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    hook = _load_hook()
    url = "https://openrouter.ai/api/v1/chat/completions"
    assert hook.rewrite_openrouter_url(url) == url


def test_ouroboros_httpx_hook_rewrites_openrouter_to_proxy(monkeypatch):
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://proxy.example/api/v1")
    hook = _load_hook()
    hook.install()

    class _RecordTransport(httpx.BaseTransport):
        def __init__(self):
            self.urls: list[str] = []

        def handle_request(self, request: httpx.Request) -> httpx.Response:
            self.urls.append(str(request.url))
            return httpx.Response(200, json={"ok": True}, request=request)

    recorder = _RecordTransport()
    client = httpx.Client(transport=recorder)
    response = client.post("https://openrouter.ai/api/v1/chat/completions", json={"model": "x"})
    assert response.json() == {"ok": True}
    assert recorder.urls == ["https://proxy.example/api/v1/chat/completions"]
