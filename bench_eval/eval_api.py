"""HTTP service that runs one WebPageBench task through DeepEval.

The bench frontend, backend, and mocks are expected to be up already. This
process does not start them. A run executes the same entry point as
``scripts/run_eval.sh``:

``python -m deepeval test run tests/evals/test_agent_bench.py``

Model name, base URL, and API key are applied only to that child process.
The key is never written to ``results.json`` or to the status payload.

Start it from the repository root::

    python -m bench_eval.eval_api
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from bench_eval.harness_names import normalize_harness_name


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9100
_MAX_BODY_BYTES = 1_000_000
_RUN_ID_RE = re.compile(r"^[0-9a-f]{32}\Z")
_SECRET_KEYS = frozenset(
    {
        "api_key",
        "llm_api_key",
        "authorization",
        "token",
        "openai_api_key",
        "openrouter_api_key",
        "gigachat_token",
        "gigahf_token",
    }
)


def repo_root() -> Path:
    """Return the WebPageBench checkout that contains this package."""
    return Path(__file__).resolve().parents[1]


def resolve_llm_provider(*, provider: str | None, api_key_env: str | None, base_url: str) -> str:
    """Pick ``LLM_PROVIDER``. An explicit provider wins over the host heuristic."""
    explicit = (provider or "").strip().lower()
    if explicit:
        return explicit
    host = (urlsplit(base_url).hostname or "").lower()
    if api_key_env == "OPENROUTER_API_KEY" or host == "openrouter.ai" or host.endswith(".openrouter.ai"):
        return "openrouter"
    if host in {"127.0.0.1", "localhost"}:
        return "vllm"
    return "openai"


def deepeval_command() -> list[str]:
    """The same DeepEval test the shell wrapper launches, without extra workers."""
    return [
        sys.executable,
        "-m",
        "deepeval",
        "test",
        "run",
        "tests/evals/test_agent_bench.py",
    ]


def _safe_identifier(harness: str, model: str, run_id: str) -> str:
    raw = f"bench-{harness}-{model}-{run_id[:8]}"
    return re.sub(r"[^A-Za-z0-9._-]+", "-", raw)[:120]


def build_child_env(spec: dict[str, Any], base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Environment for one DeepEval child. Does not mutate the parent process."""
    child = dict(base_env if base_env is not None else os.environ)
    model = spec["model"]
    provider = resolve_llm_provider(
        provider=spec.get("provider"),
        api_key_env=model.get("api_key_env"),
        base_url=model["base_url"],
    )
    child["LLM_PROVIDER"] = provider
    child["LLM_MODEL"] = model["name"]
    child["LLM_BASE_URL"] = model["base_url"]
    child["AGENT_HARNESS"] = spec["harness"]
    child["EVAL_TASK_FILTER"] = spec["task_name"]
    child["EVAL_MAX_TASKS"] = "1"
    child["EVAL_OUTPUT_DIR"] = spec["output_dir"]
    child["EVAL_REBUILD_DATASET"] = "true"
    child["EVAL_TRACK_SUFFIX"] = spec["run_id"][:8]
    child["DEEPEVAL_IDENTIFIER"] = _safe_identifier(spec["harness"], model["name"], spec["run_id"])
    child["DEEPEVAL_EXTRA_ARGS"] = ""
    child["GUI_AGENT_BASE_URL"] = model["base_url"]
    child["GUI_AGENT_MODEL"] = model["name"]
    api_key = model.get("api_key")
    api_key_env = model.get("api_key_env")
    if api_key and api_key_env:
        child[str(api_key_env)] = str(api_key)
        child["LLM_API_KEY"] = str(api_key)
        child["GUI_AGENT_API_KEY"] = str(api_key)
    return child


def agent_completion_score(row: dict[str, Any]) -> float:
    """1.0 only when the agent reported the task done and did not fail."""
    agent = row.get("agent") or {}
    if agent.get("skipped"):
        return 0.0
    if agent.get("error") or row.get("agent_error"):
        return 0.0
    done = agent.get("is_done")
    if done is None:
        done = row.get("agent_is_done")
    return 1.0 if done else 0.0


def conditions_score(row: dict[str, Any]) -> float:
    """1.0 only when every WebPageBench telemetry condition passed."""
    dab = row.get("dab_check") or {}
    return 1.0 if dab.get("all_passed") else 0.0


def scores_from_results(path: Path, *, task_name: str | None = None) -> dict[str, Any]:
    """Read the two DeepEval verdicts from an existing ``results.json``."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    tests = payload.get("tests") or []
    row: dict[str, Any] = {}
    if task_name:
        for item in tests:
            if isinstance(item, dict) and item.get("test_name") == task_name:
                row = item
                break
    if not row and tests and isinstance(tests[0], dict):
        row = tests[0]
    agent = row.get("agent") or {}
    error = row.get("agent_error") or agent.get("error")
    return {
        "agent_completion": agent_completion_score(row),
        "conditions": conditions_score(row),
        "agent_error": None if error in (None, "") else str(error),
    }


def redact_text(text: str | None, secret: str | None) -> str | None:
    """Remove a request secret from a string that might be returned to the caller."""
    if text is None:
        return None
    if secret:
        return text.replace(secret, "***")
    return text


def _validate_base_url(base_url: str) -> str:
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("model.base_url must be an absolute http(s) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("model.base_url must not carry credentials, a query, or a fragment")
    return base_url


def _validate_task_name(task_name: str) -> str:
    if not task_name or any(char in task_name for char in "/\\\x00\n\r"):
        raise ValueError("task_name must be a single path-free task id")
    return task_name


def parse_run_request(body: dict[str, Any]) -> dict[str, Any]:
    """Validate a run body and return the fields the child process needs."""
    if not isinstance(body, dict):
        raise ValueError("run body must be a JSON object")
    task_name = _validate_task_name(str(body.get("task_name") or ""))
    harness = normalize_harness_name(str(body.get("harness") or "browser-use"))
    model = body.get("model")
    if not isinstance(model, dict):
        raise ValueError("model must be an object with name and base_url")
    name = str(model.get("name") or "").strip()
    if not name:
        raise ValueError("model.name is required")
    base_url = _validate_base_url(str(model.get("base_url") or "").strip())
    api_key_env = model.get("api_key_env")
    if api_key_env is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(api_key_env)):
        raise ValueError("model.api_key_env must be an environment variable name")
    provider = body.get("provider")
    if provider is not None and not str(provider).strip():
        provider = None
    return {
        "task_name": task_name,
        "harness": harness,
        "provider": None if provider is None else str(provider),
        "model": {
            "name": name,
            "base_url": base_url,
            "api_key_env": None if api_key_env is None else str(api_key_env),
            "api_key": None if model.get("api_key") in (None, "") else str(model.get("api_key")),
        },
    }


def list_tasks(root: Path | None = None) -> dict[str, Any]:
    """List bench tasks and a revision of their instruction text."""
    checkout = root or repo_root()
    tests_dir = checkout / "tests" / "bench"
    if not (tests_dir / "config.json").is_file():
        raise FileNotFoundError(f"bench catalog is not available at {tests_dir}")
    from bench_eval.dataset import build_test_configs

    configs = build_test_configs(str(tests_dir))
    frontend = os.environ.get("EVAL_FRONTEND_HOST", "127.0.0.1:5173")
    tasks: list[dict[str, str]] = []
    for _path, config in sorted(configs.items(), key=lambda item: item[0]):
        test_data = config.get("test_data") or {}
        name = str(test_data.get("test_name") or "")
        instruction = str(test_data.get("task") or "").replace("%HOST%", f"http://{frontend}")
        if name:
            tasks.append({"task_name": name, "instruction": instruction})
    revision_source = "\n".join(f"{item['task_name']}\n{item['instruction']}" for item in tasks)
    import hashlib

    revision = hashlib.sha256(revision_source.encode("utf-8")).hexdigest()[:16]
    return {"revision": revision, "tasks": tasks}


def list_harnesses() -> dict[str, Any]:
    """Canonical harness names this service can pass to DeepEval."""
    from bench_eval.harness_names import canonical_harness_names

    return {"harnesses": canonical_harness_names()}


def default_health_probe() -> dict[str, Any]:
    """Check that the already-running bench frontend and backend answer."""
    frontend = os.environ.get("EVAL_FRONTEND_HOST", "127.0.0.1:5173")
    backend = os.environ.get("EVAL_API_ADDRESS", "localhost:9000")
    frontend_ok = _tcp_http_ok(f"http://{frontend}/")
    backend_ok = _tcp_http_ok(f"http://{backend}/")
    return {
        "ok": frontend_ok and backend_ok,
        "frontend": frontend,
        "backend": backend,
        "frontend_ok": frontend_ok,
        "backend_ok": backend_ok,
    }


def _tcp_http_ok(url: str, timeout: float = 2.0) -> bool:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status < 500
    except urllib.error.HTTPError as exc:
        return exc.code < 500
    except Exception:
        return False


def run_deepeval_subprocess(spec: dict[str, Any]) -> dict[str, Any]:
    """Run DeepEval for one task and read the scores it wrote."""
    output_dir = Path(spec["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    identifier = _safe_identifier(spec["harness"], spec["model"]["name"], spec["run_id"])
    command = [*deepeval_command(), "--identifier", identifier]
    completed = subprocess.run(
        command,
        cwd=str(spec["repo_root"]),
        env=build_child_env(spec),
        check=False,
    )
    results_path = output_dir / "results.json"
    if not results_path.is_file():
        raise RuntimeError(f"deepeval exited {completed.returncode} without writing {results_path}")
    scores = scores_from_results(results_path, task_name=spec["task_name"])
    secret = spec["model"].get("api_key")
    scores["agent_error"] = redact_text(scores.get("agent_error"), secret)
    return {
        "status": "succeeded",
        "exit_code": completed.returncode,
        "results_path": str(results_path.resolve()),
        **scores,
    }


Runner = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class EvalApi:
    """One-run-at-a-time job registry in front of DeepEval."""

    root: Path = field(default_factory=repo_root)
    runner: Runner = run_deepeval_subprocess
    health_probe: Callable[[], dict[str, Any]] = default_health_probe
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _runs: dict[str, dict[str, Any]] = field(default_factory=dict)
    _threads: dict[str, threading.Thread] = field(default_factory=dict)

    def health(self) -> dict[str, Any]:
        return self.health_probe()

    def start_run(self, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """Accept one task. 409 when another DeepEval process is still running."""
        spec = parse_run_request(body)
        if not self._lock.acquire(blocking=False):
            return 409, {"error": "a run is already in progress"}
        run_id = uuid.uuid4().hex
        output_dir = self.root / "tests" / "eval" / "lighteval-service" / run_id
        spec["run_id"] = run_id
        spec["output_dir"] = str(output_dir)
        spec["repo_root"] = str(self.root)
        self._runs[run_id] = {
            "run_id": run_id,
            "status": "running",
            "task_name": spec["task_name"],
            "harness": spec["harness"],
            "model_name": spec["model"]["name"],
            "base_url": spec["model"]["base_url"],
            "api_key_env": spec["model"].get("api_key_env"),
            "agent_completion": None,
            "conditions": None,
            "results_path": None,
            "agent_error": None,
        }
        thread = threading.Thread(target=self._execute, args=(run_id, spec), daemon=True)
        self._threads[run_id] = thread
        try:
            thread.start()
        except Exception:
            self._runs.pop(run_id, None)
            self._threads.pop(run_id, None)
            self._lock.release()
            raise
        return 202, {"run_id": run_id, "status": "running"}

    def _execute(self, run_id: str, spec: dict[str, Any]) -> None:
        secret = spec["model"].get("api_key")
        try:
            outcome = self.runner(spec)
            public = self._runs[run_id]
            public["status"] = "succeeded"
            public["agent_completion"] = outcome.get("agent_completion")
            public["conditions"] = outcome.get("conditions")
            public["results_path"] = outcome.get("results_path")
            public["agent_error"] = redact_text(outcome.get("agent_error"), secret)
            public["exit_code"] = outcome.get("exit_code")
        except Exception as exc:
            public = self._runs[run_id]
            public["status"] = "failed"
            public["agent_completion"] = 0.0
            public["conditions"] = 0.0
            public["agent_error"] = redact_text(str(exc), secret)
        finally:
            self._lock.release()

    def get_run(self, run_id: str) -> tuple[int, dict[str, Any]]:
        if _RUN_ID_RE.fullmatch(run_id or "") is None:
            return 404, {"error": "unknown run"}
        record = self._runs.get(run_id)
        if record is None:
            return 404, {"error": "unknown run"}
        return 200, {key: value for key, value in record.items() if key.lower() not in _SECRET_KEYS}


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or "0")
    if length < 0 or length > _MAX_BODY_BYTES:
        raise ValueError("request body is too large")
    raw = handler.rfile.read(length) if length else b""
    if not raw:
        return {}
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("JSON body must be an object")
    return parsed


def _send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def get_response(service: EvalApi, path: str) -> tuple[int, dict[str, Any]]:
    """Route one GET. FileNotFoundError means the bench catalog is missing."""
    if path == "/v1/health":
        return 200, service.health()
    if path == "/v1/harnesses":
        return 200, list_harnesses()
    if path == "/v1/tasks":
        return 200, list_tasks(service.root)
    prefix = "/v1/runs/"
    if path.startswith(prefix):
        return service.get_run(path[len(prefix) :])
    return 404, {"error": "not found"}


def post_response(service: EvalApi, path: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Route one POST. Unknown paths are 404."""
    if path != "/v1/runs":
        return 404, {"error": "not found"}
    return service.start_run(body)


def build_handler(service: EvalApi) -> type[BaseHTTPRequestHandler]:
    """HTTP handler bound to one service instance. Bodies are not logged."""

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler name
            path = urlsplit(self.path).path
            try:
                status, payload = get_response(service, path)
            except FileNotFoundError as exc:
                _send_json(self, 503, {"error": str(exc)})
                return
            except Exception as exc:
                _send_json(self, 500, {"error": type(exc).__name__})
                return
            _send_json(self, status, payload)

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler name
            path = urlsplit(self.path).path
            try:
                body = _read_json_body(self) if path == "/v1/runs" else {}
                status, payload = post_response(service, path, body)
            except (ValueError, json.JSONDecodeError) as exc:
                _send_json(self, 400, {"error": str(exc)})
                return
            _send_json(self, status, payload)

    return Handler


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Listen until interrupted. One DeepEval run at a time."""
    service = EvalApi()
    server = ThreadingHTTPServer((host, port), build_handler(service))
    print(f"WebPageBench eval service on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main() -> None:
    host = os.environ.get("EVAL_SERVICE_HOST", DEFAULT_HOST)
    port = int(os.environ.get("EVAL_SERVICE_PORT", str(DEFAULT_PORT)))
    serve(host, port)


if __name__ == "__main__":
    main()
