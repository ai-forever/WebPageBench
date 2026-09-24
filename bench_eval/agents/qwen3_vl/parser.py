"""Parse Qwen3-VL `computer_use` tool calls into canonical actions."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from bench_eval.agents.core.actions import Action, ActionType
from bench_eval.agents.core.coordinates import CoordinateScaler
from bench_eval.agents.core.executor import SCROLL_PIXELS_PER_CLICK

_TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
_ACTION_LINE_RE = re.compile(r"^\s*Action\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)

_POINTER_ACTIONS = {
    "left_click": ActionType.CLICK,
    "double_click": ActionType.DOUBLE_CLICK,
    "triple_click": ActionType.TRIPLE_CLICK,
    "right_click": ActionType.RIGHT_CLICK,
    "middle_click": ActionType.MIDDLE_CLICK,
    "mouse_move": ActionType.MOVE,
    "left_click_drag": ActionType.DRAG,
}


def extract_action_description(response: str) -> Optional[str]:
    match = _ACTION_LINE_RE.search(response or "")
    return match.group(1).strip() if match else None


def extract_tool_calls(response: str) -> list[dict[str, Any]]:
    """Collect tool calls from `<tool_call>` blocks or bare JSON lines."""
    payloads: list[dict[str, Any]] = []
    for block in _TOOL_CALL_RE.findall(response or ""):
        payload = _loads(block)
        if payload:
            payloads.append(payload)
    if payloads:
        return payloads

    for line in (response or "").splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            payload = _loads(line)
            if payload and "arguments" in payload:
                payloads.append(payload)
    return payloads


def _loads(raw: str) -> Optional[dict[str, Any]]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = _loads_unterminated(raw)
    return payload if isinstance(payload, dict) else None


def _loads_unterminated(raw: str) -> Optional[Any]:
    """Retry a tool call whose closing brackets the model forgot to emit."""
    closers: list[str] = []
    in_string = escaped = False
    for char in raw:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[":
            closers.append("}" if char == "{" else "]")
        elif char in "}]":
            if not closers or closers.pop() != char:
                return None
    if not closers:
        return None
    tail = ('"' if in_string else "") + "".join(reversed(closers))
    try:
        return json.loads(raw + tail)
    except json.JSONDecodeError:
        return None


def _clean_keys(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        raw = [raw]
    keys: list[str] = []
    for key in raw:
        if not isinstance(key, str):
            continue
        # Models occasionally echo the parameter name: keys=['ctrl','c'].
        cleaned = key.strip().removeprefix("keys=[").strip("[]'\" ").strip()
        if cleaned:
            keys.extend(part for part in re.split(r"[+\s,]+", cleaned) if part)
    return tuple(keys)


#: Qwen ships the same action schema under two names (desktop / mobile); some
#: checkpoints emit `mobile_use` even when prompted with the `computer_use` tool.
_TOOL_NAMES = {"computer_use", "mobile_use", None}


def tool_call_to_action(payload: dict[str, Any], scaler: CoordinateScaler) -> Optional[Action]:
    if payload.get("name") not in _TOOL_NAMES:
        return None
    args = payload.get("arguments") or {}
    if isinstance(args, str):
        args = _loads(args) or {}
    if not isinstance(args, dict):
        return None
    nested = args.get("arguments")
    if isinstance(nested, dict):
        # Some checkpoints wrap the parameters in a second `arguments` object.
        args = {**args, **nested}
    action_name = str(args.get("action") or "").strip()
    raw = json.dumps(payload, ensure_ascii=False)

    if action_name in _POINTER_ACTIONS:
        action = Action(type=_POINTER_ACTIONS[action_name], raw=raw)
        coordinate = args.get("coordinate")
        if isinstance(coordinate, (list, tuple)) and len(coordinate) >= 2:
            x, y = scaler.to_screen(float(coordinate[0]), float(coordinate[1]))
            if action.type is ActionType.DRAG:
                action.to_x, action.to_y = x, y
            else:
                action.x, action.y = x, y
        return action

    if action_name == "type":
        return Action.type_text(str(args.get("text") or ""), raw=raw)

    if action_name in {"key", "key_down"}:
        keys = _clean_keys(args.get("keys") or args.get("text"))
        return Action.hotkey(*keys, raw=raw) if keys else None

    if action_name == "key_up":
        # `key_down` above already performs a full press+release, so the paired
        # `key_up` must not fire a second press (EvoCUA-S2 emits both).
        return Action(type=ActionType.NOOP, raw=raw)

    if action_name in {"scroll", "hscroll"}:
        pixels = float(args.get("pixels") or 0)
        magnitude = abs(pixels)
        # Small magnitudes are wheel clicks, large ones are already pixels.
        delta = magnitude if magnitude > 50 else magnitude * SCROLL_PIXELS_PER_CLICK
        signed = -delta if pixels >= 0 else delta
        action = Action(type=ActionType.SCROLL, raw=raw)
        if action_name == "hscroll":
            action.scroll_dx = -signed
        else:
            action.scroll_dy = signed
        coordinate = args.get("coordinate")
        if isinstance(coordinate, (list, tuple)) and len(coordinate) >= 2:
            action.x, action.y = scaler.to_screen(float(coordinate[0]), float(coordinate[1]))
        return action

    if action_name == "wait":
        return Action.wait(float(args.get("time") or 3.0), raw=raw)

    if action_name == "terminate":
        return Action.terminate(str(args.get("status") or "success"), raw=raw)

    if action_name == "answer":
        return Action(type=ActionType.ANSWER, text=str(args.get("text") or ""), raw=raw)

    return None


def parse_response(response: str, scaler: CoordinateScaler) -> tuple[list[Action], Optional[str]]:
    """Return (actions, one-line action description)."""
    actions = [
        action
        for action in (
            tool_call_to_action(payload, scaler) for payload in extract_tool_calls(response)
        )
        if action is not None
    ]
    description = extract_action_description(response)
    if not description and actions:
        description = actions[0].describe()
    return actions, description
