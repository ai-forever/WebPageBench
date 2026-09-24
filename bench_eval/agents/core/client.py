"""Async OpenAI-compatible client for vLLM-served vision-language models.

Deliberately thin: GUI models are served through ``vllm serve`` and speak the
plain ``/chat/completions`` API. Keeping our own client (instead of browser-use's
``ChatOpenAI``) lets a family send raw text completions, custom stop tokens, and
per-endpoint sampling without fighting a structured-output wrapper.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Optional

from bench_eval.agents.core import dump
from bench_eval.retry_utils import is_retryable_http_status, retry_backoff_seconds
from bench_eval.token_usage import TokenUsage, empty_token_usage

#: ``GUI_AGENT_PLATFORM`` values with a dedicated transport (see ``create_client``).
PLATFORM_VLLM = "vllm"
PLATFORM_GIGAHF = "gigahf"


class TransientError(RuntimeError):
    """A server-side failure worth retrying, optionally with a server-set delay."""

    def __init__(self, message: str, *, retry_after: Optional[float] = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class PermanentError(RuntimeError):
    """A rejected request: the same payload will be rejected again."""


def resolve_platform(explicit: Optional[str], *, base_url: str) -> str:
    """Explicit ``GUI_AGENT_PLATFORM`` wins; otherwise recognise the host."""
    if explicit and explicit.strip():
        return explicit.strip().lower()
    if PLATFORM_GIGAHF in base_url.lower():
        return PLATFORM_GIGAHF
    return PLATFORM_VLLM


@dataclass(frozen=True)
class Endpoint:
    """Where one model is served and how to talk to it."""

    model: str
    base_url: str = "http://127.0.0.1:8000/v1"
    api_key: str = "EMPTY"
    timeout: float = 180.0
    max_retries: int = 3
    #: Which transport speaks to this endpoint — see :func:`create_client`.
    platform: str = PLATFORM_VLLM

    @classmethod
    def from_env(
        cls,
        *,
        prefix: str = "GUI_AGENT",
        model: Optional[str] = None,
        default_base_url: str = "http://127.0.0.1:8000/v1",
        timeout: float = 180.0,
        max_retries: int = 3,
    ) -> "Endpoint":
        """Read ``<PREFIX>_MODEL`` / ``<PREFIX>_BASE_URL`` / ``<PREFIX>_API_KEY``."""
        base_url = (
            os.getenv(f"{prefix}_BASE_URL")
            or os.getenv("LLM_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or default_base_url
        )
        api_key = (
            os.getenv(f"{prefix}_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or "EMPTY"
        )
        resolved_model = model or os.getenv(f"{prefix}_MODEL") or os.getenv("LLM_MODEL")
        if not resolved_model:
            raise ValueError(
                f"Model name is required: set {prefix}_MODEL or pass model=..."
            )
        resolved_base_url = base_url.rstrip("/")
        return cls(
            model=resolved_model,
            base_url=resolved_base_url,
            api_key=api_key,
            timeout=float(os.getenv(f"{prefix}_TIMEOUT", str(timeout))),
            max_retries=int(os.getenv(f"{prefix}_MAX_RETRIES", str(max_retries))),
            platform=resolve_platform(
                os.getenv(f"{prefix}_PLATFORM"), base_url=resolved_base_url
            ),
        )


@dataclass
class ChatResponse:
    text: str
    usage: TokenUsage
    finish_reason: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class SamplingParams:
    temperature: float = 0.0
    top_p: float = 0.9
    max_tokens: int = 2048
    stop: tuple[str, ...] = ()
    extra_body: dict[str, Any] = field(default_factory=dict)

    def as_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }
        if self.stop:
            payload["stop"] = list(self.stop)
        payload.update(self.extra_body)
        return payload


class TokenLedger:
    """Accumulate usage across steps and across sub-models (planner + grounder)."""

    def __init__(self) -> None:
        self.total: TokenUsage = empty_token_usage()
        self.by_model: dict[str, TokenUsage] = {}

    def add(self, model: str, usage: TokenUsage) -> None:
        for key in ("prompt_tokens", "completion_tokens", "total_tokens", "llm_calls"):
            self.total[key] += int(usage.get(key, 0) or 0)
        bucket = self.by_model.setdefault(model, empty_token_usage())
        for key in ("prompt_tokens", "completion_tokens", "total_tokens", "llm_calls"):
            bucket[key] += int(usage.get(key, 0) or 0)

    def snapshot(self) -> tuple[TokenUsage, dict[str, TokenUsage]]:
        return dict(self.total), {k: dict(v) for k, v in self.by_model.items()}


class VLMClient:
    """Chat-completions client with retries against a vLLM (or any OpenAI) server."""

    #: ``verify`` for httpx. Transports whose host uses an internal CA relax it.
    ssl_verify: Any = True

    def __init__(
        self,
        endpoint: Endpoint,
        *,
        ledger: Optional[TokenLedger] = None,
        dumper: Optional[dump.CallDumper] = None,
    ):
        self.endpoint = endpoint
        self.ledger = ledger or TokenLedger()
        self._client: Any = None
        #: Verbatim call dumps; ``None`` disables them. The eval path builds this
        #: from ``EvalConfig.agent_dump_enabled`` (see settings.build_agent);
        #: standalone callers fall back to the environment.
        self.dumper = dumper if dumper is not None else dump.CallDumper.from_env()

    async def _http(self) -> Any:
        if self._client is None:
            from bench_eval.llm_factory import build_llm_http_client

            self._client = build_llm_http_client(
                base_url=self.endpoint.base_url,
                timeout=self.endpoint.timeout,
                headers={"Authorization": f"Bearer {self.endpoint.api_key}"},
                verify=self.ssl_verify,
            )
        return self._client

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        sampling: Optional[SamplingParams] = None,
        model: Optional[str] = None,
    ) -> ChatResponse:
        params = sampling or SamplingParams()
        target_model = model or self.endpoint.model
        payload = {
            "model": target_model,
            "messages": messages,
            **params.as_payload(),
        }

        last_error: Optional[Exception] = None
        for attempt in range(self.endpoint.max_retries + 1):
            try:
                data = await self._post_completion(payload)
                break
            except Exception as exc:  # noqa: BLE001 - retried below, re-raised at the end
                last_error = exc
                if _is_fatal(exc) or attempt >= self.endpoint.max_retries:
                    raise
                await asyncio.sleep(_retry_delay(exc, attempt))
        else:  # pragma: no cover - loop always breaks or raises
            raise last_error or RuntimeError("LLM request failed")

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        text = message.get("content") or ""
        if isinstance(text, list):
            # Some servers return content parts instead of a plain string.
            text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
        if not text.strip():
            # Reasoning models can spend the whole budget before emitting content;
            # the thought is better than nothing for the parser and the trajectory.
            text = message.get("reasoning_content") or ""
        usage = _usage_from_payload(data.get("usage") or {})
        self.ledger.add(target_model, usage)
        return ChatResponse(
            text=text,
            usage=usage,
            finish_reason=choice.get("finish_reason"),
            raw=data,
        )

    def _start_record(
        self,
        *,
        transport: str,
        path: str,
        body: dict[str, Any],
        request: dict[str, Any],
    ) -> dump.CallRecord:
        """Open a dump record for one attempt (a no-op when dumping is off)."""
        if self.dumper is None:
            return dump.CallRecord(None, {})
        return self.dumper.start(
            transport=transport,
            url=f"{self.endpoint.base_url}{path}",
            body=body,
            request=request,
            endpoint={
                "base_url": self.endpoint.base_url,
                "model": self.endpoint.model,
                "platform": self.endpoint.platform,
            },
        )

    async def _post_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """One request attempt. Platform transports override this, not ``chat``."""
        client = await self._http()
        record = self._start_record(
            transport="openai", path="/chat/completions", body=payload, request=payload
        )
        try:
            response = await client.post("/chat/completions", json=payload)
            self._raise_for_status(response, str(payload.get("model") or "?"))
            data = response.json()
        except Exception as exc:  # noqa: BLE001 - dumped, then handled upstream
            record.finish(error=exc)
            raise
        record.finish(response=data)
        return data

    def _raise_for_status(self, response: Any, label: str) -> None:
        """Turn an error response into a retryable or a fatal exception."""
        if response.status_code < 400:
            return
        body = response.text[:500]
        message = f"{label} returned HTTP {response.status_code}: {body}"
        if is_retryable_http_status(response.status_code):
            raise TransientError(message, retry_after=_retry_after_seconds(response))
        raise PermanentError(message)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "VLMClient":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()


def _usage_from_payload(usage: dict[str, Any]) -> TokenUsage:
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": int(usage.get("total_tokens") or (prompt + completion)),
        "llm_calls": 1,
    }


def _retry_after_seconds(response: Any) -> Optional[float]:
    """Honour a server-set ``Retry-After`` (seconds form) when throttled."""
    raw = (getattr(response, "headers", None) or {}).get("Retry-After")
    if not raw:
        return None
    try:
        return max(0.0, float(str(raw).strip()))
    except ValueError:
        # HTTP-date form: not worth parsing, fall back to the usual backoff.
        return None


def _retry_delay(exc: Exception, attempt: int) -> float:
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        return float(retry_after)
    return retry_backoff_seconds(attempt)


def create_client(
    endpoint: Endpoint,
    *,
    ledger: Optional[TokenLedger] = None,
    dumper: Optional[dump.CallDumper] = None,
) -> "VLMClient":
    """Return the client that speaks this endpoint's platform dialect."""
    if endpoint.platform == PLATFORM_GIGAHF:
        from bench_eval.agents.core.gigahf import GigaHFClient

        return GigaHFClient(endpoint, ledger=ledger, dumper=dumper)
    return VLMClient(endpoint, ledger=ledger, dumper=dumper)


def _is_fatal(exc: Exception) -> bool:
    """Context-length and bad-request errors will not succeed on retry."""
    if isinstance(exc, PermanentError):
        # Already classified from the status code (422 validation, 401, 404...).
        return True
    if isinstance(exc, TransientError):
        return False
    message = str(exc)
    return any(
        marker in message
        for marker in ("context_length_exceeded", "HTTP 400", "HTTP 413", "Too Large")
    )


def text_part(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def image_part(base64_png: str) -> dict[str, Any]:
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{base64_png}"},
    }
