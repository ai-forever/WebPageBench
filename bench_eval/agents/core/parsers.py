"""Shared response parsing: pyautogui code blocks and coordinate boxes.

OpenCUA, EvoCUA-S1 and the Jedi planner all answer with pyautogui code, so they
share this module; only their prompt/response envelope differs. Parsing goes
through :mod:`ast` rather than regexes because models routinely emit keyword
arguments, nested lists, and escaped strings that regexes mangle.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from bench_eval.agents.core.actions import Action, ActionType
from bench_eval.agents.core.coordinates import CoordinateScaler
from bench_eval.agents.core.executor import SCROLL_PIXELS_PER_CLICK

_CODE_BLOCK_RE = re.compile(r"```(?:\w+)?\s*(.*?)```", re.DOTALL)
_SENTINELS = {"DONE", "FAIL", "WAIT"}

#: Models emit either wheel clicks (small ints) or pixels (large ints). Above this
#: threshold the number is treated as pixels, which keeps both dialects usable.
_SCROLL_PIXEL_THRESHOLD = 50


_BARE_CODE_RE = re.compile(r"\b(?:pyautogui|computer)\.\w+\s*\(|^\s*(?:DONE|FAIL|WAIT)\s*$", re.MULTILINE)


def extract_code_blocks(text: str) -> list[str]:
    """Return fenced code blocks.

    Models occasionally drop the fences, so unfenced text is accepted too — but
    only when it actually contains a call or a sentinel. Without that guard,
    prose from the Action section would be parsed as code.
    """
    blocks = [block.strip() for block in _CODE_BLOCK_RE.findall(text or "")]
    blocks = [block for block in blocks if block]
    if blocks:
        return blocks
    stripped = (text or "").strip()
    if stripped and _BARE_CODE_RE.search(stripped):
        return [stripped]
    return []


@dataclass
class RawCall:
    """One parsed call plus the comment line that preceded it."""

    func: str
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)
    comment: Optional[str] = None
    source: str = ""

    def arg(self, index: int, name: str, default: Any = None) -> Any:
        if name in self.kwargs:
            return self.kwargs[name]
        if index < len(self.args):
            return self.args[index]
        return default


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        try:
            return ast.unparse(node)
        except Exception:  # noqa: BLE001 - fall back to an opaque marker
            return None


def _func_name(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def parse_calls(code: str) -> tuple[list[RawCall], list[str]]:
    """Parse a code block into calls and any DONE/FAIL/WAIT sentinels."""
    sentinels = [line.strip() for line in code.splitlines() if line.strip() in _SENTINELS]
    comments = _comments_by_line(code)

    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Models sometimes concatenate statements with ';' or trail an unclosed
        # quote; retry line by line so one bad line does not lose the rest.
        return _parse_calls_line_by_line(code, comments), sentinels

    nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    nodes.sort(key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0)))
    return [_raw_call(node, code, comments) for node in nodes], sentinels


def _parse_calls_line_by_line(code: str, comments: dict[int, str]) -> list[RawCall]:
    calls: list[RawCall] = []
    for lineno, line in enumerate(code.splitlines(), start=1):
        for chunk in line.split(";"):
            chunk = chunk.strip()
            if not chunk or chunk.startswith("#"):
                continue
            try:
                tree = ast.parse(chunk)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    call = _raw_call(node, chunk, {})
                    call.comment = comments.get(lineno - 1) or comments.get(lineno)
                    calls.append(call)
    return calls


def _raw_call(node: ast.Call, code: str, comments: dict[int, str]) -> RawCall:
    try:
        source = ast.unparse(node)
    except Exception:  # noqa: BLE001
        source = ""
    lineno = getattr(node, "lineno", 0)
    return RawCall(
        func=_func_name(node.func),
        args=[_literal(arg) for arg in node.args],
        kwargs={kw.arg: _literal(kw.value) for kw in node.keywords if kw.arg},
        comment=comments.get(lineno - 1) or comments.get(lineno),
        source=source,
    )


def _comments_by_line(code: str) -> dict[int, str]:
    comments: dict[int, str] = {}
    for lineno, line in enumerate(code.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            comments[lineno] = stripped.lstrip("#").strip()
        elif "#" in stripped and not stripped.startswith(("'", '"')):
            comments[lineno] = stripped.split("#", 1)[1].strip()
    return comments


def _coerce_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _point(call: RawCall, scaler: CoordinateScaler) -> Optional[tuple[int, int]]:
    x = _coerce_number(call.arg(0, "x"))
    y = _coerce_number(call.arg(1, "y"))
    if x is None or y is None:
        return None
    return scaler.to_screen(x, y)


def _keys_from(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part for part in re.split(r"[+\s,]+", value) if part)
    if isinstance(value, (list, tuple)):
        keys: list[str] = []
        for item in value:
            keys.extend(_keys_from(item))
        return tuple(keys)
    return ()


def _scroll_action(call: RawCall, scaler: CoordinateScaler, *, horizontal: bool) -> Action:
    amount = _coerce_number(call.arg(0, "clicks")) or _coerce_number(call.kwargs.get("amount")) or 0.0
    magnitude = abs(amount)
    pixels = magnitude if magnitude > _SCROLL_PIXEL_THRESHOLD else magnitude * SCROLL_PIXELS_PER_CLICK
    # pyautogui: positive scrolls up / left; wheel deltas are the opposite sign.
    delta = -pixels if amount >= 0 else pixels

    action = Action(type=ActionType.SCROLL, raw=call.source)
    if horizontal:
        action.scroll_dx = -delta
    else:
        action.scroll_dy = delta

    x = _coerce_number(call.kwargs.get("x"))
    y = _coerce_number(call.kwargs.get("y"))
    if x is not None and y is not None:
        action.x, action.y = scaler.to_screen(x, y)
    return action


def call_to_action(call: RawCall, scaler: CoordinateScaler) -> Optional[Action]:
    """Translate one pyautogui/computer.* call into the canonical IR."""
    func = call.func.split(".")[-1]
    namespace = call.func.rsplit(".", 1)[0] if "." in call.func else ""

    if namespace.endswith("computer") or call.func.startswith("computer."):
        if func in {"terminate", "stop"}:
            status = str(call.arg(0, "status", "success") or "success")
            answer = call.kwargs.get("answer")
            action = Action.terminate(status=status, raw=call.source)
            if answer:
                action.text = str(answer)
            return action
        if func == "wait":
            seconds = _coerce_number(call.arg(0, "seconds")) or 20.0
            return Action.wait(seconds, raw=call.source)
        if func == "triple_click":
            point = _point(call, scaler)
            if point:
                return Action(type=ActionType.TRIPLE_CLICK, x=point[0], y=point[1], raw=call.source)
            return None
        if func == "answer":
            text = call.arg(0, "text") or call.arg(0, "answer")
            return Action(type=ActionType.ANSWER, text=str(text or ""), raw=call.source)

    if func in {"sleep"}:
        seconds = _coerce_number(call.arg(0, "seconds")) or 3.0
        return Action.wait(seconds, raw=call.source)

    if func in {"click", "leftClick", "mouseDown", "mouseUp"}:
        point = _point(call, scaler)
        button = str(call.kwargs.get("button") or "left").lower()
        clicks = int(_coerce_number(call.kwargs.get("clicks")) or 1)
        action_type = ActionType.CLICK
        if button == "right":
            action_type = ActionType.RIGHT_CLICK
        elif button == "middle":
            action_type = ActionType.MIDDLE_CLICK
        elif clicks == 2:
            action_type = ActionType.DOUBLE_CLICK
        elif clicks >= 3:
            action_type = ActionType.TRIPLE_CLICK
        action = Action(type=action_type, raw=call.source)
        if point:
            action.x, action.y = point
        return action

    if func in {"doubleClick", "tripleClick", "rightClick", "middleClick", "moveTo", "dragTo"}:
        mapping = {
            "doubleClick": ActionType.DOUBLE_CLICK,
            "tripleClick": ActionType.TRIPLE_CLICK,
            "rightClick": ActionType.RIGHT_CLICK,
            "middleClick": ActionType.MIDDLE_CLICK,
            "moveTo": ActionType.MOVE,
            "dragTo": ActionType.DRAG,
        }
        point = _point(call, scaler)
        action = Action(type=mapping[func], raw=call.source)
        if point and func == "dragTo":
            # dragTo starts wherever the cursor is; the loop fills the origin in.
            action.to_x, action.to_y = point
        elif point:
            action.x, action.y = point
        return action

    if func in {"write", "typewrite", "type"}:
        text = call.arg(0, "message")
        if isinstance(text, (list, tuple)):
            text = "".join(str(item) for item in text)
        return Action.type_text(str(text or ""), raw=call.source)

    if func == "press":
        keys = _keys_from(call.arg(0, "keys"))
        repeats = int(_coerce_number(call.kwargs.get("presses")) or 1)
        if not keys:
            return None
        action = Action.hotkey(*keys, raw=call.source)
        if repeats > 1:
            action.metadata["presses"] = repeats
        return action

    if func in {"hotkey", "keyDown", "keyUp"}:
        keys = _keys_from(call.args or call.kwargs.get("keys"))
        if not keys:
            return None
        return Action.hotkey(*keys, raw=call.source)

    if func == "scroll":
        return _scroll_action(call, scaler, horizontal=False)
    if func == "hscroll":
        return _scroll_action(call, scaler, horizontal=True)

    if func in {"screenshot", "locateCenterOnScreen", "position"}:
        return None

    return None


def parse_pyautogui_code(code: str, scaler: CoordinateScaler) -> list[Action]:
    """Full pipeline: code block → canonical actions (sentinels included)."""
    calls, sentinels = parse_calls(code)
    actions: list[Action] = [
        action for action in (call_to_action(call, scaler) for call in calls) if action
    ]

    # Expand `press(..., presses=N)` now that the executor only sees one key each.
    expanded: list[Action] = []
    for action in actions:
        repeats = int(action.metadata.pop("presses", 1) or 1)
        expanded.extend([action] * max(repeats, 1))

    for sentinel in sentinels:
        if sentinel == "DONE":
            expanded.append(Action.terminate("success", raw=sentinel))
        elif sentinel == "FAIL":
            expanded.append(Action.terminate("failure", raw=sentinel))
        elif sentinel == "WAIT":
            expanded.append(Action.wait(3.0, raw=sentinel))
    return expanded


_BOX_RE = re.compile(r"\(?\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*(?:,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*)?\)?")


def parse_box(raw: str, scaler: CoordinateScaler) -> Optional[tuple[int, int]]:
    """Parse ``(x1,y1)`` or ``(x1,y1,x2,y2)`` boxes into a screen-space centre."""
    if not raw:
        return None
    cleaned = re.sub(r"<\|?box_(start|end)\|?>|<bbox>|</bbox>|'|\"", "", str(raw)).strip()
    match = _BOX_RE.search(cleaned)
    if not match:
        return None
    x1, y1 = float(match.group(1)), float(match.group(2))
    if match.group(3) is not None and match.group(4) is not None:
        x1 = (x1 + float(match.group(3))) / 2.0
        y1 = (y1 + float(match.group(4))) / 2.0
    return scaler.to_screen(x1, y1)
