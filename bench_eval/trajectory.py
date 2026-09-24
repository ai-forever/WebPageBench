"""Serialize browser-use agent history and WebPageBench telemetry into eval trajectories."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from lib.src.agent_bench import client


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "model_dump"):
        try:
            return _to_jsonable(value.model_dump(mode="json"))
        except TypeError:
            return _to_jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return _to_jsonable(value.dict())
    return str(value)


def _serialize_history_item(item: Any, step_index: int) -> Dict[str, Any]:
    row: Dict[str, Any] = {"step": step_index}
    model_output = getattr(item, "model_output", None)
    if model_output is not None:
        row["model_output"] = _to_jsonable(model_output)

    result = getattr(item, "result", None)
    if result is not None:
        row["result"] = _to_jsonable(result)

    state = getattr(item, "state", None)
    if state is not None:
        row["state"] = _to_jsonable(state)

    metadata = getattr(item, "metadata", None)
    if metadata is not None:
        row["metadata"] = _to_jsonable(metadata)

    state_message = getattr(item, "state_message", None)
    if state_message:
        row["state_message"] = state_message

    return row


def serialize_agent_history(history: Any) -> Dict[str, Any]:
    """Extract LLM steps, actions, and browser state from browser-use history."""
    if history is None:
        return {"steps": [], "summary": {}}

    summary: Dict[str, Any] = {
        "step_count": 0,
        "is_done": False,
        "is_successful": None,
        "final_result": None,
        "urls": [],
        "errors": [],
        "action_names": [],
        "total_duration_seconds": None,
    }

    for method_name in (
        "number_of_steps",
        "is_done",
        "is_successful",
        "final_result",
        "urls",
        "errors",
        "action_names",
        "total_duration_seconds",
    ):
        method = getattr(history, method_name, None)
        if callable(method):
            try:
                summary[method_name] = _to_jsonable(method())
            except Exception:
                pass

    steps: List[Dict[str, Any]] = []
    raw_history = getattr(history, "history", None) or []
    for index, item in enumerate(raw_history, start=1):
        steps.append(_serialize_history_item(item, index))

    action_history = getattr(history, "action_history", None)
    if callable(action_history):
        try:
            summary["action_history"] = _to_jsonable(action_history())
        except Exception:
            pass

    model_actions = getattr(history, "model_actions", None)
    if callable(model_actions):
        try:
            summary["model_actions"] = _to_jsonable(model_actions())
        except Exception:
            pass

    model_thoughts = getattr(history, "model_thoughts", None)
    if callable(model_thoughts):
        try:
            summary["model_thoughts"] = _to_jsonable(model_thoughts())
        except Exception:
            pass

    if not summary.get("step_count") and steps:
        summary["step_count"] = len(steps)

    return {"steps": steps, "summary": summary}


def fetch_dab_events(
    track_id: str,
    api_address: str,
    *,
    https: bool = False,
) -> List[Dict[str, Any]]:
    events = client.get_track(track_id, api_address, https=https) or []
    return _to_jsonable(events)


def build_trajectory(
    *,
    agent_history: Any = None,
    harness_trajectory: dict[str, Any] | None = None,
    dab_events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    if harness_trajectory:
        agent_part: Dict[str, Any] = {
            "steps": harness_trajectory.get("steps", []),
            "summary": harness_trajectory.get("summary", {}),
        }
        if harness_trajectory.get("harness"):
            agent_part["harness"] = harness_trajectory["harness"]
        if harness_trajectory.get("metadata"):
            agent_part["metadata"] = harness_trajectory["metadata"]
    else:
        agent_part = serialize_agent_history(agent_history)
    dab_part = dab_events or []
    return {
        "agent": agent_part,
        "dab_events": dab_part,
        "dab_event_names": [
            event.get("event_name")
            for event in dab_part
            if isinstance(event, dict) and event.get("event_name")
        ],
    }
