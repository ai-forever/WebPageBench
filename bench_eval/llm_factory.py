"""Create browser-use LLM clients from environment settings."""

from __future__ import annotations

import asyncio
import gzip
from dataclasses import dataclass
from typing import Any, TypeVar

import httpx

from bench_eval.config import EvalConfig
from bench_eval.retry_utils import retry_backoff_seconds

T = TypeVar("T")

_GZIP_MAGIC = b"\x1f\x8b"
LLM_ACCEPT_ENCODING_HEADERS = {"Accept-Encoding": "identity"}


def maybe_gunzip_http_body(content: bytes) -> bytes:
    """Decode a gzip body that some proxies send without Content-Encoding."""
    if len(content) >= 2 and content[:2] == _GZIP_MAGIC:
        return gzip.decompress(content)
    return content


class _GunzipIfMagicTransport(httpx.AsyncBaseTransport):
    """httpx transport that gunzips 0x1f8b bodies if the proxy omitted the header."""

    def __init__(self, inner: httpx.AsyncBaseTransport | None = None) -> None:
        self._inner = inner or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await self._inner.handle_async_request(request)
        await response.aread()
        body = maybe_gunzip_http_body(response.content)
        if body is response.content:
            return response
        headers = httpx.Headers(response.headers)
        headers.pop("content-encoding", None)
        headers["content-length"] = str(len(body))
        return httpx.Response(
            status_code=response.status_code,
            headers=headers,
            content=body,
            request=request,
            extensions=response.extensions,
        )

    async def aclose(self) -> None:
        await self._inner.aclose()


class _GunzipIfMagicSyncTransport(httpx.BaseTransport):
    """Sync counterpart of ``_GunzipIfMagicTransport`` (LangChain sync calls)."""

    def __init__(self, inner: httpx.BaseTransport | None = None) -> None:
        self._inner = inner or httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        response = self._inner.handle_request(request)
        response.read()
        body = maybe_gunzip_http_body(response.content)
        if body is response.content:
            return response
        headers = httpx.Headers(response.headers)
        headers.pop("content-encoding", None)
        headers["content-length"] = str(len(body))
        return httpx.Response(
            status_code=response.status_code,
            headers=headers,
            content=body,
            request=request,
            extensions=response.extensions,
        )

    def close(self) -> None:
        self._inner.close()


def build_llm_http_client(**kwargs: Any) -> httpx.AsyncClient:
    """OpenAI-compatible HTTP client that refuses gzip and gunzips stray magic bytes."""
    headers = dict(LLM_ACCEPT_ENCODING_HEADERS)
    headers.update(kwargs.pop("headers", {}) or {})
    if "transport" not in kwargs:
        kwargs["transport"] = _GunzipIfMagicTransport(
            httpx.AsyncHTTPTransport(verify=kwargs.get("verify", True))
        )
    return httpx.AsyncClient(headers=headers, **kwargs)


def build_llm_sync_http_client(**kwargs: Any) -> httpx.Client:
    """Sync OpenAI-compatible client with the same gzip workaround."""
    headers = dict(LLM_ACCEPT_ENCODING_HEADERS)
    headers.update(kwargs.pop("headers", {}) or {})
    if "transport" not in kwargs:
        kwargs["transport"] = _GunzipIfMagicSyncTransport(
            httpx.HTTPTransport(verify=kwargs.get("verify", True))
        )
    return httpx.Client(headers=headers, **kwargs)


@dataclass
class RetryingChatModel:
    """Application-level retries for LLM providers without built-in HTTP retries."""

    wrapped: Any
    max_retries: int = 3

    @property
    def provider(self) -> str:
        return self.wrapped.provider

    @property
    def name(self) -> str:
        return self.wrapped.name

    @property
    def model(self) -> str:
        return self.wrapped.model

    async def ainvoke(self, messages, output_format=None, **kwargs: Any):
        from browser_use.llm.exceptions import ModelProviderError

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return await self.wrapped.ainvoke(
                    messages,
                    output_format=output_format,
                    **kwargs,
                )
            except ModelProviderError as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise
            except (TimeoutError, ConnectionError, OSError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise
            await asyncio.sleep(retry_backoff_seconds(attempt))
        if last_error is not None:
            raise last_error
        raise RuntimeError("LLM request failed without an exception")


def create_llm(config: EvalConfig):
    """
    Return a browser-use chat model.

    Supports:
    - openai: OpenAI API or any OpenAI-compatible server (vLLM, LiteLLM proxy, etc.)
    - gigahf: GigaHF platform (OpenAI-shaped; mind the 10 RPM sync cap)
    - openrouter: OpenRouter (ChatOpenRouter)
    - gigachat: native GigaChat SDK (OAuth, SSL, structured output via achat_parse)
    - ollama: local Ollama
    """
    provider = config.llm_provider
    max_retries = config.llm_max_retries

    if provider == "ollama":
        from browser_use import ChatOllama

        llm = ChatOllama(model=config.llm_model)
        if max_retries > 0:
            return RetryingChatModel(wrapped=llm, max_retries=max_retries)
        return llm

    if provider in {"openai", "vllm", "azure", "gigahf"}:
        from browser_use import ChatOpenAI

        kwargs = {
            "model": config.llm_model,
            "temperature": config.llm_temperature,
            "max_retries": max_retries,
        }
        if config.llm_api_key:
            kwargs["api_key"] = config.llm_api_key
        if config.llm_base_url:
            kwargs["base_url"] = config.llm_base_url
        kwargs["http_client"] = build_llm_http_client()
        kwargs["default_headers"] = dict(LLM_ACCEPT_ENCODING_HEADERS)
        return ChatOpenAI(**kwargs)

    if provider == "openrouter":
        from browser_use.llm.openrouter.chat import ChatOpenRouter

        kwargs = {
            "model": config.llm_model,
            "temperature": config.llm_temperature,
            "max_retries": max_retries,
        }
        if config.llm_api_key:
            kwargs["api_key"] = config.llm_api_key
        if config.llm_base_url:
            kwargs["base_url"] = config.llm_base_url
        kwargs["http_client"] = build_llm_http_client()
        kwargs["default_headers"] = dict(LLM_ACCEPT_ENCODING_HEADERS)
        return ChatOpenRouter(**kwargs)

    if provider == "gigachat":
        from bench_eval.gigachat_chat import ChatGigaChat

        return ChatGigaChat.from_env(
            model=config.llm_model,
            temperature=config.llm_temperature,
            max_retries=max_retries,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER={provider!r}. "
        "Use openai, vllm, azure, gigahf, openrouter, gigachat, or ollama."
    )
