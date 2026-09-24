"""HTTP/subprocess client for external Ouroboros (razzant/ouroboros)."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

from bench_eval.ouroboros_config import OuroborosHarnessConfig
from bench_eval.ouroboros_llm_sync import (
    build_ouroboros_llm_settings,
    collect_ouroboros_model_slots,
    merge_ouroboros_llm_env,
    sync_ouroboros_server_llm,
)
from bench_eval.playwright_runtime import apply_playwright_env_to, repo_root_from_env
from bench_eval.retry_utils import is_retryable_http_status, retry_backoff_seconds
from bench_eval.token_usage import (
    ModelTokenUsage,
    TokenUsage,
    merge_token_usage,
    merge_token_usage_by_model,
    normalize_model_token_usage,
    normalize_token_usage,
    tag_model_roles,
)

_SETTLED_STATUSES = frozenset({"completed", "failed", "cancelled", "rejected_duplicate"})
_QUEUE_STUCK_STATUSES = frozenset({"pending", "queued", "assigned"})
_QUEUE_STUCK_WARN_SECONDS = 120.0
_QUEUE_STUCK_FAIL_SECONDS = 300.0
_DEFAULT_RESTART_READY_TIMEOUT_SECONDS = 120.0
_CLI_GRACE_SECONDS = 60.0


def _decode_subprocess_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)):
        return "".join(_decode_subprocess_output(item) for item in value)
    return str(value)
_DEFAULT_RESTART_READY_POLL_SECONDS = 1.0


def resolve_ouroboros_restart_ready_timeout(env: Optional[dict[str, str]] = None) -> float:
    """Max seconds to wait for Ouroboros to become ready after an evolution restart."""
    source = env if env is not None else os.environ
    raw = (source.get("OUROBOROS_RESTART_READY_TIMEOUT") or "").strip()
    if not raw:
        return _DEFAULT_RESTART_READY_TIMEOUT_SECONDS
    try:
        return max(0.0, float(raw))
    except ValueError:
        return _DEFAULT_RESTART_READY_TIMEOUT_SECONDS


def resolve_ouroboros_restart_ready_poll_interval(env: Optional[dict[str, str]] = None) -> float:
    source = env if env is not None else os.environ
    raw = (source.get("OUROBOROS_RESTART_READY_POLL") or "").strip()
    if not raw:
        return _DEFAULT_RESTART_READY_POLL_SECONDS
    try:
        return max(0.1, float(raw))
    except ValueError:
        return _DEFAULT_RESTART_READY_POLL_SECONDS


def health_indicates_ready(health: dict[str, Any]) -> bool:
    """Return True when /api/health indicates the server can accept tasks."""
    if not health:
        return True
    status = str(health.get("status") or "").strip().lower()
    if status and status not in {"ok", "healthy", "ready", "up"}:
        return False
    for key in ("supervisor_ready", "ready", "accepting_tasks"):
        if key in health:
            return bool(health.get(key))
    return True


class OuroborosUnavailableError(RuntimeError):
    """Raised when a full ouroboros mode is selected but runtime is not reachable."""


class OuroborosHTTPClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, max_retries)

    def request(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    payload = response.read().decode("utf-8")
                    if not payload.strip():
                        return {}
                    parsed = json.loads(payload)
                    return parsed if isinstance(parsed, dict) else {"data": parsed}
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last_error = RuntimeError(
                    f"Ouroboros API {method} {path} failed: {exc.code} {detail}"
                )
                if is_retryable_http_status(exc.code) and attempt < self.max_retries:
                    time.sleep(retry_backoff_seconds(attempt))
                    continue
                raise last_error from exc
            except urllib.error.URLError as exc:
                last_error = OuroborosUnavailableError(
                    f"Ouroboros API unreachable at {self.base_url}: {exc}"
                )
                if attempt < self.max_retries:
                    time.sleep(retry_backoff_seconds(attempt))
                    continue
                raise last_error from exc

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Ouroboros API {method} {path} failed without an exception")

    def health(self) -> dict[str, Any]:
        return self.request("GET", "/api/health")

    def wait_until_ready(
        self,
        *,
        timeout_seconds: Optional[float] = None,
        poll_interval: Optional[float] = None,
        label: str = "Ouroboros",
    ) -> dict[str, Any]:
        """
        Poll /api/health until the server is reachable and reports ready.

        Used after post-task evolution triggers an Ouroboros restart (exit code 42)
        so the next benchmark task does not start against a wedged supervisor.
        """
        deadline = time.perf_counter() + (
            timeout_seconds
            if timeout_seconds is not None
            else resolve_ouroboros_restart_ready_timeout()
        )
        interval = (
            poll_interval
            if poll_interval is not None
            else resolve_ouroboros_restart_ready_poll_interval()
        )
        last_error: Optional[Exception] = None
        poll = 0
        while True:
            try:
                health = self.health()
                if health_indicates_ready(health):
                    if poll > 0:
                        print(
                            f"[ouroboros] {label} ready after restart "
                            f"({poll} poll(s))",
                            flush=True,
                        )
                    return health
                last_error = RuntimeError(
                    f"health not ready: {health!r}"
                )
            except OuroborosUnavailableError as exc:
                last_error = exc
            except RuntimeError as exc:
                last_error = exc

            if time.perf_counter() >= deadline:
                detail = str(last_error) if last_error is not None else "unknown error"
                raise TimeoutError(
                    f"{label} not ready within "
                    f"{timeout_seconds or resolve_ouroboros_restart_ready_timeout()}s: "
                    f"{detail}"
                ) from last_error

            if poll == 0:
                print(
                    f"[ouroboros] waiting for {label} to become ready after restart...",
                    flush=True,
                )
            elif poll % 15 == 0:
                waited = int(time.perf_counter() - (deadline - (
                    timeout_seconds or resolve_ouroboros_restart_ready_timeout()
                )))
                print(
                    f"[ouroboros] still waiting for {label} ({waited}s)...",
                    flush=True,
                )
            poll += 1
            time.sleep(interval)

    def set_post_task_evolution(self, enabled: bool) -> None:
        self.request(
            "POST",
            "/api/settings",
            {"OUROBOROS_POST_TASK_EVOLUTION": enabled},
        )

    def apply_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        if not settings:
            return {}
        return self.request("POST", "/api/settings", settings)

    def wait_task(self, task_id: str, *, timeout_seconds: float) -> dict[str, Any]:
        deadline = time.perf_counter() + timeout_seconds if timeout_seconds > 0 else None
        last_status = ""
        status_since = time.perf_counter()
        poll = 0
        while True:
            result = self.request("GET", f"/api/tasks/{urllib.parse.quote(task_id)}")
            status = str(result.get("status") or "").lower()
            artifact_status = str(result.get("artifact_status") or "").lower()
            if status != last_status:
                print(
                    f"[ouroboros] task {task_id}: status={status or '?'} "
                    f"artifact_status={artifact_status or '-'}",
                    flush=True,
                )
                last_status = status
                status_since = time.perf_counter()
            elif poll % 15 == 0 and status in _QUEUE_STUCK_STATUSES:
                stuck_for = time.perf_counter() - status_since
                print(
                    f"[ouroboros] task {task_id}: still {status} ({int(stuck_for)}s)",
                    flush=True,
                )
            if status in _SETTLED_STATUSES and artifact_status not in {"pending", "finalizing"}:
                return result
            if (
                status in _QUEUE_STUCK_STATUSES
                and time.perf_counter() - status_since >= _QUEUE_STUCK_FAIL_SECONDS
            ):
                raise TimeoutError(
                    f"Ouroboros task {task_id} stuck in {status} for "
                    f"{int(_QUEUE_STUCK_FAIL_SECONDS)}s (supervisor queue wedged or "
                    "budget exhausted on shared OUROBOROS_DATA_DIR; parallel runs need "
                    "separate data roots)"
                )
            if deadline is not None and time.perf_counter() >= deadline:
                raise TimeoutError(f"Ouroboros task {task_id} timed out after {timeout_seconds}s")
            poll += 1
            time.sleep(2.0)

    def run_task(
        self,
        prompt: str,
        *,
        memory_mode: str,
        timeout_seconds: float,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "description": prompt,
            "memory_mode": memory_mode,
            "metadata": metadata or {"source": "dab-eval"},
            "source": "dab-eval",
        }
        created = self.request("POST", "/api/tasks", body)
        task_id = str(created.get("task_id") or "")
        if not task_id:
            raise RuntimeError(f"Ouroboros task creation returned no task_id: {created}")
        print(
            f"[ouroboros] created task {task_id} memory_mode={memory_mode}",
            flush=True,
        )
        return self.wait_task(task_id, timeout_seconds=timeout_seconds)


def resolve_ouroboros_bin(config: OuroborosHarnessConfig) -> str:
    binary = (config.ouroboros_bin or "ouroboros").strip()
    if Path(binary).expanduser().is_file():
        return str(Path(binary).expanduser())
    resolved = shutil.which(binary)
    if resolved:
        return resolved
    raise OuroborosUnavailableError(
        f"Ouroboros binary {binary!r} not found. Install razzant/ouroboros and set OUROBOROS_BIN."
    )


def check_ouroboros_available(
    config: OuroborosHarnessConfig,
    *,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Verify ouroboros HTTP API or local binary is available."""
    details: dict[str, Any] = {"url": config.ouroboros_url, "bin": config.ouroboros_bin}
    if config.ouroboros_url:
        try:
            client = OuroborosHTTPClient(
                config.ouroboros_url,
                timeout=10.0,
                max_retries=max_retries,
            )
            health = client.health()
            details["health"] = health
            details["ok"] = True
            return details
        except OuroborosUnavailableError:
            pass
    try:
        binary = resolve_ouroboros_bin(config)
        completed = subprocess.run(
            [binary, "status", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        details["bin_path"] = binary
        details["status_returncode"] = completed.returncode
        if completed.returncode == 0:
            details["ok"] = True
            try:
                details["status"] = json.loads(completed.stdout or "{}")
            except json.JSONDecodeError:
                details["status_raw"] = completed.stdout
            return details
    except OuroborosUnavailableError as exc:
        details["error"] = str(exc)
    details["ok"] = False
    return details


def run_ouroboros_full_task(
    prompt: str,
    *,
    config: OuroborosHarnessConfig,
    drive_root: Path,
    timeout_seconds: float,
    max_retries: int = 3,
) -> dict[str, Any]:
    """
    Run a full ouroboros task (full_isolated or full_evolving).

    Uses HTTP API when the server is reachable; otherwise spawns `ouroboros run`.
    """
    # CLI cwd is OUROBOROS_REPO_DIR (often "ouroboros"). Relative eval paths
    # like tests/eval/.../ouroboros_task_result.json then miss their parent.
    drive_root = Path(drive_root).expanduser()
    drive_root.mkdir(parents=True, exist_ok=True)
    drive_root = drive_root.resolve()
    result_path = drive_root / "ouroboros_task_result.json"
    env = merge_ouroboros_llm_env(os.environ)
    apply_playwright_env_to(env, repo_root_from_env())
    env["OUROBOROS_DATA_DIR"] = str(drive_root)
    env["OUROBOROS_POST_TASK_EVOLUTION"] = "true" if config.evolution_enabled else "false"
    env.setdefault("LLM_MAX_RETRIES", str(max_retries))

    api_error: Optional[str] = None
    llm_sync: dict[str, str] = {}
    started_at = time.perf_counter()
    if config.ouroboros_url:
        try:
            print(
                f"[ouroboros] full task via API: memory_mode={config.memory_mode} "
                f"timeout={timeout_seconds}s drive_root={drive_root}",
                flush=True,
            )
            client = OuroborosHTTPClient(
                config.ouroboros_url,
                timeout=30.0,
                max_retries=max_retries,
            )
            if config.evolution_enabled:
                client.wait_until_ready(label="Ouroboros API (pre-task)")
            else:
                client.health()
            llm_sync = sync_ouroboros_server_llm(client, env=env)
            if config.evolution_enabled:
                client.set_post_task_evolution(True)
            else:
                client.set_post_task_evolution(False)
            payload = client.run_task(
                prompt,
                memory_mode=config.memory_mode,
                timeout_seconds=timeout_seconds,
                metadata={
                    "source": "dab-eval",
                    "mode": config.mode,
                    "dab_drive_root": str(drive_root),
                },
            )
            result_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return _normalize_ouroboros_result(
                payload,
                duration_seconds=time.perf_counter() - started_at,
                executor="ouroboros-api",
                llm_sync=llm_sync,
                drive_root=drive_root,
            )
        except TimeoutError as exc:
            # Task already consumed the budget on the server; do not start a
            # second 600s CLI run of the same prompt.
            result = _normalize_ouroboros_result(
                {},
                duration_seconds=time.perf_counter() - started_at,
                executor="ouroboros-api",
                llm_sync=llm_sync or build_ouroboros_llm_settings(env),
                drive_root=drive_root,
                cli_stderr=str(exc),
            )
            result["error"] = str(exc)
            result.setdefault("harness_metadata", {})["api_timeout"] = True
            return result
        except (OuroborosUnavailableError, RuntimeError) as exc:
            api_error = str(exc)
            print(f"[ouroboros] API unavailable, falling back to CLI: {api_error}", flush=True)

    binary = resolve_ouroboros_bin(config)
    cmd = [binary]
    if config.ouroboros_url:
        cmd.extend(["--url", config.ouroboros_url])
    cmd.extend(
        [
            "run",
            "--memory-mode",
            config.memory_mode,
            "--result-json-out",
            str(result_path),
            "--timeout",
            str(int(timeout_seconds)) if timeout_seconds > 0 else "0",
            prompt,
        ]
    )
    # Let Ouroboros logs reach the eval terminal. capture_output=True deadlocks
    # when the CLI fills the pipe buffer (typical with verbose browser logs).
    subprocess_timeout = (
        timeout_seconds + _CLI_GRACE_SECONDS
        if timeout_seconds and timeout_seconds > 0
        else None
    )
    print(
        f"[ouroboros] full task via CLI: timeout={timeout_seconds}s "
        f"subprocess_timeout={subprocess_timeout}s",
        flush=True,
    )
    started_at = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            cwd=config.ouroboros_repo_dir or None,
            env=env,
            text=True,
            timeout=subprocess_timeout,
            check=False,
        )
        cli_returncode = completed.returncode
        cli_stdout = _decode_subprocess_output(completed.stdout)
        cli_stderr = _decode_subprocess_output(completed.stderr)
    except subprocess.TimeoutExpired as exc:
        cli_returncode = -1
        cli_stdout = _decode_subprocess_output(exc.stdout)
        cli_stderr = _decode_subprocess_output(exc.stderr) or (
            f"Ouroboros CLI timed out after {subprocess_timeout}s "
            f"(task --timeout {int(timeout_seconds) if timeout_seconds else 0}s)"
        )
    duration_seconds = time.perf_counter() - started_at
    payload: dict[str, Any] = {}
    if result_path.is_file():
        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
    result = _normalize_ouroboros_result(
        payload,
        duration_seconds=duration_seconds,
        executor="ouroboros-cli",
        cli_returncode=cli_returncode,
        cli_stdout=cli_stdout,
        cli_stderr=cli_stderr,
        llm_sync=build_ouroboros_llm_settings(env),
        drive_root=drive_root,
    )
    if api_error:
        result.setdefault("harness_metadata", {})["api_fallback_reason"] = api_error
    if cli_returncode != 0 and not result.get("final_result"):
        result["error"] = cli_stderr or cli_stdout or api_error
    return result


def _coerce_non_negative_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float) and value.is_integer():
        coerced = int(value)
        return coerced if coerced >= 0 else None
    return None


def _mapping_value(payload: Any, *keys: str) -> Any:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _extract_ouroboros_final_result(payload: dict[str, Any]) -> Optional[str]:
    """Prefer deliverable text over the task description echoed in API payloads."""
    description = str(payload.get("description") or "").strip()
    loop_outcome = _mapping_value(payload, "loop_outcome")
    loop_outcome = loop_outcome if isinstance(loop_outcome, dict) else {}
    candidates: list[str] = []
    for source in (payload, loop_outcome):
        if not isinstance(source, dict):
            continue
        for key in ("final_answer", "summary", "final_text", "result"):
            text = str(source.get(key) or "").strip()
            if text:
                candidates.append(text)
    for text in candidates:
        if description and text == description:
            continue
        return text
    return candidates[0] if candidates else None


def _extract_ouroboros_steps(payload: dict[str, Any]) -> int:
    loop_outcome = _mapping_value(payload, "loop_outcome")
    loop_outcome = loop_outcome if isinstance(loop_outcome, dict) else {}
    loop_usage = loop_outcome.get("usage") if isinstance(loop_outcome.get("usage"), dict) else {}
    for source in (payload, loop_usage, loop_outcome):
        if not isinstance(source, dict):
            continue
        for key in ("total_rounds", "turns", "steps", "rounds"):
            value = _coerce_non_negative_int(source.get(key))
            if value is not None and value > 0:
                return value
    for source in (payload, loop_usage, loop_outcome):
        if not isinstance(source, dict):
            continue
        for key in ("total_rounds", "turns", "steps", "rounds"):
            value = _coerce_non_negative_int(source.get(key))
            if value is not None:
                return value
    return 0


def _llm_usage_event_cost(event: dict[str, Any]) -> float:
    usage = event.get("usage")
    value = event.get("cost")
    if value is None and isinstance(usage, dict):
        value = usage.get("cost")
    try:
        cost = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return cost if math.isfinite(cost) else 0.0


def _iter_llm_usage_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and payload.get("type") == "llm_usage":
                events.append(payload)
    except OSError:
        return []
    return events


def _aggregate_ouroboros_events_by_model(
    events_path: Path,
    *,
    task_id: str | None = None,
) -> dict[str, ModelTokenUsage]:
    """Aggregate Ouroboros ``llm_usage`` rows from ``logs/events.jsonl`` by model."""
    by_model: dict[str, ModelTokenUsage] = {}
    for event in _iter_llm_usage_events(events_path):
        if task_id and str(event.get("task_id") or "") != task_id:
            continue
        model = str(event.get("model") or "unknown").strip() or "unknown"
        entry = by_model.setdefault(model, normalize_model_token_usage({}))
        entry["llm_calls"] = int(entry.get("llm_calls") or 0) + 1
        for field in ("prompt_tokens", "completion_tokens"):
            try:
                value = int(event.get(field) or 0)
            except (TypeError, ValueError):
                value = 0
            entry[field] = int(entry.get(field) or 0) + max(value, 0)
        entry["total_tokens"] = int(entry.get("prompt_tokens") or 0) + int(
            entry.get("completion_tokens") or 0
        )
        cost = _llm_usage_event_cost(event)
        if cost > 0:
            entry["cost_usd"] = float(entry.get("cost_usd") or 0.0) + cost
    return by_model


def _fallback_usage_by_model_from_payload(payload: dict[str, Any]) -> dict[str, ModelTokenUsage]:
    """Best-effort single-bucket usage when per-model events are unavailable."""
    loop_outcome = _mapping_value(payload, "loop_outcome")
    loop_outcome = loop_outcome if isinstance(loop_outcome, dict) else {}
    loop_usage = loop_outcome.get("usage") if isinstance(loop_outcome.get("usage"), dict) else {}
    usage = merge_token_usage(
        normalize_token_usage(payload),
        normalize_token_usage(loop_usage),
        normalize_token_usage(loop_outcome),
    )
    llm_calls = int(usage.get("llm_calls") or 0)
    if llm_calls == 0:
        for source in (payload, loop_outcome):
            if not isinstance(source, dict):
                continue
            trace_refs = source.get("trace_refs")
            if not isinstance(trace_refs, dict):
                continue
            refs = trace_refs.get("llm_call_refs")
            if isinstance(refs, list):
                llm_calls = max(llm_calls, len(refs))
    if not any(
        (
            usage["prompt_tokens"],
            usage["completion_tokens"],
            usage["total_tokens"],
            llm_calls,
        )
    ):
        return {}

    model = str(payload.get("model") or loop_outcome.get("model") or "unknown").strip() or "unknown"
    cost_usd = None
    for source in (loop_usage, loop_outcome, payload):
        if not isinstance(source, dict):
            continue
        for key in ("cost_usd", "total_cost_usd", "cost", "total_cost"):
            value = source.get(key)
            if isinstance(value, (int, float)) and float(value) > 0:
                cost_usd = float(value)
                break
        if cost_usd is not None:
            break

    entry_fields: dict[str, Any] = {
        **usage,
        "llm_calls": llm_calls,
    }
    if cost_usd is not None and cost_usd > 0:
        entry_fields["cost_usd"] = cost_usd
    entry = normalize_model_token_usage(entry_fields)
    return {model: entry}


def _extract_ouroboros_token_usage_by_model(
    payload: dict[str, Any],
    *,
    drive_root: Path | None = None,
    model_slots: dict[str, list[str]] | None = None,
) -> dict[str, ModelTokenUsage]:
    task_id = str(payload.get("task_id") or "").strip() or None
    by_model: dict[str, ModelTokenUsage] = {}
    if drive_root is not None:
        events_path = drive_root / "logs" / "events.jsonl"
        by_model = _aggregate_ouroboros_events_by_model(events_path, task_id=task_id)

    if not by_model:
        by_model = _fallback_usage_by_model_from_payload(payload)

    if model_slots:
        by_model = tag_model_roles(by_model, model_slots=model_slots)
    return by_model


def _extract_ouroboros_token_usage(payload: dict[str, Any]) -> TokenUsage:
    loop_outcome = _mapping_value(payload, "loop_outcome")
    loop_outcome = loop_outcome if isinstance(loop_outcome, dict) else {}
    loop_usage = loop_outcome.get("usage") if isinstance(loop_outcome.get("usage"), dict) else {}
    usage = merge_token_usage(
        normalize_token_usage(payload),
        normalize_token_usage(loop_usage),
        normalize_token_usage(loop_outcome),
    )
    if usage["llm_calls"] == 0:
        llm_calls = 0
        for source in (payload, loop_outcome):
            if not isinstance(source, dict):
                continue
            trace_refs = source.get("trace_refs")
            if not isinstance(trace_refs, dict):
                continue
            refs = trace_refs.get("llm_call_refs")
            if isinstance(refs, list):
                llm_calls = max(llm_calls, len(refs))
        if llm_calls > 0:
            usage = dict(usage)
            usage["llm_calls"] = llm_calls
    return usage


def _normalize_ouroboros_result(
    payload: dict[str, Any],
    *,
    duration_seconds: float,
    executor: str,
    cli_returncode: Optional[int] = None,
    cli_stdout: str = "",
    cli_stderr: str = "",
    llm_sync: Optional[dict[str, str]] = None,
    drive_root: Path | None = None,
) -> dict[str, Any]:
    status = str(payload.get("status") or "").lower()
    final_result = (
        _extract_ouroboros_final_result(payload)
        or payload.get("summary")
        or (cli_stdout or "").strip()
        or (cli_stderr or "").strip()
        or payload.get("description")
    )
    is_done = status == "completed"
    if cli_returncode is not None and cli_returncode != 0 and not is_done:
        is_done = False
    harness_metadata: dict[str, Any] = {"executor": executor}
    model_slots: dict[str, list[str]] = {}
    if llm_sync:
        model_slots = collect_ouroboros_model_slots(llm_sync)
        harness_metadata["ouroboros_llm_sync"] = {
            "model": llm_sync.get("OUROBOROS_MODEL"),
            "provider_model": llm_sync.get("OUROBOROS_MODEL"),
            "model_slots": model_slots,
            "keys": sorted(llm_sync.keys()),
        }
    token_usage = _extract_ouroboros_token_usage(payload)
    token_usage_by_model = _extract_ouroboros_token_usage_by_model(
        payload,
        drive_root=drive_root,
        model_slots=model_slots or None,
    )
    if token_usage_by_model:
        merged_total = merge_token_usage_by_model(token_usage_by_model)
        if merged_total:
            derived = normalize_token_usage(
                {
                    "prompt_tokens": sum(row.get("prompt_tokens", 0) for row in merged_total.values()),
                    "completion_tokens": sum(
                        row.get("completion_tokens", 0) for row in merged_total.values()
                    ),
                    "total_tokens": sum(row.get("total_tokens", 0) for row in merged_total.values()),
                    "llm_calls": sum(row.get("llm_calls", 0) for row in merged_total.values()),
                }
            )
            if int(derived["llm_calls"] or 0) < int(token_usage["llm_calls"] or 0):
                derived = dict(derived)
                derived["llm_calls"] = token_usage["llm_calls"]
            token_usage = derived
    return {
        "final_result": final_result,
        "steps": _extract_ouroboros_steps(payload),
        "is_done": is_done,
        "duration_seconds": duration_seconds,
        "token_usage": token_usage,
        "token_usage_by_model": token_usage_by_model,
        "ouroboros_result": payload,
        "harness_metadata": harness_metadata,
        "error": None if is_done else (cli_stderr or cli_stdout or status or None),
    }
