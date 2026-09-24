"""Verbatim call dumps: what lands on disk when GUI_AGENT_DUMP_DIR is set.

No network — the GigaHF submit/poll pair is served by an httpx MockTransport, so
the assertions are about the dump layout and about it holding the exact bodies.

    pytest tests/agents/test_call_dump.py
"""

from __future__ import annotations

import json

import httpx
import pytest

from bench_eval.agents.core import dump
from bench_eval.agents.core.client import Endpoint, SamplingParams, VLMClient
from bench_eval.agents.core.gigahf import GigaHFClient, GigaHFOptions

BASE_URL = "https://gigahf.sberdevices.ru/api/v1"
PIXEL = "iVBORw0KGgoAAAANSUhEUg"
MESSAGES = [
    {
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{PIXEL}"}},
            {"type": "text", "text": "открой корзину"},
        ],
    }
]


def completion(text: str = "pyautogui.click(100, 200)") -> dict:
    return {
        "id": "cmpl-1",
        "model": "Qwen3.8-27B",
        "choices": [
            {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": text}}
        ],
        "usage": {"prompt_tokens": 120, "completion_tokens": 8, "total_tokens": 128},
    }


@pytest.fixture
def dump_dir(tmp_path, monkeypatch):
    monkeypatch.setenv(dump.ENV_DIR, str(tmp_path / "calls"))
    monkeypatch.delenv(dump.ENV_IMAGES, raising=False)
    dump.set_context(task_key="ecommerce_basket__ab12", step=3)
    return tmp_path / "calls"


def gigahf_client(handler) -> GigaHFClient:
    client = GigaHFClient(
        Endpoint(model="Qwen3.8-27B", base_url=BASE_URL, api_key="test-token", platform="gigahf"),
        options=GigaHFOptions(poll_interval=0.0, poll_max_interval=0.0),
    )
    client._client = httpx.AsyncClient(
        base_url=BASE_URL, transport=httpx.MockTransport(handler)
    )
    return client


def dumped(directory) -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(directory.rglob("*.json"))
    ]


def test_dumping_is_off_without_the_env_var(monkeypatch):
    monkeypatch.delenv(dump.ENV_DIR, raising=False)
    assert VLMClient(Endpoint(model="qwen3-vl-8b")).dumper is None


@pytest.mark.asyncio
async def test_async_dump_keeps_the_wire_body_and_the_generation(dump_dir):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/async/chat/completions"):
            return httpx.Response(200, json={"id": "req-7", "status": "pending"})
        return httpx.Response(200, json={"status": "ready", "response": completion()})

    client = gigahf_client(handler)
    await client.chat(MESSAGES, sampling=SamplingParams(max_tokens=4096))

    (call,) = dumped(dump_dir)
    # The envelope GigaHF actually receives, screenshots and all.
    assert call["http"]["url"] == f"{BASE_URL}/async/chat/completions"
    assert call["http"]["body"]["request"]["messages"] == MESSAGES
    assert PIXEL in json.dumps(call["http"]["body"])
    assert call["request"]["max_tokens"] == 4096
    # The generation, untouched, plus the poll history that produced it.
    assert call["response"] == completion()
    assert call["gigahf"]["request_id"] == "req-7"
    assert [poll["status"] for poll in call["gigahf"]["polls"]] == ["ready"]
    assert call["error"] is None


@pytest.mark.asyncio
async def test_dump_is_filed_by_task_and_step_with_a_skimmable_summary(dump_dir):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/async/chat/completions"):
            return httpx.Response(200, json={"status": "ready", "response": completion()})
        return httpx.Response(404)

    await gigahf_client(handler).chat(MESSAGES)

    (path,) = sorted(dump_dir.rglob("*.json"))
    assert path.parent.name == "ecommerce_basket__ab12"
    assert path.name.startswith("step-03_call-")

    summary = json.loads(path.read_text(encoding="utf-8"))["summary"]
    assert summary["content"] == "pyautogui.click(100, 200)"
    assert summary["images"] == 1
    assert summary["usage"]["total_tokens"] == 128

    (line,) = (dump_dir / "index.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(line)
    assert entry["context"]["step"] == 3
    assert entry["transport"] == "gigahf-async"
    assert PIXEL not in line  # the index stays greppable


@pytest.mark.asyncio
async def test_a_failed_call_is_dumped_with_its_error(dump_dir):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "extra fields not permitted"})

    with pytest.raises(Exception):
        await gigahf_client(handler).chat(MESSAGES)

    (call,) = dumped(dump_dir)
    assert call["response"] is None
    assert "422" in call["error"]


@pytest.mark.asyncio
async def test_trim_mode_swaps_screenshots_for_their_size(dump_dir, monkeypatch):
    monkeypatch.setenv(dump.ENV_IMAGES, "trim")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ready", "response": completion()})

    await gigahf_client(handler).chat(MESSAGES)

    (call,) = dumped(dump_dir)
    part = call["http"]["body"]["request"]["messages"][0]["content"][0]
    assert part["image_url"]["url"] == f"<base64 image, {len(PIXEL)} chars>"


# ------------------------------------------------------- the config switch


def eval_config(**overrides):
    """A stand-in for EvalConfig carrying only what the resolver reads."""
    from types import SimpleNamespace

    fields = {
        "agent_dump_enabled": False,
        "agent_dump_dir": None,
        "eval_output_dir": None,
        "eval_results_base_dir": "tests/eval",
        "agent_max_steps": 25,
        "agent_max_failures": 5,
        "agent_wait_between_actions": 0.5,
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


def build(config, monkeypatch, **env):
    from bench_eval.agents.core.settings import build_settings

    monkeypatch.setenv("GUI_AGENT_BASE_URL", BASE_URL)
    monkeypatch.setenv("GUI_AGENT_API_KEY", "test-token")
    for name in (dump.ENV_DIR, dump.ENV_IMAGES, "GUI_AGENT_DUMP_DIR"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return build_settings("qwen3-vl-8b", eval_config=config)


def test_dumping_is_off_when_the_config_says_so(monkeypatch):
    settings = build(eval_config(agent_dump_enabled=False), monkeypatch)
    assert settings.dump_dir is None


def test_the_switch_wins_over_a_directory_being_set(monkeypatch):
    # A leftover AGENT_DUMP_DIR must not turn dumping back on.
    config = eval_config(agent_dump_enabled=False, agent_dump_dir="logs/stale")
    assert build(config, monkeypatch).dump_dir is None


def test_enabled_without_a_directory_writes_beside_the_run(monkeypatch):
    config = eval_config(agent_dump_enabled=True, eval_output_dir="tests/eval/run-7")
    assert build(config, monkeypatch).dump_dir == "tests/eval/run-7/llm-calls"


def test_an_explicit_directory_is_used_verbatim(monkeypatch):
    config = eval_config(agent_dump_enabled=True, agent_dump_dir="logs/mine")
    assert build(config, monkeypatch).dump_dir == "logs/mine"


def test_config_reads_the_switch_and_its_legacy_alias(monkeypatch):
    from bench_eval.config import load_config

    monkeypatch.delenv("AGENT_DUMP_DIR", raising=False)
    monkeypatch.delenv("GUI_AGENT_DUMP_DIR", raising=False)
    monkeypatch.delenv("AGENT_DUMP_ENABLED", raising=False)
    assert load_config().agent_dump_enabled is False

    # The name this shipped with still switches dumping on by itself.
    monkeypatch.setenv("GUI_AGENT_DUMP_DIR", "logs/legacy")
    config = load_config()
    assert config.agent_dump_enabled is True
    assert config.agent_dump_dir == "logs/legacy"

    # An explicit false wins over a directory being present.
    monkeypatch.setenv("AGENT_DUMP_ENABLED", "false")
    assert load_config().agent_dump_enabled is False


def test_a_disabled_run_builds_a_client_that_records_nothing(monkeypatch, tmp_path):
    from bench_eval.agents.core.client import Endpoint, create_client

    for name in (dump.ENV_DIR, "GUI_AGENT_DUMP_DIR"):
        monkeypatch.delenv(name, raising=False)
    client = create_client(Endpoint(model="qwen3-vl-8b"), dumper=None)
    assert client.dumper is None
    # And the record it opens is inert, so the transports need no branching.
    record = client._start_record(
        transport="openai", path="/chat/completions", body={}, request={}
    )
    record.finish(response={"choices": []})
    assert record.path is None
    assert list(tmp_path.iterdir()) == []
