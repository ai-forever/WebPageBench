"""Eval service contract without launching DeepEval or a browser."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from bench_eval.eval_api import (
    EvalApi,
    agent_completion_score,
    build_child_env,
    build_handler,
    conditions_score,
    deepeval_command,
    parse_run_request,
    resolve_llm_provider,
    scores_from_results,
)


def test_deepeval_command_is_the_bench_suite():
    command = deepeval_command()
    assert command[-3:] == ["test", "run", "tests/evals/test_agent_bench.py"]
    assert "--num-processes" not in command


def test_openrouter_key_is_injected_only_into_the_child_env():
    spec = parse_run_request(
        {
            "task_name": "demo_task",
            "harness": "browser-use",
            "model": {
                "name": "google/gemini-2.5-flash",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "api_key": "sk-or-test",
            },
        }
    )
    spec["run_id"] = "a" * 32
    spec["output_dir"] = "C:/tmp/out"
    child = build_child_env(spec, base_env={})
    assert child["LLM_PROVIDER"] == "openrouter"
    assert child["LLM_MODEL"] == "google/gemini-2.5-flash"
    assert child["LLM_BASE_URL"] == "https://openrouter.ai/api/v1"
    assert child["OPENROUTER_API_KEY"] == "sk-or-test"
    assert child["LLM_API_KEY"] == "sk-or-test"
    assert child["EVAL_TASK_FILTER"] == "demo_task"
    assert child["EVAL_MAX_TASKS"] == "1"
    assert child["AGENT_HARNESS"] == "browser-use"


def test_explicit_provider_overrides_the_localhost_heuristic():
    assert (
        resolve_llm_provider(
            provider="openai",
            api_key_env="OPENAI_API_KEY",
            base_url="http://127.0.0.1:8000/v1",
        )
        == "openai"
    )
    assert (
        resolve_llm_provider(provider=None, api_key_env=None, base_url="http://127.0.0.1:8000/v1")
        == "vllm"
    )


def test_scores_match_the_two_deepeval_metrics(tmp_path: Path):
    results = tmp_path / "results.json"
    results.write_text(
        json.dumps(
            {
                "tests": [
                    {
                        "test_name": "demo_task",
                        "agent_is_done": True,
                        "agent": {"is_done": True, "steps": 2},
                        "dab_check": {"all_passed": False, "score": 0.5, "passed": 1, "total": 2},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    scores = scores_from_results(results, task_name="demo_task")
    assert scores["agent_completion"] == 1.0
    assert scores["conditions"] == 0.0
    assert agent_completion_score({"agent": {"skipped": True, "is_done": True}}) == 0.0
    assert conditions_score({"dab_check": {"all_passed": True}}) == 1.0


def test_status_returns_both_scores_and_path_without_the_key(tmp_path: Path):
    secret = "sk-or-test-secret"
    seen: dict[str, object] = {}

    def runner(spec: dict) -> dict:
        seen["task"] = spec["task_name"]
        seen["key"] = spec["model"]["api_key"]
        return {
            "agent_completion": 1.0,
            "conditions": 1.0,
            "results_path": str(Path(spec["output_dir"]) / "results.json"),
            "agent_error": f"failed near {secret}",
            "exit_code": 1,
        }

    service = EvalApi(root=tmp_path, runner=runner, health_probe=lambda: {"ok": True})
    status, started = service.start_run(
        {
            "task_name": "demo_task",
            "harness": "openhands",
            "model": {
                "name": "local-model",
                "base_url": "http://127.0.0.1:8000/v1",
                "api_key_env": "OPENAI_API_KEY",
                "api_key": secret,
            },
        }
    )
    assert status == 202
    service._threads[started["run_id"]].join(timeout=5)
    code, payload = service.get_run(started["run_id"])
    assert code == 200
    assert payload["status"] == "succeeded"
    assert payload["agent_completion"] == 1.0
    assert payload["conditions"] == 1.0
    assert str(payload["results_path"]).endswith("results.json")
    encoded = json.dumps(payload)
    assert secret not in encoded
    assert "***" in encoded
    assert seen["task"] == "demo_task"
    assert seen["key"] == secret


def test_http_run_round_trip_hides_the_key(tmp_path: Path):
    secret = "sk-or-http"

    def runner(spec: dict) -> dict:
        return {
            "agent_completion": 0.0,
            "conditions": 1.0,
            "results_path": "D:/bench/results.json",
            "agent_error": None,
            "exit_code": 0,
        }

    service = EvalApi(root=tmp_path, runner=runner, health_probe=lambda: {"ok": True, "frontend_ok": True})
    server = ThreadingHTTPServer(("127.0.0.1", 0), build_handler(service))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    port = server.server_address[1]
    try:
        body = json.dumps(
            {
                "task_name": "demo_task",
                "harness": "browser-use",
                "model": {
                    "name": "m",
                    "base_url": "http://127.0.0.1:8000/v1",
                    "api_key": secret,
                    "api_key_env": "OPENAI_API_KEY",
                },
            }
        ).encode("utf-8")
        request = Request(
            f"http://127.0.0.1:{port}/v1/runs",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            started = json.loads(response.read().decode("utf-8"))
            assert response.status == 202
        service._threads[started["run_id"]].join(timeout=5)
        with urlopen(f"http://127.0.0.1:{port}/v1/runs/{started['run_id']}", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["conditions"] == 1.0
        assert payload["agent_completion"] == 0.0
        assert payload["results_path"] == "D:/bench/results.json"
        assert secret not in json.dumps(payload)
        with urlopen(f"http://127.0.0.1:{port}/v1/health", timeout=5) as response:
            health = json.loads(response.read().decode("utf-8"))
        assert health["ok"] is True
    finally:
        server.shutdown()
        server.server_close()
