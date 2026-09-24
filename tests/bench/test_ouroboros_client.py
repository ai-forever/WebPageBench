"""Unit tests for ouroboros HTTP client helpers."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import urllib.error

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.ouroboros_client import (
    OuroborosHTTPClient,
    OuroborosUnavailableError,
    _normalize_ouroboros_result,
    health_indicates_ready,
    run_ouroboros_full_task,
)
from bench_eval.ouroboros_config import load_ouroboros_harness_config


@contextmanager
def _mock_urlopen_response(payload: str = '{"ok": true}'):
    response = MagicMock()
    response.read.return_value = payload.encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    yield response


def test_normalize_ouroboros_result_completed():
    payload = {"status": "completed", "summary": "done", "turns": 3}
    result = _normalize_ouroboros_result(
        payload,
        duration_seconds=12.5,
        executor="ouroboros-api",
    )
    assert result["is_done"] is True
    assert result["final_result"] == "done"
    assert result["steps"] == 3
    assert result["token_usage"]["total_tokens"] == 0
    assert result["harness_metadata"]["executor"] == "ouroboros-api"


def test_normalize_ouroboros_result_reads_loop_outcome_usage():
    prompt = "You are Ouroboros executing a browser automation task."
    payload = {
        "status": "completed",
        "description": prompt,
        "total_rounds": 8,
        "loop_outcome": {
            "final_answer": "Added item to basket.",
            "usage": {
                "prompt_tokens": 1200,
                "completion_tokens": 340,
                "total_rounds": 8,
            },
            "trace_refs": {
                "llm_call_refs": [{"llm_call_id": f"call-{index}"} for index in range(8)],
            },
        },
    }
    result = _normalize_ouroboros_result(
        payload,
        duration_seconds=78.0,
        executor="ouroboros-api",
    )
    assert result["final_result"] == "Added item to basket."
    assert result["steps"] == 8
    assert result["token_usage"]["prompt_tokens"] == 1200
    assert result["token_usage"]["completion_tokens"] == 340
    assert result["token_usage"]["total_tokens"] == 1540
    assert result["token_usage"]["llm_calls"] == 8


def test_normalize_ouroboros_result_reads_events_usage_by_model(tmp_path):
    events_path = tmp_path / "logs"
    events_path.mkdir(parents=True)
    (events_path / "events.jsonl").write_text(
        "\n".join(
            [
                '{"type":"llm_usage","task_id":"task-1","model":"google/gemini-2.5-flash","prompt_tokens":1000,"completion_tokens":200,"cost":0.01}',
                '{"type":"llm_usage","task_id":"task-1","model":"deepseek/deepseek-v4-flash","prompt_tokens":500,"completion_tokens":100,"cost":0.02}',
                '{"type":"llm_usage","task_id":"other","model":"ignored/model","prompt_tokens":999,"completion_tokens":999,"cost":9.99}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "status": "completed",
        "task_id": "task-1",
        "loop_outcome": {"final_answer": "done"},
    }
    llm_sync = {
        "OUROBOROS_MODEL": "google/gemini-2.5-flash",
        "OUROBOROS_MODEL_FALLBACKS": "deepseek/deepseek-v4-flash",
    }
    result = _normalize_ouroboros_result(
        payload,
        duration_seconds=1.0,
        executor="ouroboros-api",
        llm_sync=llm_sync,
        drive_root=tmp_path,
    )
    by_model = result["token_usage_by_model"]
    assert set(by_model) == {
        "google/gemini-2.5-flash",
        "deepseek/deepseek-v4-flash",
    }
    assert by_model["google/gemini-2.5-flash"]["prompt_tokens"] == 1000
    assert by_model["deepseek/deepseek-v4-flash"]["cost_usd"] == pytest.approx(0.02)
    assert "fallback" in (by_model["deepseek/deepseek-v4-flash"].get("roles") or [])
    assert result["token_usage"]["total_tokens"] == 1800


def test_normalize_ouroboros_result_prefers_final_answer_over_description():
    description = "На сайте добавь в корзину любой товар."
    payload = {
        "status": "completed",
        "description": description,
        "result": description,
        "loop_outcome": {
            "final_text": "FINAL ANSWER: basket updated",
            "final_answer": "basket updated",
        },
    }
    result = _normalize_ouroboros_result(
        payload,
        duration_seconds=1.0,
        executor="ouroboros-api",
    )
    assert result["final_result"] == "basket updated"


def test_request_retries_on_retryable_http_error():
    client = OuroborosHTTPClient("http://127.0.0.1:9000", max_retries=2)
    http_error = urllib.error.HTTPError(
        "http://127.0.0.1:9000/api/health",
        503,
        "unavailable",
        hdrs=None,
        fp=io.BytesIO(b"temporary"),
    )
    with patch("bench_eval.ouroboros_client.time.sleep") as sleep_mock:
        with patch(
            "urllib.request.urlopen",
            side_effect=[http_error, _mock_urlopen_response('{"status":"ok"}')],
        ) as urlopen_mock:
            result = client.health()
    assert result == {"status": "ok"}
    assert urlopen_mock.call_count == 2
    sleep_mock.assert_called_once()


def test_request_retries_on_connection_error():
    client = OuroborosHTTPClient("http://127.0.0.1:9000", max_retries=1)
    with patch("bench_eval.ouroboros_client.time.sleep"):
        with patch(
            "urllib.request.urlopen",
            side_effect=[
                urllib.error.URLError("connection refused"),
                _mock_urlopen_response('{"status":"ok"}'),
            ],
        ) as urlopen_mock:
            result = client.health()
    assert result == {"status": "ok"}
    assert urlopen_mock.call_count == 2


def test_request_raises_after_exhausted_retries():
    client = OuroborosHTTPClient("http://127.0.0.1:9000", max_retries=1)
    with patch("bench_eval.ouroboros_client.time.sleep"):
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            with pytest.raises(OuroborosUnavailableError):
                client.health()


def test_wait_task_fails_when_queue_stuck_in_pending(monkeypatch):
    client = OuroborosHTTPClient("http://127.0.0.1:9000", max_retries=0)
    clock = {"t": 0.0}

    def fake_perf_counter():
        return clock["t"]

    def fake_sleep(seconds):
        clock["t"] += seconds

    monkeypatch.setattr("bench_eval.ouroboros_client.time.perf_counter", fake_perf_counter)
    monkeypatch.setattr("bench_eval.ouroboros_client.time.sleep", fake_sleep)
    monkeypatch.setattr(
        "bench_eval.ouroboros_client._QUEUE_STUCK_FAIL_SECONDS",
        10.0,
    )

    with patch.object(
        client,
        "request",
        return_value={"status": "queued", "artifact_status": ""},
    ):
        with pytest.raises(TimeoutError, match="stuck in queued"):
            client.wait_task("task-1", timeout_seconds=3600.0)


def test_health_indicates_ready_accepts_common_payloads():
    assert health_indicates_ready({}) is True
    assert health_indicates_ready({"status": "ok"}) is True
    assert health_indicates_ready({"status": "ok", "supervisor_ready": True}) is True
    assert health_indicates_ready({"status": "ok", "supervisor_ready": False}) is False
    assert health_indicates_ready({"status": "starting"}) is False


def test_wait_until_ready_polls_through_restart(monkeypatch):
    client = OuroborosHTTPClient("http://127.0.0.1:9000", max_retries=0)
    responses = [
        OuroborosUnavailableError("down"),
        {"status": "starting", "supervisor_ready": False},
        {"status": "ok", "supervisor_ready": True},
    ]

    def fake_health():
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    with patch.object(client, "health", side_effect=fake_health):
        with patch("bench_eval.ouroboros_client.time.sleep"):
            health = client.wait_until_ready(timeout_seconds=10.0, poll_interval=0.01)
    assert health == {"status": "ok", "supervisor_ready": True}


def test_wait_until_ready_times_out(monkeypatch):
    client = OuroborosHTTPClient("http://127.0.0.1:9000", max_retries=0)
    clock = {"t": 0.0}

    def fake_perf_counter():
        return clock["t"]

    def fake_sleep(seconds):
        clock["t"] += seconds

    monkeypatch.setattr("bench_eval.ouroboros_client.time.perf_counter", fake_perf_counter)
    monkeypatch.setattr("bench_eval.ouroboros_client.time.sleep", fake_sleep)

    with patch.object(
        client,
        "health",
        side_effect=OuroborosUnavailableError("down"),
    ):
        with pytest.raises(TimeoutError, match="not ready within"):
            client.wait_until_ready(timeout_seconds=2.0, poll_interval=1.0)


def test_run_ouroboros_full_task_waits_when_evolution_enabled(tmp_path, monkeypatch):
    config = load_ouroboros_harness_config("configs/ouroboros.full_evolving.json")
    monkeypatch.setenv("OUROBOROS_URL", "http://127.0.0.1:9123")

    client = OuroborosHTTPClient("http://127.0.0.1:9123", max_retries=0)
    with patch(
        "bench_eval.ouroboros_client.OuroborosHTTPClient",
        return_value=client,
    ):
        with patch.object(client, "wait_until_ready", return_value={"status": "ok"}) as wait_mock:
            with patch.object(client, "set_post_task_evolution", return_value=None):
                with patch.object(
                    client,
                    "run_task",
                    return_value={"status": "completed", "summary": "done", "turns": 1},
                ):
                    with patch(
                        "bench_eval.ouroboros_client.sync_ouroboros_server_llm",
                        return_value={},
                    ):
                        result = run_ouroboros_full_task(
                            "do task",
                            config=config,
                            drive_root=tmp_path,
                            timeout_seconds=30.0,
                            max_retries=0,
                        )
    wait_mock.assert_called_once()
    assert result["is_done"] is True


def test_run_ouroboros_full_task_passes_llm_max_retries_to_subprocess_env(tmp_path, monkeypatch):
    config = load_ouroboros_harness_config("configs/ouroboros.full_isolated.json")
    monkeypatch.setenv("OUROBOROS_URL", "")
    captured_env = {}

    def fake_run(cmd, **kwargs):
        captured_env.update(kwargs.get("env", {}))
        return MagicMock(returncode=1, stdout="", stderr="cli failed")

    with patch("bench_eval.ouroboros_client.resolve_ouroboros_bin", return_value="/bin/ouroboros"):
        with patch("subprocess.run", side_effect=fake_run):
            run_ouroboros_full_task(
                "do task",
                config=config,
                drive_root=tmp_path,
                timeout_seconds=30.0,
                max_retries=4,
            )
    assert captured_env["LLM_MAX_RETRIES"] == "4"
    assert captured_env["PLAYWRIGHT_INSTALL_WITH_DEPS"] == "0"
    assert "PLAYWRIGHT_BROWSERS_PATH" in captured_env


def test_run_ouroboros_full_task_cli_uses_absolute_result_path(tmp_path):
    repo_dir = tmp_path / "ouroboros-src"
    repo_dir.mkdir()
    drive = tmp_path / "task-drive"
    relative_drive = Path(os.path.relpath(drive))
    config = replace(
        load_ouroboros_harness_config("configs/ouroboros.full_isolated.json"),
        ouroboros_url="",
        ouroboros_repo_dir=str(repo_dir),
    )
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        captured["env"] = kwargs.get("env", {})
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch("bench_eval.ouroboros_client.resolve_ouroboros_bin", return_value="/bin/ouroboros"):
        with patch("subprocess.run", side_effect=fake_run):
            run_ouroboros_full_task(
                "do task",
                config=config,
                drive_root=relative_drive,
                timeout_seconds=30.0,
                max_retries=0,
            )

    result_out = Path(captured["cmd"][captured["cmd"].index("--result-json-out") + 1])
    assert result_out.is_absolute()
    assert result_out == drive.resolve() / "ouroboros_task_result.json"
    assert Path(captured["env"]["OUROBOROS_DATA_DIR"]) == drive.resolve()
    assert captured["cwd"] == str(repo_dir)


def test_run_ouroboros_full_task_api_timeout_does_not_spawn_cli(tmp_path, monkeypatch):
    config = load_ouroboros_harness_config("configs/ouroboros.full_isolated.json")
    monkeypatch.setenv("OUROBOROS_URL", "http://127.0.0.1:9123")
    client = OuroborosHTTPClient("http://127.0.0.1:9123", max_retries=0)

    with patch("bench_eval.ouroboros_client.OuroborosHTTPClient", return_value=client):
        with patch.object(client, "health", return_value={"status": "ok"}):
            with patch.object(client, "set_post_task_evolution", return_value=None):
                with patch.object(
                    client,
                    "run_task",
                    side_effect=TimeoutError("Ouroboros task task-1 timed out after 600s"),
                ):
                    with patch(
                        "bench_eval.ouroboros_client.sync_ouroboros_server_llm",
                        return_value={},
                    ):
                        with patch("subprocess.run") as cli:
                            result = run_ouroboros_full_task(
                                "do task",
                                config=config,
                                drive_root=tmp_path,
                                timeout_seconds=30.0,
                                max_retries=0,
                            )
    cli.assert_not_called()
    assert result["is_done"] is False
    assert "timed out" in str(result.get("error") or "")
    assert result["harness_metadata"].get("api_timeout") is True


def test_run_ouroboros_full_task_cli_timeout_does_not_raise(tmp_path, monkeypatch):
    config = replace(
        load_ouroboros_harness_config("configs/ouroboros.full_isolated.json"),
        ouroboros_url="",
    )
    monkeypatch.setenv("OUROBOROS_URL", "")

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout"))

    with patch("bench_eval.ouroboros_client.resolve_ouroboros_bin", return_value="/bin/ouroboros"):
        with patch("subprocess.run", side_effect=fake_run):
            result = run_ouroboros_full_task(
                "do task",
                config=config,
                drive_root=tmp_path,
                timeout_seconds=5.0,
                max_retries=0,
            )
    assert result["is_done"] is False
    assert "timed out" in str(result.get("error") or "")
