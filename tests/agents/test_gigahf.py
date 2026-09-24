"""GigaHF transport tests: submit/poll, payload reshaping, failure handling.

No network and no token — every case drives the client through an httpx
MockTransport, so the assertions are about the wire format the platform
documents (``/api/v1`` OpenAPI v1.15) rather than about a live deployment.

    pytest tests/agents/test_gigahf.py
"""

from __future__ import annotations

import json

import httpx
import pytest

from bench_eval.agents.core.client import (
    PLATFORM_GIGAHF,
    PLATFORM_VLLM,
    Endpoint,
    PermanentError,
    SamplingParams,
    TransientError,
    VLMClient,
    create_client,
    resolve_platform,
)
from bench_eval.agents.core.gigahf import GigaHFClient, GigaHFOptions, model_ids

BASE_URL = "https://gigahf.sberdevices.ru/api/v1"
MESSAGES = [{"role": "user", "content": "какая кнопка тут ведёт в корзину?"}]


def endpoint(**overrides) -> Endpoint:
    kwargs = {
        "model": "Qwen3.8-27B",
        "base_url": BASE_URL,
        "api_key": "test-token",
        "platform": PLATFORM_GIGAHF,
        "max_retries": 0,
    }
    kwargs.update(overrides)
    return Endpoint(**kwargs)


def completion(text: str = "нажми на иконку корзины", **message_extra) -> dict:
    message = {"role": "assistant", "content": text}
    message.update(message_extra)
    return {
        "id": "cmpl-1",
        "model": "Qwen3.8-27B",
        "object": "chat.completion",
        "choices": [{"index": 0, "finish_reason": "stop", "message": message}],
        "usage": {"prompt_tokens": 120, "completion_tokens": 8, "total_tokens": 128},
    }


def build_client(handler, *, options: GigaHFOptions | None = None, **endpoint_kwargs):
    """A GigaHF client whose HTTP calls are served by ``handler``."""
    client = GigaHFClient(
        endpoint(**endpoint_kwargs),
        options=options or GigaHFOptions(poll_interval=0.0, poll_max_interval=0.0),
    )
    client._client = httpx.AsyncClient(
        base_url=BASE_URL,
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer test-token"},
    )
    return client


# ------------------------------------------------------------ platform wiring


@pytest.mark.parametrize(
    "explicit,url,expected",
    [
        (None, BASE_URL, PLATFORM_GIGAHF),
        (None, "http://127.0.0.1:8000/v1", PLATFORM_VLLM),
        ("gigahf", "http://127.0.0.1:8000/v1", PLATFORM_GIGAHF),
        ("vllm", BASE_URL, PLATFORM_VLLM),
    ],
)
def test_platform_is_explicit_or_recognised_from_the_host(explicit, url, expected):
    # NB: the parameter cannot be called `base_url` — pytest-base-url claims it.
    assert resolve_platform(explicit, base_url=url) == expected


def test_endpoint_from_env_picks_up_the_platform(monkeypatch):
    monkeypatch.setenv("GUI_AGENT_BASE_URL", BASE_URL)
    monkeypatch.setenv("GUI_AGENT_API_KEY", "test-token")
    monkeypatch.setenv("GUI_AGENT_MODEL", "Qwen3.8-27B")
    resolved = Endpoint.from_env()
    assert resolved.platform == PLATFORM_GIGAHF
    assert resolved.base_url == BASE_URL


def test_create_client_selects_the_transport(monkeypatch):
    monkeypatch.setenv("GIGAHF_MODE", "async")
    assert isinstance(create_client(endpoint()), GigaHFClient)
    local = Endpoint(model="qwen3-vl-8b", api_key="EMPTY", platform=PLATFORM_VLLM)
    assert type(create_client(local)) is VLMClient


def test_gigahf_skips_tls_verification_but_vllm_does_not():
    # The host is signed by an internal CA that certifi does not carry.
    assert GigaHFClient.ssl_verify is False
    assert VLMClient.ssl_verify is True


@pytest.mark.asyncio
async def test_the_httpx_client_is_built_with_verification_off():
    client = GigaHFClient(endpoint(), options=GigaHFOptions())
    try:
        transport = (await client._http())._transport
        inner = getattr(transport, "_inner", transport)
        assert inner._pool._ssl_context.verify_mode.name == "CERT_NONE"
    finally:
        await client.close()


def test_a_missing_token_fails_before_any_request_is_made():
    with pytest.raises(ValueError, match="bearer token"):
        GigaHFClient(endpoint(api_key="EMPTY"), options=GigaHFOptions())


# ---------------------------------------------------------- async submit/poll


@pytest.mark.asyncio
async def test_async_mode_submits_then_polls_until_ready():
    seen: list[tuple[str, str]] = []
    polls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if request.method == "POST":
            body = json.loads(request.content)
            # The whole OpenAI payload travels nested under "request".
            assert set(body) == {"request"}
            assert body["request"]["model"] == "Qwen3.8-27B"
            assert body["request"]["messages"] == MESSAGES
            return httpx.Response(200, json={"id": "req-7", "status": "pending"})
        polls["n"] += 1
        if polls["n"] == 1:
            return httpx.Response(
                200, json={"id": "req-7", "status": "pending", "ready_estimation_seconds": 0}
            )
        return httpx.Response(200, json={"id": "req-7", "status": "ready", "response": completion()})

    client = build_client(handler)
    response = await client.chat(MESSAGES)

    assert response.text == "нажми на иконку корзины"
    assert response.finish_reason == "stop"
    assert response.usage["total_tokens"] == 128
    assert response.usage["llm_calls"] == 1
    assert client.ledger.total["prompt_tokens"] == 120
    assert seen == [
        ("POST", "/api/v1/async/chat/completions"),
        ("GET", "/api/v1/async/chat/completions/req-7"),
        ("GET", "/api/v1/async/chat/completions/req-7"),
    ]


@pytest.mark.asyncio
async def test_a_submit_that_is_already_ready_skips_polling():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.method)
        return httpx.Response(200, json={"id": "req-8", "status": "ready", "response": completion()})

    client = build_client(handler)
    response = await client.chat(MESSAGES)

    assert response.text == "нажми на иконку корзины"
    assert calls == ["POST"]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["failed", "cancelled", "unknown_query_id"])
async def test_terminal_statuses_raise_with_the_server_reason(status):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(200, json={"id": "req-9", "status": "pending"})
        return httpx.Response(
            200, json={"id": "req-9", "status": status, "error_message": "no capacity"}
        )

    client = build_client(handler)
    with pytest.raises(RuntimeError, match=f"{status}: no capacity"):
        await client.chat(MESSAGES)


@pytest.mark.asyncio
async def test_polling_gives_up_after_the_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(200, json={"id": "req-10", "status": "pending"})
        return httpx.Response(200, json={"id": "req-10", "status": "pending"})

    client = build_client(
        handler,
        options=GigaHFOptions(poll_interval=0.0, poll_max_interval=0.0, poll_timeout=0.0),
    )
    with pytest.raises(TransientError, match="still pending"):
        await client.chat(MESSAGES)


# ------------------------------------------------------------- payload shaping


def test_unknown_fields_are_nested_under_extra_params():
    client = build_client(lambda request: httpx.Response(200, json={}))
    request = client.build_request(
        {
            "model": "Qwen3.8-27B",
            "messages": MESSAGES,
            "temperature": 0.0,
            "top_p": 0.9,
            "max_tokens": 4096,
            # vLLM-only knobs the GigaHF schema does not declare at top level.
            "guided_json": {"type": "object"},
            "chat_template_kwargs": {"enable_thinking": False},
        }
    )

    assert set(request) == {
        "model",
        "messages",
        "temperature",
        "top_p",
        "max_tokens",
        "extra_params",
    }
    assert request["extra_params"] == {
        "guided_json": {"type": "object"},
        "chat_template_kwargs": {"enable_thinking": False},
    }


def test_configured_extra_params_are_merged_and_overridable():
    client = build_client(
        lambda request: httpx.Response(200, json={}),
        options=GigaHFOptions(extra_params={"model_path": "giga/Staging/Qwen3.5-2B"}),
    )
    request = client.build_request(
        {"model": "m", "messages": MESSAGES, "extra_params": {"num_inference_steps": 30}}
    )
    assert request["extra_params"] == {
        "model_path": "giga/Staging/Qwen3.5-2B",
        "num_inference_steps": 30,
    }


def test_a_plain_payload_carries_no_extra_params_key():
    client = build_client(lambda request: httpx.Response(200, json={}))
    assert "extra_params" not in client.build_request({"model": "m", "messages": MESSAGES})


@pytest.mark.asyncio
async def test_sampling_stop_tokens_reach_the_request():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content)["request"])
        return httpx.Response(200, json={"id": "r", "status": "ready", "response": completion()})

    client = build_client(handler)
    await client.chat(MESSAGES, sampling=SamplingParams(max_tokens=512, stop=("</tool_call>",)))

    assert captured["max_tokens"] == 512
    assert captured["stop"] == ["</tool_call>"]


# ------------------------------------------------------------------ sync mode


@pytest.mark.asyncio
async def test_sync_mode_posts_to_chat_completions():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        body = json.loads(request.content)
        # Sync mode sends the request unwrapped, OpenAI style.
        assert body["model"] == "Qwen3.8-27B"
        return httpx.Response(200, json=completion())

    client = build_client(handler, options=GigaHFOptions(mode="sync", sync_rpm=0))
    response = await client.chat(MESSAGES)

    assert response.text == "нажми на иконку корзины"
    assert seen == ["/api/v1/chat/completions"]


@pytest.mark.asyncio
async def test_a_sync_504_is_resumed_through_the_async_result():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(504, json={"detail": {"query_id": "req-11"}})
        assert request.url.path == "/api/v1/async/chat/completions/req-11"
        return httpx.Response(200, json={"status": "ready", "response": completion()})

    client = build_client(
        handler,
        options=GigaHFOptions(mode="sync", sync_rpm=0, poll_interval=0.0, poll_max_interval=0.0),
    )
    assert (await client.chat(MESSAGES)).text == "нажми на иконку корзины"


@pytest.mark.asyncio
async def test_a_504_without_a_query_id_is_reported_as_transient():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(504, text="gateway timeout")

    client = build_client(handler, options=GigaHFOptions(mode="sync", sync_rpm=0))
    with pytest.raises(TransientError, match="HTTP 504"):
        await client.chat(MESSAGES)


def test_mode_must_be_async_or_sync(monkeypatch):
    monkeypatch.setenv("GIGAHF_MODE", "batch")
    with pytest.raises(ValueError, match="must be 'async' or 'sync'"):
        GigaHFOptions.from_env()


# ---------------------------------------------------------------- retry rules


@pytest.mark.asyncio
async def test_429_is_retried_and_honours_retry_after():
    slept: list[float] = []
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] == 1:
            return httpx.Response(429, text="rate limited", headers={"Retry-After": "7"})
        return httpx.Response(200, json={"status": "ready", "response": completion()})

    client = build_client(handler, max_retries=2)

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    import bench_eval.agents.core.client as client_module

    original = client_module.asyncio.sleep
    client_module.asyncio.sleep = fake_sleep
    try:
        response = await client.chat(MESSAGES)
    finally:
        client_module.asyncio.sleep = original

    assert response.text == "нажми на иконку корзины"
    assert slept == [7.0]


@pytest.mark.asyncio
async def test_a_422_is_fatal_and_not_retried():
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        return httpx.Response(422, text="validation error")

    client = build_client(handler, max_retries=3)
    with pytest.raises(PermanentError, match="HTTP 422"):
        await client.chat(MESSAGES)
    assert attempts["n"] == 1


# ------------------------------------------------------------ reasoning + probe


@pytest.mark.asyncio
async def test_reasoning_content_is_used_when_content_came_back_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = completion("", reasoning_content="сначала открою каталог")
        return httpx.Response(200, json={"status": "ready", "response": payload})

    client = build_client(handler)
    assert (await client.chat(MESSAGES)).text == "сначала открою каталог"


def test_model_ids_reads_both_the_openai_and_the_gigahf_shape():
    assert model_ids({"data": [{"id": "qwen3-vl-8b"}]}) == ["qwen3-vl-8b"]
    assert model_ids({"models": [{"name": "Qwen3.8-27B"}, {"name": "gemma-4-31B-it"}]}) == [
        "Qwen3.8-27B",
        "gemma-4-31B-it",
    ]
    assert model_ids({}) == []
    assert model_ids("nope") == []
