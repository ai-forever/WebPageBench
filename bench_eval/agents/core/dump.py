"""Verbatim dumps of every model call (opt-in, ``AGENT_DUMP_ENABLED``).

The trajectory in ``results.json`` keeps only the parsed answer — the actions and
the raw text. When a run goes wrong the question is usually one level lower:
*what exactly did we put on the wire, and what exactly came back?* This module
writes that, one JSON file per call, with the request body byte-for-byte as the
transport sends it (base64 screenshots included) next to the untouched response.

Off unless the run config turns it on — ``EvalConfig.agent_dump_enabled``,
from ``AGENT_DUMP_ENABLED``::

    AGENT_DUMP_ENABLED=true ./scripts/run_eval.sh qwen3-vl/gigahf-qwen3.8-27b

``AGENT_DUMP_DIR`` picks the directory (default ``<EVAL_OUTPUT_DIR>/llm-calls``).
Files land at ``<dir>/<task>/step-NN_call-NNN_<pid>.json``; ``<dir>/index.jsonl``
gets one image-free summary line per call, so a run can be skimmed without
opening megabytes of base64. Set ``AGENT_DUMP_IMAGES=trim`` to replace the
data URIs in the dumps themselves with a ``<N bytes>`` placeholder.
"""

from __future__ import annotations

import contextvars
import itertools
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ENV_DIR = "AGENT_DUMP_DIR"
ENV_IMAGES = "AGENT_DUMP_IMAGES"
#: Names this shipped with, still honoured so existing run envs keep working.
ENV_DIR_ALIASES = (ENV_DIR, "GUI_AGENT_DUMP_DIR")
ENV_IMAGES_ALIASES = (ENV_IMAGES, "GUI_AGENT_DUMP_IMAGES")

#: ``data:image/png;base64,AAAA...`` inside a request we are about to trim.
_DATA_URI = re.compile(r"^data:image/[a-z]+;base64,(.*)$", re.DOTALL)

#: Answers are clipped to this in ``index.jsonl`` (never in the call file), so
#: concurrent appends stay under the atomic-write size.
INDEX_CONTENT_CHARS = 400

_counter = itertools.count(1)
_index_lock = threading.Lock()

#: Per-task breadcrumbs (task key, step, url) merged into every dump.
_context: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "llm_dump_context", default={}
)


def _first_env(names: tuple[str, ...]) -> Optional[str]:
    for name in names:
        value = (os.getenv(name) or "").strip()
        if value:
            return value
    return None


def set_context(**fields: Any) -> None:
    """Merge breadcrumbs into the current context (loop sets step, harness task)."""
    _context.set({**_context.get(), **fields})


def context() -> dict[str, Any]:
    return dict(_context.get())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _slug(value: Any, fallback: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "")).strip("_")
    return text[:80] or fallback


def _trim_images(node: Any) -> Any:
    """Replace base64 image payloads with their size, keeping the shape intact."""
    if isinstance(node, dict):
        return {key: _trim_images(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_trim_images(item) for item in node]
    if isinstance(node, str):
        match = _DATA_URI.match(node)
        if match:
            return f"<base64 image, {len(match.group(1))} chars>"
    return node


class CallRecord:
    """One in-flight call. ``finish`` writes the file; a dumper-less record is a no-op."""

    def __init__(self, dumper: Optional["CallDumper"], payload: dict[str, Any]) -> None:
        self._dumper = dumper
        self._payload = payload
        self.path: Optional[str] = None

    def note(self, **fields: Any) -> None:
        """Attach transport detail known only mid-flight (async id, poll log)."""
        if self._dumper is not None:
            self._payload.update(fields)

    def finish(
        self,
        *,
        response: Optional[dict[str, Any]] = None,
        error: Optional[BaseException] = None,
    ) -> None:
        if self._dumper is None:
            return
        self._payload["finished_at"] = _now()
        self._payload["response"] = response
        self._payload["error"] = (
            f"{type(error).__name__}: {error}" if error is not None else None
        )
        self.path = self._dumper.write(self._payload)
        self._dumper = None  # write once, even if a caller finishes twice


class CallDumper:
    """Writes one JSON file per model call under ``directory``."""

    def __init__(self, directory: Path, *, trim_images: bool = False) -> None:
        self.directory = directory
        self.trim_images = trim_images
        self.directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> Optional["CallDumper"]:
        """For entry points without an ``EvalConfig`` (``cli/benchmark``, ``cli/infer``).

        The eval path does not come through here: it builds the dumper from
        ``EvalConfig.agent_dump_enabled`` in ``settings.build_agent``.
        """
        raw = _first_env(ENV_DIR_ALIASES)
        if not raw:
            return None
        mode = (_first_env(ENV_IMAGES_ALIASES) or "full").lower()
        return cls(Path(raw).expanduser(), trim_images=mode == "trim")

    def start(
        self,
        *,
        transport: str,
        url: str,
        body: dict[str, Any],
        request: dict[str, Any],
        endpoint: Optional[dict[str, Any]] = None,
        method: str = "POST",
    ) -> CallRecord:
        """Open a record for a call that is about to go out."""
        return CallRecord(
            self,
            {
                "seq": next(_counter),
                "pid": os.getpid(),
                "started_at": _now(),
                "context": context(),
                "transport": transport,
                "endpoint": endpoint or {},
                # What actually goes on the wire, envelope and all.
                "http": {"method": method, "url": url, "body": body},
                # The chat-completions request inside that envelope.
                "request": request,
            },
        )

    def write(self, payload: dict[str, Any]) -> str:
        ctx = payload.get("context") or {}
        task = _slug(ctx.get("task_key"), "task")
        step = ctx.get("step")
        name = (
            f"step-{int(step):02d}" if isinstance(step, int) else "step-xx"
        ) + f"_call-{payload['seq']:03d}_{payload['pid']}.json"

        target = self.directory / task
        target.mkdir(parents=True, exist_ok=True)
        path = target / name

        payload["summary"] = _summarize(payload)
        body = payload if not self.trim_images else _trim_images(payload)
        path.write_text(
            json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._append_index(payload, path)
        return str(path)

    def _append_index(self, payload: dict[str, Any], path: Path) -> None:
        summary = dict(payload["summary"])
        # DeepEval runs its workers as separate processes, all appending here.
        # A single short O_APPEND write lands atomically; a long one could
        # interleave, so the full answer stays in the per-call file only.
        summary["content"] = _clip(summary.get("content"), INDEX_CONTENT_CHARS)
        line = {
            "seq": payload["seq"],
            "file": str(path.relative_to(self.directory)),
            "started_at": payload["started_at"],
            "finished_at": payload.get("finished_at"),
            "context": payload.get("context"),
            "transport": payload.get("transport"),
            **summary,
            "error": _clip(payload.get("error"), INDEX_CONTENT_CHARS),
        }
        blob = (json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8")
        with _index_lock:
            handle = os.open(
                self.directory / "index.jsonl",
                os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                0o644,
            )
            try:
                os.write(handle, blob)
            finally:
                os.close(handle)


def _summarize(payload: dict[str, Any]) -> dict[str, Any]:
    """Image-free digest: what was asked, what came back, how much it cost."""
    request = payload.get("request") or {}
    response = payload.get("response") or {}
    choice = ((response.get("choices") or [{}]) or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    return {
        "model": request.get("model"),
        "messages": len(request.get("messages") or []),
        "images": _count_images(request.get("messages") or []),
        "max_tokens": request.get("max_tokens"),
        "finish_reason": choice.get("finish_reason"),
        "usage": response.get("usage"),
        "content": content or message.get("reasoning_content") or "",
    }


def _clip(text: Optional[str], limit: int) -> Optional[str]:
    if not text or len(text) <= limit:
        return text
    return text[:limit] + "…"


def _count_images(messages: list[Any]) -> int:
    total = 0
    for message in messages:
        content = (message or {}).get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        total += sum(
            1
            for part in content
            if isinstance(part, dict) and part.get("type") == "image_url"
        )
    return total
