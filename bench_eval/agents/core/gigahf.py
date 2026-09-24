"""GigaHF transport (``gigahf.sberdevices.ru``) for the GUI-agent client.

GigaHF serves models behind an OpenAI-shaped chat-completions API, so the
message format the bench already builds — text parts plus ``image_url`` data
URIs — goes over unchanged. Two details make the plain :class:`VLMClient`
unusable for a benchmark run, and this module exists to handle them:

* the synchronous ``POST /chat/completions`` is capped at **10 requests per
  minute per IP** (HTTP 429). One bench task alone spends up to
  ``AGENT_MAX_STEPS`` calls, so a 152-task run would spend its life throttled.
  The async pair — ``POST /async/chat/completions`` then
  ``GET /async/chat/completions/{id}`` until the task reports ``ready`` — is
  limited at ~150 RPS instead, and is what this client uses by default.
* request fields outside the documented schema are rejected rather than
  ignored, so anything extra has to travel inside ``extra_params``.

The host is also signed by an internal CA, so this transport turns TLS
verification off (``ssl_verify = False``) rather than asking for a bundle.

Set ``GIGAHF_MODE=sync`` to use the synchronous endpoint anyway (a client-side
limiter of ``GIGAHF_SYNC_RPM`` requests/minute keeps it under the cap, and a
504 is resumed through the async result endpoint). Note the limiter lives in
one process: DeepEval runs its workers as separate processes, so with
``--num-processes N`` the effective ceiling is N times that value.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional

from bench_eval.agents.core.client import (
    Endpoint,
    TokenLedger,
    TransientError,
    VLMClient,
)
from bench_eval.agents.core.dump import CallDumper, CallRecord

#: Top-level fields ``ChatCompletionRequestJSON`` accepts; everything else must
#: be nested under ``extra_params`` (GigaHF API v1.15).
REQUEST_FIELDS = frozenset(
    {
        "model",
        "messages",
        "max_tokens",
        "min_tokens",
        "temperature",
        "top_p",
        "top_k",
        "min_p",
        "stop",
        "seed",
        "n",
        "frequency_penalty",
        "presence_penalty",
        "repetition_penalty",
        "reasoning_effort",
        "response_format",
        "response_attachments_format",
        "return_images",
        "request_type",
        "truncation",
        "tools",
        "tool_choice",
        "extra_params",
    }
)

#: Statuses ``GET /async/chat/completions/{id}`` can report.
_TERMINAL_FAILURES = {"failed", "cancelled", "unknown_query_id"}


def _env_float(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    return float(raw) if raw else default


def _env_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    return int(raw) if raw else default


@dataclass(frozen=True)
class GigaHFOptions:
    """Transport knobs, all overridable from the run env."""

    #: ``async`` (submit + poll, ~150 RPS) or ``sync`` (one call, 10 RPM).
    mode: str = "async"
    poll_interval: float = 2.0
    poll_max_interval: float = 15.0
    poll_timeout: float = 900.0
    #: Client-side ceiling for ``sync`` mode; 0 disables the limiter.
    sync_rpm: int = 10
    #: Merged into every request's ``extra_params`` (e.g. ``model_path``).
    extra_params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls, *, prefix: str = "GIGAHF") -> "GigaHFOptions":
        raw_extra = (os.getenv(f"{prefix}_EXTRA_PARAMS") or "").strip()
        extra_params = json.loads(raw_extra) if raw_extra else {}
        mode = (os.getenv(f"{prefix}_MODE") or "async").strip().lower()
        if mode not in {"async", "sync"}:
            raise ValueError(
                f"{prefix}_MODE must be 'async' or 'sync', got {mode!r}"
            )
        return cls(
            mode=mode,
            poll_interval=_env_float(f"{prefix}_POLL_INTERVAL", 2.0),
            poll_max_interval=_env_float(f"{prefix}_POLL_MAX_INTERVAL", 15.0),
            poll_timeout=_env_float(f"{prefix}_POLL_TIMEOUT", 900.0),
            sync_rpm=_env_int(f"{prefix}_SYNC_RPM", 10),
            extra_params=extra_params,
        )


class RateGate:
    """Sliding-window limiter: at most ``per_minute`` acquisitions per 60s."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._stamps: deque[float] = deque()
        self._lock: Optional[asyncio.Lock] = None

    async def acquire(self) -> None:
        if self.per_minute <= 0:
            return
        if self._lock is None:
            # Built lazily so the gate can be constructed outside a running loop.
            self._lock = asyncio.Lock()
        async with self._lock:
            while True:
                now = time.monotonic()
                while self._stamps and now - self._stamps[0] >= 60.0:
                    self._stamps.popleft()
                if len(self._stamps) < self.per_minute:
                    self._stamps.append(now)
                    return
                await asyncio.sleep(60.0 - (now - self._stamps[0]))


class GigaHFClient(VLMClient):
    """Chat-completions client that submits to GigaHF and polls for the result."""

    #: GigaHF is signed by the SberDevices internal root CA, which certifi does
    #: not carry — httpx would fail the handshake where curl succeeds.
    ssl_verify = False

    def __init__(
        self,
        endpoint: Endpoint,
        *,
        ledger: Optional[TokenLedger] = None,
        dumper: Optional[CallDumper] = None,
        options: Optional[GigaHFOptions] = None,
    ) -> None:
        super().__init__(endpoint, ledger=ledger, dumper=dumper)
        self.options = options or GigaHFOptions.from_env()
        self._gate = RateGate(self.options.sync_rpm)
        if not endpoint.api_key or endpoint.api_key == "EMPTY":
            raise ValueError(
                "GigaHF needs a bearer token: set GUI_AGENT_API_KEY (or GIGAHF_TOKEN "
                "in envs/_gigahf.env, see envs/_gigahf.env.example)."
            )

    # ------------------------------------------------------------- transport

    async def _post_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = self.build_request(payload)
        if self.options.mode == "sync":
            return await self._sync_completion(request)
        return await self._async_completion(request)

    def build_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Reshape an OpenAI payload into ``ChatCompletionRequestJSON``."""
        request = {k: v for k, v in payload.items() if k in REQUEST_FIELDS}
        unknown = {k: v for k, v in payload.items() if k not in REQUEST_FIELDS}
        extra = {
            **self.options.extra_params,
            **(payload.get("extra_params") or {}),
            **unknown,
        }
        if extra:
            request["extra_params"] = extra
        return request

    async def _sync_completion(self, request: dict[str, Any]) -> dict[str, Any]:
        await self._gate.acquire()
        client = await self._http()
        record = self._start_record(
            transport="gigahf-sync",
            path="/chat/completions",
            body=request,
            request=request,
        )
        try:
            response = await client.post("/chat/completions", json=request)
            if response.status_code == 504:
                # Documented behaviour: the coordinator kept the job, take the id
                # and collect the answer through the async result endpoint.
                request_id = _request_id_from_body(response)
                if request_id:
                    record.note(gigahf={"resumed_after_504": True, "request_id": request_id})
                    result = await self.await_result(request_id, record=record)
                    record.finish(response=result)
                    return result
            self._raise_for_status(response, str(request.get("model") or "?"))
            data = response.json()
        except Exception as exc:  # noqa: BLE001 - dumped, then handled upstream
            record.finish(error=exc)
            raise
        record.finish(response=data)
        return data

    async def _async_completion(self, request: dict[str, Any]) -> dict[str, Any]:
        client = await self._http()
        # The wire body is the request wrapped in the async envelope.
        record = self._start_record(
            transport="gigahf-async",
            path="/async/chat/completions",
            body={"request": request},
            request=request,
        )
        try:
            response = await client.post(
                "/async/chat/completions", json={"request": request}
            )
            self._raise_for_status(response, str(request.get("model") or "?"))
            submitted = response.json()
            record.note(gigahf={"submitted": _without_response(submitted), "polls": []})

            status = str(submitted.get("status") or "").lower()
            if status == "ready" and submitted.get("response"):
                record.finish(response=submitted["response"])
                return submitted["response"]
            if status in _TERMINAL_FAILURES:
                raise RuntimeError(_failure_message(submitted.get("id"), submitted))

            request_id = submitted.get("id")
            if not request_id:
                raise RuntimeError(
                    f"GigaHF accepted the request without an id: {str(submitted)[:300]}"
                )
            result = await self.await_result(
                request_id,
                estimate=submitted.get("ready_estimation_seconds"),
                record=record,
            )
        except Exception as exc:  # noqa: BLE001 - dumped, then handled upstream
            record.finish(error=exc)
            raise
        record.finish(response=result)
        return result

    async def await_result(
        self,
        request_id: str,
        *,
        estimate: Optional[float] = None,
        record: Optional[CallRecord] = None,
    ) -> dict[str, Any]:
        """Poll one async job until it is ``ready``, then return its response."""
        client = await self._http()
        deadline = time.monotonic() + self.options.poll_timeout
        delay = self._next_delay(estimate, self.options.poll_interval)
        polls: list[dict[str, Any]] = []

        while True:
            await asyncio.sleep(delay)
            response = await client.get(f"/async/chat/completions/{request_id}")
            self._raise_for_status(response, request_id)
            payload = response.json()
            status = str(payload.get("status") or "").lower()
            _log_poll(record, polls, request_id, delay, payload)

            if status == "ready":
                result = payload.get("response")
                if not result:
                    raise RuntimeError(
                        f"GigaHF request {request_id} is ready but carries no response"
                    )
                return result
            if status in _TERMINAL_FAILURES:
                raise RuntimeError(_failure_message(request_id, payload))
            if time.monotonic() >= deadline:
                raise TransientError(
                    f"GigaHF request {request_id} still {status or 'pending'} after "
                    f"{self.options.poll_timeout:.0f}s"
                )
            delay = self._next_delay(
                payload.get("ready_estimation_seconds"), delay * 1.5
            )

    def _next_delay(self, estimate: Optional[float], fallback: float) -> float:
        """Trust the server's estimate when it gives one, else back off gently."""
        try:
            hint = float(estimate) if estimate is not None else 0.0
        except (TypeError, ValueError):
            hint = 0.0
        chosen = hint if hint > 0 else fallback
        return max(0.0, min(chosen, self.options.poll_max_interval))


def _without_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Poll/submit envelope minus the generation itself (dumped separately)."""
    return {key: value for key, value in payload.items() if key != "response"}


def _log_poll(
    record: Optional[CallRecord],
    polls: list[dict[str, Any]],
    request_id: str,
    delay: float,
    payload: dict[str, Any],
) -> None:
    """Keep the poll history in the dump: how long the job took and in what states."""
    if record is None:
        return
    polls.append({"waited_seconds": round(delay, 3), **_without_response(payload)})
    record.note(gigahf={"request_id": request_id, "polls": polls})


def _failure_message(request_id: Any, payload: dict[str, Any]) -> str:
    status = str(payload.get("status") or "unknown").lower()
    reason = payload.get("error_message") or ""
    suffix = f": {reason}" if reason else ""
    return f"GigaHF request {request_id} ended as {status}{suffix}"


def _request_id_from_body(response: Any) -> Optional[str]:
    """Dig the resumable job id out of a 504 body (``query_id`` per the docs)."""
    try:
        body = response.json()
    except Exception:  # noqa: BLE001 - a gateway may answer with plain text
        return None
    if not isinstance(body, dict):
        return None
    for container in (body, body.get("detail") or {}):
        if not isinstance(container, dict):
            continue
        for key in ("query_id", "request_id", "id"):
            value = container.get(key)
            if value:
                return str(value)
    return None


def model_ids(payload: Any) -> list[str]:
    """Model names from either the OpenAI or the GigaHF ``/models`` shape."""
    if not isinstance(payload, dict):
        return []
    items = payload.get("data") or payload.get("models") or []
    if not isinstance(items, list):
        return []
    return [
        str(item.get("id") or item.get("name") or "")
        for item in items
        if isinstance(item, dict)
    ]
