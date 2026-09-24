"""HTTP workarounds for the Ouroboros full_* process.

1. Some LLM proxies return gzip bodies (magic ``0x1f 0x8b``) without
   ``Content-Encoding``. OpenAI/httpx then try to decode raw bytes as UTF-8.
2. Ouroboros hardcodes ``https://openrouter.ai/api/v1`` and ignores
   ``OPENROUTER_BASE_URL``. When a proxy URL is in the env, rewrite those
   requests onto the proxy.

This file is loaded as ``sitecustomize`` via a dedicated PYTHONPATH set by
``_run_ouroboros_server`` / ``merge_ouroboros_llm_env``. It must stay
self-contained: the Ouroboros process must not import ``bench_eval``.
"""

from __future__ import annotations

import gzip
import os

_GZIP_MAGIC = b"\x1f\x8b"
_PATCHED_ATTR = "_agent_bench_gzip_patched"
_AUTH_PATCHED_ATTR = "_agent_bench_openrouter_auth_patched"
_AUTH_KEY_MARK = "/api/v1/auth/key"
_STUB_AUTH_KEY_BODY = b'{"data":{"usage":0,"usage_daily":0}}'
_OPENROUTER_PREFIXES = (
    "https://openrouter.ai/api/v1",
    "http://openrouter.ai/api/v1",
    "https://openrouter.ai",
    "http://openrouter.ai",
)


def maybe_gunzip_http_body(content: bytes) -> bytes:
    if len(content) >= 2 and content[:2] == _GZIP_MAGIC:
        return gzip.decompress(content)
    return content


def llm_proxy_base() -> str:
    """OpenAI-compatible proxy base, or empty when traffic should stay on OpenRouter."""
    for key in ("OPENROUTER_BASE_URL", "LLM_BASE_URL", "OPENAI_BASE_URL"):
        value = str(os.environ.get(key) or "").strip().rstrip("/")
        if value and "openrouter.ai" not in value.lower():
            return value
    return ""


def rewrite_openrouter_url(url: str) -> str:
    """Map official OpenRouter URLs onto the configured LLM proxy."""
    proxy = llm_proxy_base()
    if not proxy:
        return url
    text = str(url or "")
    for prefix in _OPENROUTER_PREFIXES:
        if text.startswith(prefix):
            return proxy + text[len(prefix) :]
    return text


def _rebuild_response(response, request, body: bytes):
    import httpx

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


def _rewrite_httpx_request(request):
    import httpx

    original = str(request.url)
    rewritten = rewrite_openrouter_url(original)
    if rewritten == original:
        return request
    headers = httpx.Headers(request.headers)
    headers.pop("host", None)
    return httpx.Request(
        request.method,
        rewritten,
        headers=headers,
        content=request.content,
        extensions=request.extensions,
    )


def _wrap_sync_transport(inner):
    import httpx

    if inner is None or getattr(inner, _PATCHED_ATTR, False):
        return inner

    class _GunzipIfMagicSyncTransport(httpx.BaseTransport):
        def __init__(self, inner_transport):
            self._inner = inner_transport
            setattr(self, _PATCHED_ATTR, True)

        def handle_request(self, request):
            request = _rewrite_httpx_request(request)
            response = self._inner.handle_request(request)
            response.read()
            body = maybe_gunzip_http_body(response.content)
            if body is response.content:
                return response
            return _rebuild_response(response, request, body)

        def close(self):
            close = getattr(self._inner, "close", None)
            if close is not None:
                close()

    return _GunzipIfMagicSyncTransport(inner)


def _wrap_async_transport(inner):
    import httpx

    if inner is None or getattr(inner, _PATCHED_ATTR, False):
        return inner

    class _GunzipIfMagicTransport(httpx.AsyncBaseTransport):
        def __init__(self, inner_transport):
            self._inner = inner_transport
            setattr(self, _PATCHED_ATTR, True)

        async def handle_async_request(self, request):
            request = _rewrite_httpx_request(request)
            response = await self._inner.handle_async_request(request)
            await response.aread()
            body = maybe_gunzip_http_body(response.content)
            if body is response.content:
                return response
            return _rebuild_response(response, request, body)

        async def aclose(self):
            aclose = getattr(self._inner, "aclose", None)
            if aclose is not None:
                await aclose()

    return _GunzipIfMagicTransport(inner)


def _merge_identity_headers(kwargs: dict) -> dict:
    headers = dict(kwargs.get("headers") or {})
    if not any(str(key).lower() == "accept-encoding" for key in headers):
        headers["Accept-Encoding"] = "identity"
    kwargs["headers"] = headers
    return kwargs


def _wrap_mounts(mounts, wrapper):
    if not mounts:
        return mounts
    return {key: wrapper(value) for key, value in mounts.items()}


def _request_url(url) -> str:
    if hasattr(url, "full_url"):
        return str(url.full_url)
    get_full_url = getattr(url, "get_full_url", None)
    if callable(get_full_url):
        return str(get_full_url())
    return str(url)


class _StubAuthKeyResponse:
    def read(self) -> bytes:
        return _STUB_AUTH_KEY_BODY

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False


def _rewrite_urllib_url(url):
    import urllib.request

    original = _request_url(url)
    rewritten = rewrite_openrouter_url(original)
    if rewritten == original:
        return url
    if isinstance(url, urllib.request.Request):
        headers = dict(url.header_items())
        headers.pop("Host", None)
        headers.pop("host", None)
        return urllib.request.Request(
            rewritten,
            data=url.data,
            headers=headers,
            method=url.get_method(),
        )
    return rewritten


def install_openrouter_auth_skip() -> None:
    """Skip blocked /auth/key and send remaining OpenRouter urllib calls to the proxy."""
    import urllib.request

    if getattr(urllib.request.urlopen, _AUTH_PATCHED_ATTR, False):
        return

    orig_urlopen = urllib.request.urlopen

    def _urlopen(url, *args, **kwargs):
        if _AUTH_KEY_MARK in _request_url(url):
            return _StubAuthKeyResponse()
        return orig_urlopen(_rewrite_urllib_url(url), *args, **kwargs)

    setattr(_urlopen, _AUTH_PATCHED_ATTR, True)
    urllib.request.urlopen = _urlopen


def install() -> None:
    import httpx

    if getattr(httpx.Client, _PATCHED_ATTR, False):
        return

    orig_client_init = httpx.Client.__init__
    orig_async_init = httpx.AsyncClient.__init__

    def _patched_client_init(self, *args, **kwargs):
        kwargs = _merge_identity_headers(kwargs)
        orig_client_init(self, *args, **kwargs)
        self._transport = _wrap_sync_transport(getattr(self, "_transport", None))
        if hasattr(self, "_mounts"):
            self._mounts = _wrap_mounts(self._mounts, _wrap_sync_transport)

    def _patched_async_init(self, *args, **kwargs):
        kwargs = _merge_identity_headers(kwargs)
        orig_async_init(self, *args, **kwargs)
        self._transport = _wrap_async_transport(getattr(self, "_transport", None))
        if hasattr(self, "_mounts"):
            self._mounts = _wrap_mounts(self._mounts, _wrap_async_transport)

    httpx.Client.__init__ = _patched_client_init
    httpx.AsyncClient.__init__ = _patched_async_init
    setattr(httpx.Client, _PATCHED_ATTR, True)
    setattr(httpx.AsyncClient, _PATCHED_ATTR, True)


try:
    install()
except Exception:
    # Never block Ouroboros startup if httpx is missing or internals changed.
    pass

try:
    install_openrouter_auth_skip()
except Exception:
    pass
