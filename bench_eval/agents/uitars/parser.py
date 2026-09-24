"""Parse the UI-TARS DSL (`Thought: ... Action: click(start_box='(x,y)')`)."""

from __future__ import annotations

import re
from typing import Optional

from bench_eval.agents.core.actions import Action, ActionType
from bench_eval.agents.core.coordinates import CoordinateScaler
from bench_eval.agents.core.executor import SCROLL_PIXELS_PER_CLICK
from bench_eval.agents.core.parsers import parse_box

_THOUGHT_RE = re.compile(
    r"(?:Thought|Reflection|Action_Summary)\s*:\s*(.*?)(?=\s*Action\s*:|$)",
    re.DOTALL,
)
_CALL_RE = re.compile(r"^\s*(?P<name>[a-zA-Z_]\w*)\s*\((?P<args>.*)\)\s*$", re.DOTALL)
_BOX_ARG_RE = re.compile(r"(start_box|end_box)\s*=\s*'([^']*)'", re.DOTALL)
_KEY_ARG_RE = re.compile(r"key\s*=\s*'([^']*)'", re.DOTALL)
_DIRECTION_RE = re.compile(r"direction\s*=\s*'([^']*)'", re.DOTALL)
_CONTENT_RE = re.compile(r"content\s*=\s*'(.*)'\s*$", re.DOTALL)

_SIMPLE_ACTIONS = {
    "click": ActionType.CLICK,
    "left_single": ActionType.CLICK,
    "left_click": ActionType.CLICK,
    "left_double": ActionType.DOUBLE_CLICK,
    "double_click": ActionType.DOUBLE_CLICK,
    "right_single": ActionType.RIGHT_CLICK,
    "right_click": ActionType.RIGHT_CLICK,
    "middle_click": ActionType.MIDDLE_CLICK,
    "hover": ActionType.MOVE,
    "mouse_move": ActionType.MOVE,
}

#: `scroll(direction=...)` is unitless; five wheel clicks matches UI-TARS training.
_SCROLL_CLICKS = 5


def extract_thought(response: str) -> Optional[str]:
    match = _THOUGHT_RE.search(response or "")
    if not match:
        return None
    thought = match.group(1).strip()
    return thought or None


def split_actions(response: str) -> list[str]:
    """Everything after `Action:`, split on blank lines into separate calls."""
    if "Action:" not in (response or ""):
        return []
    tail = response.split("Action:")[-1].strip()
    chunks = [chunk.strip() for chunk in tail.split("\n\n")]
    return [chunk for chunk in chunks if chunk]


def parse_action_call(call: str, scaler: CoordinateScaler) -> Optional[Action]:
    match = _CALL_RE.match(call.strip())
    if not match:
        return None
    name = match.group("name").lower()
    args = match.group("args")
    boxes = {key: value for key, value in _BOX_ARG_RE.findall(args)}

    if name in _SIMPLE_ACTIONS:
        action = Action(type=_SIMPLE_ACTIONS[name], raw=call)
        point = parse_box(boxes.get("start_box", ""), scaler)
        if point:
            action.x, action.y = point
        return action

    if name == "drag":
        action = Action(type=ActionType.DRAG, raw=call)
        start = parse_box(boxes.get("start_box", ""), scaler)
        end = parse_box(boxes.get("end_box", ""), scaler)
        if start:
            action.x, action.y = start
        if end:
            action.to_x, action.to_y = end
        return action

    if name == "hotkey":
        key_match = _KEY_ARG_RE.search(args)
        raw_keys = key_match.group(1) if key_match else ""
        keys = tuple(part for part in re.split(r"[+\s,]+", raw_keys) if part)
        return Action.hotkey(*keys, raw=call) if keys else None

    if name == "type":
        content_match = _CONTENT_RE.search(args)
        text = content_match.group(1) if content_match else ""
        # UI-TARS escapes quotes/newlines inside content.
        text = text.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
        return Action.type_text(text, raw=call)

    if name == "scroll":
        action = Action(type=ActionType.SCROLL, raw=call)
        point = parse_box(boxes.get("start_box", ""), scaler)
        if point:
            action.x, action.y = point
        direction_match = _DIRECTION_RE.search(args)
        direction = (direction_match.group(1) if direction_match else "down").lower()
        delta = _SCROLL_CLICKS * SCROLL_PIXELS_PER_CLICK
        if "up" in direction:
            action.scroll_dy = -delta
        elif "down" in direction:
            action.scroll_dy = delta
        elif "left" in direction:
            action.scroll_dx = -delta
        elif "right" in direction:
            action.scroll_dx = delta
        else:
            action.scroll_dy = delta
        return action

    if name == "wait":
        return Action.wait(5.0, raw=call)

    if name in {"finished", "finish", "done"}:
        content_match = _CONTENT_RE.search(args)
        action = Action.terminate("success", raw=call)
        if content_match:
            action.text = content_match.group(1).replace("\\n", "\n")
        return action

    if name == "call_user":
        return Action(type=ActionType.CALL_USER, raw=call)

    if name in {"fail", "failed"}:
        return Action.terminate("failure", raw=call)

    return None


def parse_response(
    response: str,
    scaler: CoordinateScaler,
) -> tuple[list[Action], Optional[str], Optional[str]]:
    """Return (actions, thought, action description)."""
    thought = extract_thought(response)
    calls = split_actions(response)
    actions = [
        action for action in (parse_action_call(call, scaler) for call in calls) if action
    ]
    description = calls[0] if calls else None
    return actions, thought, description
