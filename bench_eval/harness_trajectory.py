"""Serialize trajectories from non-browser-use harness adapters."""

from __future__ import annotations

from typing import Any, Sequence

from bench_eval.trajectory import _to_jsonable


def _join_openhands_content_parts(parts: list[str]) -> str:
    return "".join(parts).strip()


def openhands_content_to_text(content: Sequence[Any] | Any) -> str:
    """Join OpenHands LLM message content parts into a single string."""
    from openhands.sdk.llm import content_to_str

    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    return _join_openhands_content_parts(content_to_str(content))


def serialize_message_trajectory(
    messages: list[Any],
    *,
    harness: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize LangChain/OpenHands message lists for eval artifacts."""
    steps: list[dict[str, Any]] = []
    for index, message in enumerate(messages):
        role = getattr(message, "type", None) or getattr(message, "role", None) or "unknown"
        content = getattr(message, "content", None)
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(str(part.get("text") or ""))
                elif hasattr(part, "text"):
                    text_parts.append(str(part.text))
                else:
                    text_parts.append(str(part))
            content = "\n".join(part for part in text_parts if part)
        step: dict[str, Any] = {
            "index": index,
            "role": role,
            "content": content if isinstance(content, str) else str(content),
        }
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            step["tool_calls"] = [
                {
                    "id": call.get("id") if isinstance(call, dict) else getattr(call, "id", None),
                    "name": call.get("name") if isinstance(call, dict) else getattr(call, "name", None),
                    "args": call.get("args") if isinstance(call, dict) else getattr(call, "args", None),
                }
                for call in tool_calls
            ]
        name = getattr(message, "name", None)
        if name:
            step["name"] = name
        usage_metadata = getattr(message, "usage_metadata", None)
        if usage_metadata:
            if isinstance(usage_metadata, dict):
                step["usage_metadata"] = usage_metadata
            elif hasattr(usage_metadata, "model_dump"):
                try:
                    step["usage_metadata"] = usage_metadata.model_dump(mode="json")
                except TypeError:
                    step["usage_metadata"] = usage_metadata.model_dump()
        steps.append(step)

    payload: dict[str, Any] = {
        "harness": harness,
        "summary": {"step_count": len(steps)},
        "steps": steps,
    }
    if extra:
        payload["metadata"] = extra
    return payload


def serialize_openhands_events(events: Any, *, harness: str) -> dict[str, Any]:
    """Serialize OpenHands event log into a compact trajectory."""
    from openhands.sdk.event.llm_convertible.action import ActionEvent
    from openhands.sdk.event.llm_convertible.message import MessageEvent

    steps: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        if isinstance(event, MessageEvent):
            text = openhands_content_to_text(event.llm_message.content)
            steps.append(
                {
                    "index": index,
                    "kind": "message",
                    "source": event.source,
                    "content": text,
                }
            )
        elif isinstance(event, ActionEvent):
            steps.append(
                {
                    "index": index,
                    "kind": "action",
                    "tool": getattr(event, "tool_name", None),
                    "action": _to_jsonable(getattr(event, "action", None)),
                }
            )

    return {
        "harness": harness,
        "summary": {"step_count": len(steps)},
        "steps": steps,
    }
